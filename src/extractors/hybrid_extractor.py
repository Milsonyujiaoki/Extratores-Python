"""
Extrator híbrido que combina extração direta e OCR.
Tenta extração direta primeiro, usa OCR como fallback.
"""

import time
from pathlib import Path
from typing import Dict, Any
import logging

from ..core.base_extractor import BaseExtractor, ExtractionResult
from ..core.extractor_factory import register_extractor, ExtractorFactory

logger = logging.getLogger(__name__)


@register_extractor('hybrid')
class HybridExtractor(BaseExtractor):
    """
    Extrator híbrido que combina métodos diretos e OCR.
    Estratégia adaptativa para máxima eficiência e robustez.
    """
    
    def _setup_extractor(self) -> None:
        """Configuração específica do extrator híbrido."""
        self.min_text_threshold = self.config.get('min_text_length', 50)
        self.prefer_direct = self.config.get('prefer_direct', True)
        self.ocr_fallback = self.config.get('ocr_fallback', True)
        
        # Configurações para estratégia de seleção
        self.direct_attempt_timeout = self.config.get('direct_timeout', 30)  # segundos
        self.ocr_quality_threshold = self.config.get('ocr_quality_threshold', 0.7)
        
        self.logger.info(f"HybridExtractor configurado - threshold: {self.min_text_threshold}, fallback OCR: {self.ocr_fallback}")
    
    @property
    def extractor_name(self) -> str:
        """Nome do extrator."""
        return "Hybrid PDF Text Extractor"
    
    @property
    def extractor_type(self) -> str:
        """Tipo do extrator."""
        return "hybrid"
    
    def is_suitable_for(self, pdf_path: Path) -> bool:
        """
        Verifica se o extrator híbrido é adequado para o PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True (híbrido é adequado para qualquer PDF)
        """
        return self.validate_pdf(pdf_path)
    
    def extract_text(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto usando estratégia híbrida.
        
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
        
        self.logger.info(f"Iniciando extração híbrida: {pdf_path}")
        
        # Estratégia 1: Tenta extração direta primeiro
        if self.prefer_direct:
            direct_result = self._try_direct_extraction(pdf_path)
            
            if self._is_extraction_successful(direct_result):
                self.logger.info("Extração direta bem-sucedida")
                direct_result.extraction_method = f"{self.extractor_name} (Direct)"
                return direct_result
            else:
                self.logger.info("Extração direta falhou ou produziu pouco texto")
        
        # Estratégia 2: Tenta OCR como fallback
        if self.ocr_fallback:
            self.logger.info("Tentando extração OCR como fallback...")
            ocr_result = self._try_ocr_extraction(pdf_path)
            
            if self._is_extraction_successful(ocr_result):
                self.logger.info("Extração OCR bem-sucedida")
                ocr_result.extraction_method = f"{self.extractor_name} (OCR)"
                return ocr_result
            else:
                self.logger.warning("Extração OCR também falhou")
        
        # Se ambos falharam, retorna o melhor resultado disponível
        if self.prefer_direct and hasattr(self, '_last_direct_result'):
            result = self._last_direct_result
            result.extraction_method = f"{self.extractor_name} (Direct - Partial)"
        elif hasattr(self, '_last_ocr_result'):
            result = self._last_ocr_result
            result.extraction_method = f"{self.extractor_name} (OCR - Partial)"
        else:
            result = ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=0,
                extraction_method=self.extractor_name,
                processing_time=time.time() - start_time,
                file_size=file_info.get('file_size', 0),
                error_message="Nenhum método de extração foi bem-sucedido"
            )
        
        return result
    
    def _try_direct_extraction(self, pdf_path: Path) -> ExtractionResult:
        """
        Tenta extração direta.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Resultado da extração direta
        """
        try:
            direct_extractor = ExtractorFactory.get_extractor('direct', None)
            # Aplica configurações do híbrido ao extrator direto
            direct_extractor.config.update(self.config)
            
            result = direct_extractor.extract_text(pdf_path)
            self._last_direct_result = result
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na tentativa de extração direta: {e}")
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=0,
                extraction_method="Direct (Error)",
                processing_time=0,
                file_size=0,
                error_message=str(e)
            )
    
    def _try_ocr_extraction(self, pdf_path: Path) -> ExtractionResult:
        """
        Tenta extração OCR.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Resultado da extração OCR
        """
        try:
            ocr_extractor = ExtractorFactory.get_extractor('ocr', None)
            # Aplica configurações do híbrido ao extrator OCR
            ocr_extractor.config.update(self.config)
            
            result = ocr_extractor.extract_text(pdf_path)
            self._last_ocr_result = result
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na tentativa de extração OCR: {e}")
            return ExtractionResult(
                file_path=pdf_path,
                success=False,
                text_content="",
                pages_processed=0,
                extraction_method="OCR (Error)",
                processing_time=0,
                file_size=0,
                error_message=str(e)
            )
    
    def _is_extraction_successful(self, result: ExtractionResult) -> bool:
        """
        Verifica se uma extração foi bem-sucedida.
        
        Args:
            result: Resultado da extração
            
        Returns:
            True se a extração foi bem-sucedida
        """
        if not result.success:
            return False
        
        # Verifica se há texto suficiente
        if len(result.text_content.strip()) < self.min_text_threshold:
            self.logger.info(f"Texto extraído muito curto: {len(result.text_content)} caracteres")
            return False
        
        # Verifica se há páginas processadas
        if result.pages_processed == 0:
            self.logger.info("Nenhuma página foi processada com sucesso")
            return False
        
        return True
    
    def _estimate_pdf_type(self, pdf_path: Path) -> str:
        """
        Estima o tipo de PDF para otimizar estratégia.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Tipo estimado: 'native', 'scanned', 'mixed'
        """
        try:
            # Implementação básica - poderia ser mais sofisticada
            # Por exemplo, analisando metadados, tamanho do arquivo, etc.
            
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            
            # PDFs escaneados tendem a ser maiores devido às imagens
            if file_size_mb > 50:
                return 'scanned'
            elif file_size_mb < 1:
                return 'native'
            else:
                return 'mixed'
                
        except Exception:
            return 'mixed'  # Default para estratégia híbrida
    
    def extract_with_adaptive_strategy(self, pdf_path: Path) -> ExtractionResult:
        """
        Extração com estratégia adaptativa baseada no tipo de PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Resultado da extração
        """
        pdf_type = self._estimate_pdf_type(pdf_path)
        self.logger.info(f"Tipo de PDF estimado: {pdf_type}")
        
        if pdf_type == 'native':
            # Para PDFs nativos, prioriza extração direta
            return self.extract_text(pdf_path)
        
        elif pdf_type == 'scanned':
            # Para PDFs escaneados, vai direto para OCR
            self.logger.info("PDF escaneado detectado, usando OCR diretamente")
            ocr_result = self._try_ocr_extraction(pdf_path)
            if ocr_result.success:
                ocr_result.extraction_method = f"{self.extractor_name} (OCR Direct)"
                return ocr_result
            
            # Fallback para extração direta se OCR falhar
            direct_result = self._try_direct_extraction(pdf_path)
            if direct_result.success:
                direct_result.extraction_method = f"{self.extractor_name} (Direct Fallback)"
            return direct_result
        
        else:  # mixed
            # Para PDFs mistos, usa estratégia híbrida padrão
            return self.extract_text(pdf_path)
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas das extrações realizadas.
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'direct_attempts': getattr(self, '_direct_attempts', 0),
            'ocr_attempts': getattr(self, '_ocr_attempts', 0),
            'hybrid_successes': getattr(self, '_hybrid_successes', 0),
            'total_extractions': getattr(self, '_total_extractions', 0)
        }
        
        if stats['total_extractions'] > 0:
            stats['success_rate'] = stats['hybrid_successes'] / stats['total_extractions']
        else:
            stats['success_rate'] = 0.0
        
        return stats