"""
Processador assíncrono para extração de múltiplos PDFs.
Implementa processamento paralelo e descoberta recursiva de arquivos.
"""

import asyncio
import concurrent.futures
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
import logging
from dataclasses import dataclass
from datetime import datetime
import json

from ..core.base_extractor import BaseExtractor, ExtractionResult
from ..core.extractor_factory import ExtractorFactory
from ..core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Estatísticas de processamento em lote."""
    
    total_files: int = 0
    processed_files: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    total_processing_time: float = 0.0
    total_characters_extracted: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso das extrações."""
        return self.successful_extractions / self.processed_files if self.processed_files > 0 else 0.0
    
    @property
    def average_processing_time(self) -> float:
        """Tempo médio de processamento por arquivo."""
        return self.total_processing_time / self.processed_files if self.processed_files > 0 else 0.0
    
    @property
    def processing_speed(self) -> float:
        """Caracteres extraídos por segundo."""
        return self.total_characters_extracted / self.total_processing_time if self.total_processing_time > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte estatísticas para dicionário."""
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_extractions': self.successful_extractions,
            'failed_extractions': self.failed_extractions,
            'success_rate': self.success_rate,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': self.average_processing_time,
            'total_characters_extracted': self.total_characters_extracted,
            'processing_speed': self.processing_speed,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class AsyncPDFProcessor:
    """
    Processador assíncrono para extração de múltiplos PDFs.
    Suporta processamento paralelo e descoberta recursiva de arquivos.
    """
    
    def __init__(self, config: ConfigManager):
        """
        Inicializa o processador assíncrono.
        
        Args:
            config: Gerenciador de configurações
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.stats = ProcessingStats()
        
        # Configurações de paralelismo
        self.max_workers = config.config.max_workers
        self.batch_size = config.config.batch_size
        
        # Callbacks para eventos
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.file_processed_callback: Optional[Callable[[ExtractionResult], None]] = None
        
        self.logger.info(f"AsyncPDFProcessor inicializado - workers: {self.max_workers}, batch: {self.batch_size}")
    
    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """
        Define callback para progresso.
        
        Args:
            callback: Função que recebe (processed, total)
        """
        self.progress_callback = callback
    
    def set_file_processed_callback(self, callback: Callable[[ExtractionResult], None]) -> None:
        """
        Define callback para arquivo processado.
        
        Args:
            callback: Função que recebe ExtractionResult
        """
        self.file_processed_callback = callback
    
    async def discover_pdfs(self, directory: Path, recursive: bool = True) -> List[Path]:
        """
        Descobre arquivos PDF em um diretório.
        
        Args:
            directory: Diretório para busca
            recursive: Se deve buscar recursivamente
            
        Returns:
            Lista de caminhos para arquivos PDF
        """
        self.logger.info(f"Descobrindo PDFs em: {directory} (recursivo: {recursive})")
        
        def _scan_directory() -> List[Path]:
            pdf_files = []
            
            try:
                if recursive:
                    pattern = "**/*.pdf"
                else:
                    pattern = "*.pdf"
                
                for pdf_path in directory.glob(pattern):
                    if pdf_path.is_file():
                        # Verifica tamanho máximo se configurado
                        if self.config.config.max_file_size_mb > 0:
                            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
                            if file_size_mb > self.config.config.max_file_size_mb:
                                self.logger.warning(f"Arquivo muito grande ignorado: {pdf_path} ({file_size_mb:.1f}MB)")
                                continue
                        
                        pdf_files.append(pdf_path)
                
                return pdf_files
                
            except Exception as e:
                self.logger.error(f"Erro ao escanear diretório {directory}: {e}")
                return []
        
        # Executa escaneamento em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        pdf_files = await loop.run_in_executor(None, _scan_directory)
        
        self.logger.info(f"Encontrados {len(pdf_files)} arquivos PDF")
        return pdf_files
    
    async def process_files(self, pdf_files: List[Path], extractor_type: str = 'auto') -> List[ExtractionResult]:
        """
        Processa lista de arquivos PDF.
        
        Args:
            pdf_files: Lista de arquivos PDF
            extractor_type: Tipo de extrator ('auto', 'direct', 'ocr', 'hybrid')
            
        Returns:
            Lista de resultados de extração
        """
        self.stats = ProcessingStats()
        self.stats.total_files = len(pdf_files)
        self.stats.start_time = datetime.now()
        
        self.logger.info(f"Iniciando processamento de {len(pdf_files)} arquivos")
        
        results = []
        
        # Processa arquivos em lotes
        for i in range(0, len(pdf_files), self.batch_size):
            batch = pdf_files[i:i + self.batch_size]
            batch_results = await self._process_batch(batch, extractor_type)
            results.extend(batch_results)
            
            # Atualiza progresso
            if self.progress_callback:
                self.progress_callback(len(results), len(pdf_files))
        
        self.stats.end_time = datetime.now()
        self.logger.info(f"Processamento concluído - {self.stats.successful_extractions}/{self.stats.total_files} sucessos")
        
        return results
    
    async def _process_batch(self, batch: List[Path], extractor_type: str) -> List[ExtractionResult]:
        """
        Processa um lote de arquivos em paralelo.
        
        Args:
            batch: Lote de arquivos PDF
            extractor_type: Tipo de extrator
            
        Returns:
            Lista de resultados do lote
        """
        self.logger.info(f"Processando lote de {len(batch)} arquivos")
        
        # Usa ThreadPoolExecutor para processamento paralelo
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Cria tasks para processamento paralelo
            tasks = [
                loop.run_in_executor(executor, self._process_single_file, pdf_path, extractor_type)
                for pdf_path in batch
            ]
            
            # Aguarda conclusão de todos os tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados e exceções
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Erro ao processar {batch[i]}: {result}")
                # Cria resultado de erro
                error_result = ExtractionResult(
                    file_path=batch[i],
                    success=False,
                    text_content="",
                    pages_processed=0,
                    extraction_method="Error",
                    processing_time=0,
                    file_size=0,
                    error_message=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        # Atualiza estatísticas
        for result in processed_results:
            self._update_stats(result)
            
            # Chama callback se definido
            if self.file_processed_callback:
                try:
                    self.file_processed_callback(result)
                except Exception as e:
                    self.logger.error(f"Erro no callback de arquivo processado: {e}")
        
        return processed_results
    
    def _process_single_file(self, pdf_path: Path, extractor_type: str) -> ExtractionResult:
        """
        Processa um único arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            extractor_type: Tipo de extrator
            
        Returns:
            Resultado da extração
        """
        try:
            self.logger.info(f"Processando: {pdf_path}")
            
            # Seleciona extrator
            if extractor_type == 'auto':
                extractor = ExtractorFactory.auto_select_extractor(pdf_path, self.config)
            else:
                extractor = ExtractorFactory.get_extractor(extractor_type, self.config)
            
            # Executa extração
            result = extractor.extract_text(pdf_path)
            
            # Salva resultado se configurado
            if result.success and result.text_content.strip():
                self._save_extraction_result(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Erro ao processar {pdf_path}: {e}"
            self.logger.error(error_msg)
            
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=0,
                extraction_method="Error",
                processing_time=0,
                file_size=0,
                error_message=error_msg
            )
    
    def _save_extraction_result(self, result: ExtractionResult) -> None:
        """
        Salva resultado da extração.
        
        Args:
            result: Resultado da extração
        """
        try:
            output_path = self.config.get_output_path(result.file_path)
            
            if self.config.config.output_format == 'txt':
                self._save_text_result(result, output_path)
            elif self.config.config.output_format == 'json':
                self._save_json_result(result, output_path)
            
            self.logger.info(f"Resultado salvo: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar resultado para {result.file_path}: {e}")
    
    def _save_text_result(self, result: ExtractionResult, output_path: Path) -> None:
        """Salva resultado em formato texto."""
        # Limpa conteúdo
        cleaned_content = result.text_content.replace('\x00', '')
        cleaned_content = cleaned_content.replace('\ufeff', '')
        cleaned_content = cleaned_content.replace('\r\n', '\n').replace('\r', '\n')
        
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(cleaned_content)
    
    def _save_json_result(self, result: ExtractionResult, output_path: Path) -> None:
        """Salva resultado em formato JSON."""
        result_dict = result.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    def _update_stats(self, result: ExtractionResult) -> None:
        """
        Atualiza estatísticas de processamento.
        
        Args:
            result: Resultado da extração
        """
        self.stats.processed_files += 1
        self.stats.total_processing_time += result.processing_time
        
        if result.success:
            self.stats.successful_extractions += 1
            self.stats.total_characters_extracted += result.characters_extracted
        else:
            self.stats.failed_extractions += 1
    
    async def process_directory(self, directory: Path, extractor_type: str = 'auto', recursive: bool = True) -> List[ExtractionResult]:
        """
        Processa todos os PDFs em um diretório.
        
        Args:
            directory: Diretório para processamento
            extractor_type: Tipo de extrator
            recursive: Se deve buscar recursivamente
            
        Returns:
            Lista de resultados de extração
        """
        if not directory.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Caminho não é um diretório: {directory}")
        
        # Descobre arquivos PDF
        pdf_files = await self.discover_pdfs(directory, recursive)
        
        if not pdf_files:
            self.logger.warning(f"Nenhum arquivo PDF encontrado em: {directory}")
            return []
        
        # Processa arquivos
        return await self.process_files(pdf_files, extractor_type)
    
    def generate_report(self, results: List[ExtractionResult], output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Gera relatório de processamento.
        
        Args:
            results: Lista de resultados
            output_path: Caminho para salvar relatório (opcional)
            
        Returns:
            Relatório como dicionário
        """
        report = {
            'summary': self.stats.to_dict(),
            'results': [result.to_dict() for result in results],
            'successful_files': [
                str(r.file_path) for r in results if r.success
            ],
            'failed_files': [
                {'file': str(r.file_path), 'error': r.error_message}
                for r in results if not r.success
            ]
        }
        
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Relatório salvo em: {output_path}")
            except Exception as e:
                self.logger.error(f"Erro ao salvar relatório: {e}")
        
        return report
    
    async def process_with_progress(self, directory: Path, extractor_type: str = 'auto') -> AsyncGenerator[Dict[str, Any], None]:
        """
        Processa diretório com atualizações de progresso em tempo real.
        
        Args:
            directory: Diretório para processamento
            extractor_type: Tipo de extrator
            
        Yields:
            Dicionários com informações de progresso
        """
        # Descobre arquivos
        yield {'status': 'discovering', 'message': 'Descobrindo arquivos PDF...'}
        pdf_files = await self.discover_pdfs(directory, True)
        
        if not pdf_files:
            yield {'status': 'completed', 'message': 'Nenhum arquivo PDF encontrado', 'results': []}
            return
        
        yield {'status': 'starting', 'total_files': len(pdf_files), 'message': f'Iniciando processamento de {len(pdf_files)} arquivos'}
        
        # Configurar callback de progresso
        async def progress_update(processed: int, total: int):
            yield {
                'status': 'processing',
                'processed': processed,
                'total': total,
                'percentage': (processed / total) * 100,
                'message': f'Processando... {processed}/{total}'
            }
        
        self.set_progress_callback(lambda p, t: asyncio.create_task(progress_update(p, t)))
        
        # Processa arquivos
        results = await self.process_files(pdf_files, extractor_type)
        
        # Resultado final
        yield {
            'status': 'completed',
            'results': results,
            'stats': self.stats.to_dict(),
            'message': f'Processamento concluído - {self.stats.successful_extractions}/{self.stats.total_files} sucessos'
        }