"""
Extrator OCR para PDFs escaneados ou baseados em imagens.
Usa Tesseract OCR através do pytesseract.
"""

import time
from pathlib import Path
from typing import Dict, Any, List
import logging

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from ..core.base_extractor import BaseExtractor, ExtractionResult
from ..core.extractor_factory import register_extractor

logger = logging.getLogger(__name__)


@register_extractor('ocr')
class OCRExtractor(BaseExtractor):
    """
    Extrator OCR para PDFs escaneados ou baseados em imagens.
    Converte páginas para imagens e aplica OCR.
    """
    
    def _setup_extractor(self) -> None:
        """Configuração específica do extrator OCR."""
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image não está disponível")
        
        if not PYTESSERACT_AVAILABLE:
            raise ImportError("pytesseract não está disponível")
        
        # Configurações OCR
        self.ocr_language = self.config.get('ocr_language', 'por')
        self.ocr_dpi = self.config.get('ocr_dpi', 300)
        self.max_pages = self.config.get('ocr_max_pages', None)
        
        # Configurar caminho do Tesseract se especificado
        tesseract_cmd = self.config.get('tesseract_cmd', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.logger.info(f"OCRExtractor configurado - idioma: {self.ocr_language}, DPI: {self.ocr_dpi}")
    
    @property
    def extractor_name(self) -> str:
        """Nome do extrator."""
        return "OCR PDF Text Extractor"
    
    @property
    def extractor_type(self) -> str:
        """Tipo do extrator."""
        return "ocr"
    
    def is_suitable_for(self, pdf_path: Path) -> bool:
        """
        Verifica se o extrator OCR é adequado para o PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True se adequado (sempre, mas OCR é mais lento)
        """
        if not self.validate_pdf(pdf_path):
            return False
        
        # OCR pode processar qualquer PDF, mas é mais lento
        # Em uma estratégia automática, seria usado como fallback
        return True
    
    def extract_text(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto do PDF usando OCR.
        
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
        
        return self._extract_with_ocr(pdf_path, start_time, file_info)
    
    def _extract_with_ocr(self, pdf_path: Path, start_time: float, file_info: Dict[str, Any]) -> ExtractionResult:
        """
        Extrai texto usando OCR.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            start_time: Tempo de início do processamento
            file_info: Informações do arquivo
            
        Returns:
            Resultado da extração
        """
        text_content = []
        pages_processed = 0
        images = None
        error_message = None
        
        try:
            self.logger.info(f"Iniciando extração OCR: {pdf_path}")
            
            # Converte PDF para imagens
            self.logger.info(f"Convertendo PDF para imagens (DPI: {self.ocr_dpi})...")
            images = convert_from_path(pdf_path, dpi=self.ocr_dpi)
            
            total_pages = len(images)
            pages_to_process = min(total_pages, self.max_pages) if self.max_pages else total_pages
            
            self.logger.info(f"PDF tem {total_pages} páginas, processando {pages_to_process}")
            
            for page_num in range(pages_to_process):
                try:
                    self.logger.info(f"OCR - Página {page_num + 1}/{pages_to_process}")
                    
                    # Aplica OCR na imagem
                    text = pytesseract.image_to_string(
                        images[page_num], 
                        lang=self.ocr_language,
                        config='--psm 1'  # Page Segmentation Mode para melhor detecção
                    )
                    
                    if text.strip():
                        text_content.append(f"=== PÁGINA {page_num + 1} ===\n{text}\n")
                        pages_processed += 1
                    else:
                        self.logger.warning(f"Página {page_num + 1} não contém texto extraível")
                    
                    # Log de progresso a cada 5 páginas (OCR é mais lento)
                    if (page_num + 1) % 5 == 0:
                        self.logger.info(f"OCR processou {page_num + 1}/{pages_to_process} páginas")
                        
                except Exception as page_error:
                    self.logger.error(f"Erro ao processar página {page_num + 1} com OCR: {page_error}")
                    continue
            
            # Adiciona nota se nem todas as páginas foram processadas
            if self.max_pages and total_pages > self.max_pages:
                note = f"\n[NOTA: PDF tem {total_pages} páginas, mas apenas {self.max_pages} foram processadas via OCR]\n"
                text_content.append(note)
            
            success = len(text_content) > 0
            final_text = "\n".join(text_content) if success else ""
            
            if success:
                self.logger.info(f"OCR extraiu texto de {pages_processed} páginas")
            else:
                error_message = "OCR não conseguiu extrair texto de nenhuma página"
            
            return ExtractionResult(
                file_path=pdf_path,
                success=success,
                text_content=final_text,
                pages_processed=pages_processed,
                extraction_method="Tesseract OCR",
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message=error_message,
                metadata={
                    'ocr_language': self.ocr_language,
                    'ocr_dpi': self.ocr_dpi,
                    'total_pages': total_pages,
                    'pages_limited': self.max_pages is not None and total_pages > self.max_pages
                }
            )
            
        except Exception as e:
            error_msg = f"Erro na extração OCR: {e}"
            self.logger.error(error_msg)
            
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=pages_processed,
                extraction_method="Tesseract OCR",
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message=error_msg
            )
        
        finally:
            # Limpa todas as imagens da memória
            if images:
                for img in images:
                    if img:
                        try:
                            img.close()
                        except:
                            pass
            
            # Força limpeza de memória
            import gc
            gc.collect()
            self.logger.info("Recursos de imagem OCR liberados da memória")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Pré-processa imagem para melhorar a qualidade do OCR.
        
        Args:
            image: Imagem PIL para processamento
            
        Returns:
            Imagem processada
        """
        try:
            # Converte para escala de cinza se não estiver
            if image.mode != 'L':
                image = image.convert('L')
            
            # Melhora contraste (implementação básica)
            # Aqui poderiam ser adicionados filtros mais avançados
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Erro no pré-processamento da imagem: {e}")
            return image
    
    def test_ocr_availability(self) -> bool:
        """
        Testa se o OCR está funcionando corretamente.
        
        Returns:
            True se OCR está disponível e funcionando
        """
        try:
            # Cria uma imagem de teste simples
            from PIL import Image, ImageDraw, ImageFont
            
            test_image = Image.new('RGB', (200, 50), color='white')
            draw = ImageDraw.Draw(test_image)
            draw.text((10, 10), "Test OCR", fill='black')
            
            # Tenta extrair texto
            text = pytesseract.image_to_string(test_image, lang=self.ocr_language)
            
            return 'test' in text.lower() or 'ocr' in text.lower()
            
        except Exception as e:
            self.logger.error(f"Teste de OCR falhou: {e}")
            return False