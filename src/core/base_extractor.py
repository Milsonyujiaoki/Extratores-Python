"""
Classe base abstrata para todos os extratores de PDF.
Define a interface comum que todos os extratores devem implementar.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Resultado de uma extração de PDF."""
    
    file_path: Path
    success: bool
    text_content: str
    pages_processed: int
    extraction_method: str
    processing_time: float
    file_size: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()
    
    @property
    def characters_extracted(self) -> int:
        """Número de caracteres extraídos."""
        return len(self.text_content) if self.text_content else 0
    
    @property
    def extraction_rate(self) -> float:
        """Taxa de extração (caracteres por segundo)."""
        return self.characters_extracted / self.processing_time if self.processing_time > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o resultado para dicionário."""
        return {
            'file_path': str(self.file_path),
            'success': self.success,
            'pages_processed': self.pages_processed,
            'characters_extracted': self.characters_extracted,
            'extraction_method': self.extraction_method,
            'processing_time': self.processing_time,
            'extraction_rate': self.extraction_rate,
            'file_size': self.file_size,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class BaseExtractor(ABC):
    """
    Classe base abstrata para extratores de PDF.
    Define a interface comum e funcionalidades básicas.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extrator.
        
        Args:
            config: Configurações específicas do extrator
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_extractor()
    
    @abstractmethod
    def _setup_extractor(self) -> None:
        """Configuração específica do extrator. Deve ser implementada pelas subclasses."""
        pass
    
    @abstractmethod
    def extract_text(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto de um arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            ExtractionResult com o resultado da extração
        """
        pass
    
    @abstractmethod
    def is_suitable_for(self, pdf_path: Path) -> bool:
        """
        Verifica se este extrator é adequado para o PDF específico.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True se o extrator é adequado, False caso contrário
        """
        pass
    
    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """Nome do extrator."""
        pass
    
    @property
    @abstractmethod
    def extractor_type(self) -> str:
        """Tipo do extrator (direct, ocr, hybrid)."""
        pass
    
    def validate_pdf(self, pdf_path: Path) -> bool:
        """
        Valida se o arquivo é um PDF válido e acessível.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True se o PDF é válido, False caso contrário
        """
        try:
            if not pdf_path.exists():
                self.logger.error(f"Arquivo não encontrado: {pdf_path}")
                return False
            
            if not pdf_path.is_file():
                self.logger.error(f"Caminho não aponta para um arquivo: {pdf_path}")
                return False
            
            if pdf_path.suffix.lower() != '.pdf':
                self.logger.error(f"Arquivo não é um PDF: {pdf_path}")
                return False
            
            if pdf_path.stat().st_size == 0:
                self.logger.error(f"Arquivo PDF está vazio: {pdf_path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao validar PDF {pdf_path}: {e}")
            return False
    
    def get_file_info(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Obtém informações básicas do arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dicionário com informações do arquivo
        """
        try:
            stat = pdf_path.stat()
            return {
                'file_size': stat.st_size,
                'creation_time': datetime.fromtimestamp(stat.st_ctime),
                'modification_time': datetime.fromtimestamp(stat.st_mtime),
                'file_extension': pdf_path.suffix,
                'file_name': pdf_path.name
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do arquivo {pdf_path}: {e}")
            return {}