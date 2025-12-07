import os
import logging
from pathlib import Path
import pdfplumber
import PyPDF2
import configparser
import psutil
import time
import gc
from typing import List, Tuple, Optional
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    @classmethod
    def get_current(cls) -> 'SystemResources':
        """Obtém recursos atuais do sistema"""
        memory = psutil.virtual_memory()
        return cls(
            total_memory_gb=memory.total / (1024**3),
            available_memory_gb=memory.available / (1024**3),
            cpu_count=psutil.cpu_count()
        )

@dataclass
class DirectProcessingConfig:
    """Configuração adaptativa para extração direta"""
    batch_size: int
    use_fallback: bool
    max_memory_usage_percent: float
    cleanup_frequency: int
    
    @classmethod
    def from_system_resources(cls, resources: SystemResources, file_size_mb: float) -> 'DirectProcessingConfig':
        """Cria configuração baseada nos recursos disponíveis"""
        
        if resources.available_memory_gb >= 8:
            # Sistema com bastante memória
            batch_size = 50 if file_size_mb < 100 else 25
            cleanup_freq = 100
            max_memory = 0.7
        elif resources.available_memory_gb >= 4:
            # Sistema com memória moderada
            batch_size = 25 if file_size_mb < 50 else 10
            cleanup_freq = 50
            max_memory = 0.6
        else:
            # Sistema com pouca memória
            batch_size = 10 if file_size_mb < 25 else 5
            cleanup_freq = 25
            max_memory = 0.5
        
        return cls(
            batch_size=batch_size,
            use_fallback=True,
            max_memory_usage_percent=max_memory,
            cleanup_frequency=cleanup_freq
        )

class MemoryManager:
    """Gerenciador de memória para extração direta"""
    
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
        time.sleep(0.1)  # Dá tempo para o GC fazer efeito
    
    def wait_for_memory_availability(self, max_wait_seconds: int = 30):
        """Aguarda até que a memória esteja disponível"""
        start_time = time.time()
        while self.is_memory_critical() and (time.time() - start_time) < max_wait_seconds:
            current_usage = self.get_memory_usage_percentage()
            logger.warning(f"Memória crítica ({current_usage:.1%}). Aguardando liberação...")
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
        self.current_method = "pdfplumber"
        
    def update(self, pages_processed: int, characters: int = 0, failed: bool = False, method: str = None):
        """Atualiza progresso"""
        self.processed_pages += pages_processed
        self.characters_extracted += characters
        if failed:
            self.failed_pages += 1
        if method:
            self.current_method = method
            
        # Log de progresso a cada 10 páginas ou no final
        if self.processed_pages % 10 == 0 or self.processed_pages == self.total_pages:
            elapsed = time.time() - self.start_time
            percentage = (self.processed_pages / self.total_pages) * 100
            
            if self.processed_pages > 0:
                avg_time_per_page = elapsed / self.processed_pages
                remaining_pages = self.total_pages - self.processed_pages
                eta_seconds = remaining_pages * avg_time_per_page
                eta_minutes = eta_seconds / 60
                
                logger.info(
                    f"Progresso: {self.processed_pages}/{self.total_pages} ({percentage:.1f}%) - "
                    f"Método: {self.current_method} - "
                    f"ETA: {eta_minutes:.1f}min - "
                    f"Caracteres: {self.characters_extracted:,} - "
                    f"Falhas: {self.failed_pages}"
                )

