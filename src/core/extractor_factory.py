"""
Factory para criação de extratores de PDF.
Implementa padrão Factory Method para criação flexível de extratores.
"""

from typing import Dict, Type, List, Optional
from pathlib import Path
import logging

from .base_extractor import BaseExtractor
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """
    Factory para criação de extratores de PDF.
    Gerencia diferentes tipos de extratores e suas instâncias.
    """
    
    _extractors: Dict[str, Type[BaseExtractor]] = {}
    _instances: Dict[str, BaseExtractor] = {}
    
    @classmethod
    def register_extractor(cls, extractor_type: str, extractor_class: Type[BaseExtractor]) -> None:
        """
        Registra um novo tipo de extrator.
        
        Args:
            extractor_type: Identificador do tipo de extrator
            extractor_class: Classe do extrator
        """
        cls._extractors[extractor_type] = extractor_class
        logger.info(f"Extrator registrado: {extractor_type} -> {extractor_class.__name__}")
    
    @classmethod
    def create_extractor(cls, extractor_type: str, config: Optional[ConfigManager] = None) -> BaseExtractor:
        """
        Cria uma instância de extrator.
        
        Args:
            extractor_type: Tipo do extrator (direct, ocr, hybrid)
            config: Configurações para o extrator
            
        Returns:
            Instância do extrator
            
        Raises:
            ValueError: Se o tipo de extrator não estiver registrado
        """
        if extractor_type not in cls._extractors:
            available_types = list(cls._extractors.keys())
            raise ValueError(f"Tipo de extrator '{extractor_type}' não registrado. "
                           f"Tipos disponíveis: {available_types}")
        
        extractor_class = cls._extractors[extractor_type]
        config_dict = config.config.to_dict() if config else {}
        
        return extractor_class(config_dict)
    
    @classmethod
    def get_extractor(cls, extractor_type: str, config: Optional[ConfigManager] = None) -> BaseExtractor:
        """
        Obtém uma instância de extrator (singleton por tipo).
        
        Args:
            extractor_type: Tipo do extrator
            config: Configurações para o extrator
            
        Returns:
            Instância do extrator (reutilizada se já existir)
        """
        cache_key = f"{extractor_type}_{id(config) if config else 'default'}"
        
        if cache_key not in cls._instances:
            cls._instances[cache_key] = cls.create_extractor(extractor_type, config)
        
        return cls._instances[cache_key]
    
    @classmethod
    def get_available_extractors(cls) -> List[str]:
        """
        Retorna lista de extratores disponíveis.
        
        Returns:
            Lista de tipos de extratores registrados
        """
        return list(cls._extractors.keys())
    
    @classmethod
    def auto_select_extractor(cls, pdf_path: Path, config: Optional[ConfigManager] = None) -> BaseExtractor:
        """
        Seleciona automaticamente o melhor extrator para um PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            config: Configurações do sistema
            
        Returns:
            Extrator mais adequado para o arquivo
        """
        logger.info(f"Selecionando extrator automático para: {pdf_path}")
        
        # Estratégia de seleção automática
        suitable_extractors = []
        
        for extractor_type in cls._extractors.keys():
            try:
                extractor = cls.get_extractor(extractor_type, config)
                if extractor.is_suitable_for(pdf_path):
                    suitable_extractors.append((extractor_type, extractor))
            except Exception as e:
                logger.warning(f"Erro ao verificar adequação do extrator {extractor_type}: {e}")
        
        if not suitable_extractors:
            # Fallback para extrator híbrido se disponível
            if 'hybrid' in cls._extractors:
                logger.info("Nenhum extrator específico adequado, usando híbrido")
                return cls.get_extractor('hybrid', config)
            elif cls._extractors:
                # Usa o primeiro extrator disponível
                first_type = list(cls._extractors.keys())[0]
                logger.warning(f"Usando extrator padrão: {first_type}")
                return cls.get_extractor(first_type, config)
            else:
                raise ValueError("Nenhum extrator disponível")
        
        # Prioriza extrator híbrido se disponível
        for extractor_type, extractor in suitable_extractors:
            if extractor_type == 'hybrid':
                logger.info("Selecionado extrator híbrido")
                return extractor
        
        # Usa o primeiro extrator adequado
        selected_type, selected_extractor = suitable_extractors[0]
        logger.info(f"Selecionado extrator: {selected_type}")
        return selected_extractor
    
    @classmethod
    def clear_cache(cls) -> None:
        """Limpa o cache de instâncias de extratores."""
        cls._instances.clear()
        logger.info("Cache de extratores limpo")
    
    @classmethod
    def get_extractor_info(cls) -> Dict[str, Dict[str, str]]:
        """
        Retorna informações sobre todos os extratores registrados.
        
        Returns:
            Dicionário com informações dos extratores
        """
        info = {}
        
        for extractor_type, extractor_class in cls._extractors.items():
            try:
                # Cria instância temporária para obter informações
                temp_instance = extractor_class({})
                info[extractor_type] = {
                    'name': temp_instance.extractor_name,
                    'type': temp_instance.extractor_type,
                    'class': extractor_class.__name__,
                    'module': extractor_class.__module__
                }
            except Exception as e:
                info[extractor_type] = {
                    'name': 'Erro ao obter nome',
                    'type': 'Erro ao obter tipo',
                    'class': extractor_class.__name__,
                    'module': extractor_class.__module__,
                    'error': str(e)
                }
        
        return info


# Decorator para registro automático de extratores
def register_extractor(extractor_type: str):
    """
    Decorator para registro automático de extratores.
    
    Args:
        extractor_type: Tipo do extrator para registro
    """
    def decorator(extractor_class: Type[BaseExtractor]):
        ExtractorFactory.register_extractor(extractor_type, extractor_class)
        return extractor_class
    
    return decorator