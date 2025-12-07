"""
Módulo de extratores de PDF.
Contém implementações específicas para diferentes tipos de extração.
"""

from .direct_extractor import DirectExtractor
from .ocr_extractor import OCRExtractor
from .hybrid_extractor import HybridExtractor

__all__ = [
    'DirectExtractor',
    'OCRExtractor', 
    'HybridExtractor'
]