class DirectPDFProcessor:
    """Processador otimizado para extração direta de PDF"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.load_config()
        self.memory_manager = MemoryManager()
        self._pdf_cache = None
        self._pdf_reader_cache = None
        
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
        self.output_path = Path(config['Paths']['OUTPUT_PATH_DIRECT'])
        
    def get_pdf_page_count_fast(self) -> int:
        """Obtém número de páginas rapidamente"""
        try:
            # Método 1: Tenta com PyPDF2 (mais rápido)
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e1:
            logger.warning(f"PyPDF2 falhou para contar páginas: {e1}")
            try:
                # Método 2: Tenta com pdfplumber
                with pdfplumber.open(self.pdf_path) as pdf:
                    return len(pdf.pages)
            except Exception as e2:
                logger.warning(f"pdfplumber falhou para contar páginas: {e2}")
                return 1000  # Fallback seguro
    
    def extract_page_with_pdfplumber(self, page_num: int) -> Optional[str]:
        """Extrai texto de uma página usando pdfplumber"""
        try:
            if self._pdf_cache is None:
                self._pdf_cache = pdfplumber.open(self.pdf_path)
            
            if page_num <= len(self._pdf_cache.pages):
                page = self._pdf_cache.pages[page_num - 1]  # pdfplumber usa índice 0
                text = page.extract_text()
                return text if text else ""
            return None
            
        except Exception as e:
            logger.debug(f"pdfplumber falhou na página {page_num}: {e}")
            return None
    
    def extract_page_with_pypdf2(self, page_num: int) -> Optional[str]:
        """Extrai texto de uma página usando PyPDF2"""
        try:
            if self._pdf_reader_cache is None:
                with open(self.pdf_path, 'rb') as file:
                    self._pdf_reader_cache = PyPDF2.PdfReader(file)
            
            if page_num <= len(self._pdf_reader_cache.pages):
                page = self._pdf_reader_cache.pages[page_num - 1]  # PyPDF2 usa índice 0
                text = page.extract_text()
                return text if text else ""
            return None
            
        except Exception as e:
            logger.debug(f"PyPDF2 falhou na página {page_num}: {e}")
            return None
    
    def extract_page_hybrid(self, page_num: int) -> Tuple[str, str]:
        """Extrai texto de uma página usando método híbrido"""
        # Tenta primeiro pdfplumber (melhor qualidade)
        text = self.extract_page_with_pdfplumber(page_num)
        method = "pdfplumber"
        
        if text is None or len(text.strip()) < 10:
            # Fallback para PyPDF2
            text = self.extract_page_with_pypdf2(page_num)
            method = "pypdf2"
            
        if text is None:
            text = ""
            method = "failed"
            
        return text, method
    
    def process_page_batch(self, start_page: int, end_page: int, config: DirectProcessingConfig) -> List[Tuple[int, str, str]]:
        """Processa um lote de páginas"""
        results = []
        
        for page_num in range(start_page, min(end_page + 1, start_page + config.batch_size)):
            try:
                # Verifica memória antes de processar
                if self.memory_manager.is_memory_critical():
                    logger.warning(f"Memória crítica na página {page_num}. Limpando...")
                    self.memory_manager.force_cleanup()
                    self.memory_manager.wait_for_memory_availability()
                
                # Extrai texto da página
                text, method = self.extract_page_hybrid(page_num)
                
                if text.strip():
                    results.append((page_num, text.strip(), method))
                    logger.debug(f"Página {page_num} ({method}): {len(text)} caracteres")
                else:
                    logger.debug(f"Página {page_num}: sem texto extraível")
                
                # Limpeza periódica de memória
                if page_num % config.cleanup_frequency == 0:
                    self.memory_manager.force_cleanup()
                    
            except Exception as e:
                logger.warning(f"Erro na página {page_num}: {e}")
                continue
                
        return results
    
    def process_complete_pdf(self) -> str:
        """Processa o PDF completo de forma otimizada"""
        logger.info("🚀 === Iniciando Processamento Direto Completo do PDF ===")
        
        # Análise inicial
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {self.pdf_path}")
            
        file_size_mb = self.pdf_path.stat().st_size / (1024 * 1024)
        logger.info(f"Arquivo: {self.pdf_path.name} ({file_size_mb:.1f} MB)")
        
        # Recursos do sistema
        resources = SystemResources.get_current()
        logger.info(f"Sistema: {resources.available_memory_gb:.1f}GB RAM disponível, {resources.cpu_count} CPUs")
        
        # Configuração adaptativa
        config = DirectProcessingConfig.from_system_resources(resources, file_size_mb)
        logger.info(f"Configuração: Batch={config.batch_size}, Cleanup={config.cleanup_frequency}, MaxMem={config.max_memory_usage_percent:.1%}")
        
        # Conta páginas
        total_pages = self.get_pdf_page_count_fast()
        logger.info(f"Total de páginas: {total_pages}")
        
        # Progress tracker
        progress = ProgressTracker(total_pages)
        
        # Processamento em lotes
        all_results = []
        
        try:
            # Inicializa caches
            logger.info("Inicializando caches de PDF...")
            
            for batch_start in range(1, total_pages + 1, config.batch_size):
                batch_end = min(batch_start + config.batch_size - 1, total_pages)
                
                logger.info(f"Processando lote: páginas {batch_start}-{batch_end}")
                
                # Processa lote
                batch_results = self.process_page_batch(batch_start, batch_end, config)
                all_results.extend(batch_results)
                
                # Atualiza progresso
                chars_in_batch = sum(len(text) for _, text, _ in batch_results)
                methods_used = [method for _, _, method in batch_results]
                primary_method = max(set(methods_used), key=methods_used.count) if methods_used else "unknown"
                
                progress.update(len(batch_results), chars_in_batch, method=primary_method)
                
                # Limpeza de memória entre lotes grandes
                if batch_end - batch_start > 20:
                    self.memory_manager.force_cleanup()
                
                # Pausa se memória crítica
                if self.memory_manager.is_memory_critical():
                    logger.warning("Memória crítica - pausa para recuperação")
                    self.memory_manager.force_cleanup()
                    time.sleep(3)
            
            # Fecha caches
            self._close_caches()
            
            # Monta resultado final
            if not all_results:
                return "Nenhum texto foi extraído do PDF."
            
            # Ordena por página
            all_results.sort(key=lambda x: x[0])
            
            # Monta texto final e estatísticas por método
            final_text_parts = []
            method_stats = {}
            
            for page_num, text, method in all_results:
                final_text_parts.append(f"=== PÁGINA {page_num} ===\n{text}\n")
                method_stats[method] = method_stats.get(method, 0) + 1
            
            final_text = "\n".join(final_text_parts)
            
            # Estatísticas finais
            logger.info(f"✅ Processamento direto concluído!")
            logger.info(f"📄 Páginas processadas: {len(all_results)}/{total_pages}")
            logger.info(f"📝 Caracteres extraídos: {len(final_text):,}")
            logger.info(f"⏱️ Tempo total: {(time.time() - progress.start_time)/60:.1f} minutos")
            logger.info(f"❌ Páginas com falha: {progress.failed_pages}")
            logger.info(f"🔧 Métodos usados: {dict(method_stats)}")
            
            return final_text
            
        finally:
            # Limpeza final
            self._close_caches()
            self.memory_manager.force_cleanup()
    
    def _close_caches(self):
        """Fecha e limpa caches de PDF"""
        try:
            if self._pdf_cache:
                self._pdf_cache.close()
                self._pdf_cache = None
            self._pdf_reader_cache = None
            gc.collect()
            logger.debug("Caches de PDF fechados")
        except Exception as e:
            logger.warning(f"Erro ao fechar caches: {e}")

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
    logger.info("🚀 === EXTRATOR DIRETO COMPLETO - ARQUITETURA MODULAR ===")
    
    # Configuração
    script_dir = Path(__file__).parent
    config_file = script_dir / 'config.ini'
    
    try:
        # Inicializa processador
        processor = DirectPDFProcessor(config_file)
        
        # Processa PDF completo
        extracted_text = processor.process_complete_pdf()
        
        # Salva resultado
        processor.save_text(extracted_text)
        
        logger.info("🎉 === PROCESSAMENTO DIRETO CONCLUÍDO COM SUCESSO ===")
        
    except KeyboardInterrupt:
        logger.warning("⏹️ Processamento interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro crítico: {e}")
        raise

if __name__ == "__main__":
    main()