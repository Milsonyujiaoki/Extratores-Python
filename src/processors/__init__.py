"""
Módulo de processadores para extração de PDFs.
Contém processadores para diferentes cenários de uso.
"""

from .async_processor import AsyncPDFProcessor, ProcessingStats

__all__ = [
    'AsyncPDFProcessor',
    'ProcessingStats'
]