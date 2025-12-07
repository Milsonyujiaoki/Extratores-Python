from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import logging
import configparser
from PIL import Image
import gc
import os
import psutil
import time
import threading
from typing import List, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil

# Configuração de log avançado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemResources:
    """Monitora recursos do sistema"""
    total_memory_gb: float
    available_memory_gb: float
    cpu_count: int
    disk_space_gb: float
    
    @classmethod
    def get_current(cls) -> 'SystemResources':
        """Obtém recursos atuais do sistema"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return cls(
            total_memory_gb=memory.total / (1024**3),
            available_memory_gb=memory.available / (1024**3),
            cpu_count=psutil.cpu_count(),
            disk_space_gb=disk.free / (1024**3)
        )

@dataclass
class ProcessingConfig:
    """Configuração adaptativa de processamento"""
    dpi: int
    batch_size: int
    max_concurrent_pages: int
    use_temp_files: bool
    compression_quality: int
    
    @classmethod
    def from_system_resources(cls, resources: SystemResources, file_size_mb: float) -> 'ProcessingConfig':
        """Cria configuração baseada nos recursos disponíveis"""
        
        # Calcula configurações baseadas na memória disponível
        if resources.available_memory_gb >= 8:
            # Sistema com bastante memória
            dpi = 200 if file_size_mb < 50 else 150
            batch_size = 5
            max_concurrent = min(4, resources.cpu_count)
            use_temp = file_size_mb > 200
        elif resources.available_memory_gb >= 4:
            # Sistema com memória moderada
            dpi = 150 if file_size_mb < 100 else 120
            batch_size = 3
            max_concurrent = min(2, resources.cpu_count)
            use_temp = file_size_mb > 100
        else:
            # Sistema com pouca memória
            dpi = 120 if file_size_mb < 50 else 100
            batch_size = 1
            max_concurrent = 1
            use_temp = file_size_mb > 50
        
        return cls(
            dpi=dpi,
            batch_size=batch_size,
            max_concurrent_pages=max_concurrent,
            use_temp_files=use_temp,
            compression_quality=85 if use_temp else 95
        )

class MemoryManager:
    """Gerenciador de memória inteligente"""
    
    def __init__(self, memory_limit_percentage: float = 0.7):
        self.memory_limit_percentage = memory_limit_percentage
        self.initial_memory = psutil.virtual_memory().available
        
    def get_memory_usage_percentage(self) -> float:
        """Retorna percentual de uso de memória"""
        current = psutil.virtual_memory()
        return (current.total - current.available) / current.total
    
    def is_memory_critical(self) -> bool:
        """Verifica se a memória está em nível crítico"""
        return self.get_memory_usage_percentage() > self.memory_limit_percentage
    
    def force_cleanup(self):
        """Força limpeza agressiva de memória"""
        gc.collect()
        # Aguarda um pouco para o GC fazer efeito
        time.sleep(0.1)
    
    def wait_for_memory_availability(self, max_wait_seconds: int = 30):
        """Aguarda até que a memória esteja disponível"""
        start_time = time.time()
        while self.is_memory_critical() and (time.time() - start_time) < max_wait_seconds:
            logger.warning(f"Memória crítica ({self.get_memory_usage_percentage():.1%}). Aguardando...")
            self.force_cleanup()
            time.sleep(2)

class ProgressTracker:
    """Rastreador de progresso com estimativas"""
    
    def __init__(self, total_pages: int):
        self.total_pages = total_pages
        self.processed_pages = 0
        self.start_time = time.time()
        self.characters_extracted = 0
        self.failed_pages = 0
        
    def update(self, pages_processed: int, characters: int = 0, failed: bool = False):
        """Atualiza progresso"""
        self.processed_pages += pages_processed
        self.characters_extracted += characters
        if failed:
            self.failed_pages += 1
            
        # Log de progresso
        elapsed = time.time() - self.start_time
        percentage = (self.processed_pages / self.total_pages) * 100
        
        if self.processed_pages > 0:
            avg_time_per_page = elapsed / self.processed_pages
            remaining_pages = self.total_pages - self.processed_pages
            eta_seconds = remaining_pages * avg_time_per_page
            eta_minutes = eta_seconds / 60
            
            logger.info(
                f"Progresso: {self.processed_pages}/{self.total_pages} ({percentage:.1f}%) - "
                f"ETA: {eta_minutes:.1f}min - "
                f"Caracteres: {self.characters_extracted:,} - "
                f"Falhas: {self.failed_pages}"
            )

class PDFProcessor:
    """Processador principal de PDF com arquitetura modular"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.load_config()
        self.memory_manager = MemoryManager()
        self.temp_dir = None
        
    def load_config(self):
        """Carrega configuração do arquivo"""
        config = configparser.ConfigParser()
        
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config não encontrado: {self.config_file}")
            
        # Tenta diferentes encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
            try:
                config.read(self.config_file, encoding=encoding)
                if config.has_section('Paths'):
                    break
            except Exception as e:
                logger.debug(f"Falha com encoding {encoding}: {e}")
                continue
        else:
            raise configparser.Error("Falha ao carregar configuração")
            
        if not config.has_section('Paths'):
            raise configparser.NoSectionError('Paths')
            
        self.pdf_path = Path(config['Paths']['PDF_PATH'])
        self.output_path = Path(config['Paths']['OUTPUT_PATH_OCR'])
        
    def get_pdf_page_count(self) -> int:
        """Estima número de páginas do PDF"""
        try:
            # Método rápido: converte apenas primeira página para estimar
            test_images = convert_from_path(str(self.pdf_path), dpi=72, first_page=1, last_page=1)
            if test_images:
                test_images[0].close()
            del test_images
            gc.collect()
            
            # Usa binary search para encontrar a última página
            return self._binary_search_last_page()
        except Exception as e:
            logger.warning(f"Erro ao contar páginas: {e}")
            return 1000  # Fallback seguro
    
    def _binary_search_last_page(self) -> int:
        """Busca binária para encontrar última página"""
        low, high = 1, 2000  # Assume máximo de 2000 páginas inicialmente
        last_valid = 1
        
        while low <= high:
            mid = (low + high) // 2
            try:
                test_images = convert_from_path(
                    str(self.pdf_path), 
                    dpi=72, 
                    first_page=mid, 
                    last_page=mid
                )
                if test_images:
                    test_images[0].close()
                    last_valid = mid
                    low = mid + 1
                else:
                    high = mid - 1
                del test_images
                gc.collect()
            except Exception:
                high = mid - 1
                
        logger.info(f"PDF contém aproximadamente {last_valid} páginas")
        return last_valid
    
    def create_temp_directory(self) -> Path:
        """Cria diretório temporário se necessário"""
        if self.temp_dir is None:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="pdf_ocr_"))
            logger.info(f"Diretório temporário criado: {self.temp_dir}")
        return self.temp_dir
    
    def cleanup_temp_directory(self):
        """Remove diretório temporário"""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("Diretório temporário removido")
            except Exception as e:
                logger.warning(f"Erro ao remover temp dir: {e}")
    
    def process_page_batch(self, start_page: int, end_page: int, config: ProcessingConfig) -> List[Tuple[int, str]]:
        """Processa um lote de páginas"""
        results = []
        
        for page_num in range(start_page, end_page + 1):
            try:
                # Verifica memória antes de processar
                self.memory_manager.wait_for_memory_availability()
                
                # Converte página
                images = convert_from_path(
                    str(self.pdf_path),
                    dpi=config.dpi,
                    first_page=page_num,
                    last_page=page_num,
                    thread_count=1
                )
                
                if not images:
                    continue
                    
                image = images[0]
                
                # Otimiza imagem se necessário
                if config.use_temp_files:
                    image = self._optimize_image(image, config.compression_quality)
                
                # OCR
                text = pytesseract.image_to_string(image, lang='por')
                
                if text.strip():
                    results.append((page_num, text.strip()))
                    logger.debug(f"Página {page_num}: {len(text)} caracteres")
                
                # Limpeza imediata
                image.close()
                del images, image
                gc.collect()
                
            except Exception as e:
                error_msg = str(e).lower()
                if "page does not exist" in error_msg or "page out of range" in error_msg:
                    logger.info(f"Fim do documento na página {page_num}")
                    break
                else:
                    logger.warning(f"Erro na página {page_num}: {e}")
                    continue
                    
        return results
    
    def _optimize_image(self, image: Image.Image, quality: int) -> Image.Image:
        """Otimiza imagem para reduzir uso de memória"""
        # Converte para RGB se necessário
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Redimensiona se muito grande
        width, height = image.size
        max_dimension = 2000
        
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
        return image
    
    def process_complete_pdf(self) -> str:
        """Processa o PDF completo de forma inteligente"""
        logger.info("=== Iniciando Processamento Completo do PDF ===")
        
        # Análise inicial
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {self.pdf_path}")
            
        file_size_mb = self.pdf_path.stat().st_size / (1024 * 1024)
        logger.info(f"Arquivo: {self.pdf_path.name} ({file_size_mb:.1f} MB)")
        
        # Recursos do sistema
        resources = SystemResources.get_current()
        logger.info(f"Sistema: {resources.available_memory_gb:.1f}GB RAM disponível, {resources.cpu_count} CPUs")
        
        # Configuração adaptativa
        config = ProcessingConfig.from_system_resources(resources, file_size_mb)
        logger.info(f"Configuração: DPI={config.dpi}, Batch={config.batch_size}, Temp={config.use_temp_files}")
        
        # Conta páginas
        total_pages = self.get_pdf_page_count()
        
        # Progress tracker
        progress = ProgressTracker(total_pages)
        
        # Cria temp dir se necessário
        if config.use_temp_files:
            self.create_temp_directory()
        
        # Processamento em lotes
        all_results = []
        
        try:
            for batch_start in range(1, total_pages + 1, config.batch_size):
                batch_end = min(batch_start + config.batch_size - 1, total_pages)
                
                logger.info(f"Processando lote: páginas {batch_start}-{batch_end}")
                
                # Processa lote
                batch_results = self.process_page_batch(batch_start, batch_end, config)
                all_results.extend(batch_results)
                
                # Atualiza progresso
                chars_in_batch = sum(len(text) for _, text in batch_results)
                progress.update(len(batch_results), chars_in_batch)
                
                # Limpeza de memória entre lotes
                self.memory_manager.force_cleanup()
                
                # Pausa se memória crítica
                if self.memory_manager.is_memory_critical():
                    logger.warning("Memória crítica - pausa para recuperação")
                    time.sleep(5)
            
            # Monta resultado final
            if not all_results:
                return "Nenhum texto foi extraído do PDF."
            
            # Ordena por página
            all_results.sort(key=lambda x: x[0])
            
            # Monta texto final
            final_text_parts = []
            for page_num, text in all_results:
                final_text_parts.append(f"=== PÁGINA {page_num} ===\n{text}\n")
            
            final_text = "\n".join(final_text_parts)
            
            # Estatísticas finais
            logger.info(f"✅ Processamento concluído!")
            logger.info(f"📄 Páginas processadas: {len(all_results)}/{total_pages}")
            logger.info(f"📝 Caracteres extraídos: {len(final_text):,}")
            logger.info(f"⏱️ Tempo total: {(time.time() - progress.start_time)/60:.1f} minutos")
            logger.info(f"❌ Páginas com falha: {progress.failed_pages}")
            
            return final_text
            
        finally:
            # Limpeza final
            self.cleanup_temp_directory()
            self.memory_manager.force_cleanup()

    def save_text(self, content: str) -> None:
        """Salva o texto extraído no arquivo de saída"""
        logger.info(f"Salvando texto em: {self.output_path}")
        
        # Limpa caracteres problemáticos
        cleaned_content = content.replace('\x00', '').replace('\ufeff', '')
        cleaned_content = cleaned_content.replace('\r\n', '\n').replace('\r', '\n')
        
        try:
            # Cria diretório de saída se não existir
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva com encoding UTF-8
            with open(self.output_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(cleaned_content)
            logger.info(f"✅ Arquivo salvo com {len(cleaned_content):,} caracteres")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar arquivo: {e}")
            raise

# === Configuração e Execução Principal ===
def main():
    """Função principal"""
    logger.info("🚀 === EXTRATOR OCR COMPLETO - ARQUITETURA MODULAR ===")
    
    # Configuração
    script_dir = Path(__file__).parent
    config_file = script_dir / 'config.ini'
    
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    try:
        # Inicializa processador
        processor = PDFProcessor(config_file)
        
        # Processa PDF completo
        extracted_text = processor.process_complete_pdf()
        
        # Salva resultado
        processor.save_text(extracted_text)
        
        logger.info("🎉 === PROCESSAMENTO CONCLUÍDO COM SUCESSO ===")
        
    except KeyboardInterrupt:
        logger.warning("⏹️ Processamento interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro crítico: {e}")
        raise

if __name__ == "__main__":
    main()