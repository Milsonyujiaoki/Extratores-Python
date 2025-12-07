"""
Core module para o sistema de extração de PDFs.
Contém as classes base e interfaces principais.
"""

from .base_extractor import BaseExtractor
from .extraction_result import ExtractionResult
from .extractor_factory import ExtractorFactory
from .config_manager import ConfigManager

__all__ = [
    'BaseExtractor',
    'ExtractionResult', 
    'ExtractorFactory',
    'ConfigManager'
]