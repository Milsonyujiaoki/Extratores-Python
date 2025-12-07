"""
Extrator direto para PDFs com texto nativo.
Usa pdfplumber e PyPDF2 para extração direta de texto.
"""

import time
from pathlib import Path
from typing import Dict, Any
import logging

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from ..core.base_extractor import BaseExtractor, ExtractionResult
from ..core.extractor_factory import register_extractor

logger = logging.getLogger(__name__)


@register_extractor('direct')
class DirectExtractor(BaseExtractor):
    """
    Extrator para PDFs com texto nativo extraível.
    Tenta pdfplumber primeiro, depois PyPDF2 como fallback.
    """
    
    def _setup_extractor(self) -> None:
        """Configuração específica do extrator direto."""
        self.use_pdfplumber = PDFPLUMBER_AVAILABLE and self.config.get('use_pdfplumber', True)
        self.use_pypdf2 = PYPDF2_AVAILABLE and self.config.get('use_pypdf2', True)
        
        if not self.use_pdfplumber and not self.use_pypdf2:
            raise ImportError("Nem pdfplumber nem PyPDF2 estão disponíveis")
        
        self.logger.info(f"DirectExtractor configurado - pdfplumber: {self.use_pdfplumber}, PyPDF2: {self.use_pypdf2}")
    
    @property
    def extractor_name(self) -> str:
        """Nome do extrator."""
        return "Direct PDF Text Extractor"
    
    @property
    def extractor_type(self) -> str:
        """Tipo do extrator."""
        return "direct"
    
    def is_suitable_for(self, pdf_path: Path) -> bool:
        """
        Verifica se o extrator direto é adequado para o PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True se adequado (sempre, pois é o extrator base)
        """
        if not self.validate_pdf(pdf_path):
            return False
        
        # O extrator direto pode tentar qualquer PDF
        # A adequação real é determinada durante a extração
        return True
    
    def extract_text(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto diretamente do PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Resultado da extração
        """
        start_time = time.time()
        file_info = self.get_file_info(pdf_path)
        
        if not self.validate_pdf(pdf_path):
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=0,
                extraction_method=self.extractor_name,
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message="PDF inválido ou inacessível"
            )
        
        # Tenta pdfplumber primeiro
        if self.use_pdfplumber:
            result = self._extract_with_pdfplumber(pdf_path, start_time, file_info)
            if result.success and result.text_content.strip():
                return result
            self.logger.info("pdfplumber não extraiu texto, tentando PyPDF2...")
        
        # Fallback para PyPDF2
        if self.use_pypdf2:
            result = self._extract_with_pypdf2(pdf_path, start_time, file_info)
            if result.success:
                return result
        
        # Se ambos falharam
        return ExtractionResult(
            file_path=pdf_path,
            success=False,
            text_content="",
            pages_processed=0,
            extraction_method=self.extractor_name,
            processing_time=time.time() - start_time,
            file_size=file_info.get('file_size', 0),
            error_message="Não foi possível extrair texto com métodos diretos"
        )
    
    def _extract_with_pdfplumber(self, pdf_path: Path, start_time: float, file_info: Dict[str, Any]) -> ExtractionResult:
        """
        Extrai texto usando pdfplumber.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            start_time: Tempo de início do processamento
            file_info: Informações do arquivo
            
        Returns:
            Resultado da extração
        """
        text_content = []
        pages_processed = 0
        error_message = None
        
        try:
            self.logger.info(f"Extraindo com pdfplumber: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                self.logger.info(f"PDF tem {total_pages} páginas")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(f"=== PÁGINA {page_num} ===\n{text}\n")
                            pages_processed += 1
                        
                        # Log de progresso a cada 10 páginas
                        if page_num % 10 == 0:
                            self.logger.info(f"Processadas {page_num}/{total_pages} páginas")
                            
                    except Exception as page_error:
                        self.logger.warning(f"Erro ao processar página {page_num} com pdfplumber: {page_error}")
                        continue
            
            success = len(text_content) > 0
            final_text = "\n".join(text_content) if success else ""
            
            if success:
                self.logger.info(f"pdfplumber extraiu texto de {pages_processed} páginas")
            
            return ExtractionResult(
                file_path=pdf_path,
                success=success,
                text_content=final_text,
                pages_processed=pages_processed,
                extraction_method="pdfplumber",
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message=error_message
            )
            
        except Exception as e:
            error_msg = f"Erro na extração com pdfplumber: {e}"
            self.logger.error(error_msg)
            
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=pages_processed,
                extraction_method="pdfplumber",
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message=error_msg
            )
        
        finally:
            # Força limpeza de memória
            import gc
            gc.collect()
    
    def _extract_with_pypdf2(self, pdf_path: Path, start_time: float, file_info: Dict[str, Any]) -> ExtractionResult:
        """
        Extrai texto usando PyPDF2.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            start_time: Tempo de início do processamento
            file_info: Informações do arquivo
            
        Returns:
            Resultado da extração
        """
        text_content = []
        pages_processed = 0
        error_message = None
        
        try:
            self.logger.info(f"Extraindo com PyPDF2: {pdf_path}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                self.logger.info(f"PDF tem {total_pages} páginas")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(f"=== PÁGINA {page_num} ===\n{text}\n")
                            pages_processed += 1
                        
                        # Log de progresso a cada 10 páginas
                        if page_num % 10 == 0:
                            self.logger.info(f"Processadas {page_num}/{total_pages} páginas")
                            
                    except Exception as page_error:
                        self.logger.warning(f"Erro ao processar página {page_num} com PyPDF2: {page_error}")
                        continue
            
            success = len(text_content) > 0
            final_text = "\n".join(text_content) if success else ""
            
            if success:
                self.logger.info(f"PyPDF2 extraiu texto de {pages_processed} páginas")
            
            return ExtractionResult(
                file_path=pdf_path,
                success=success,
                text_content=final_text,
                pages_processed=pages_processed,
                extraction_method="PyPDF2",
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message=error_message
            )
            
        except Exception as e:
            error_msg = f"Erro na extração com PyPDF2: {e}"
            self.logger.error(error_msg)
            
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=pages_processed,
                extraction_method="PyPDF2",
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message=error_msg
            )
        
        finally:
            # Força limpeza de memória
            import gc
            gc.collect()