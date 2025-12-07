"""
Gerenciador de configurações avançado para o sistema de extração.
Suporta múltiplos formatos e validação de configurações.
"""

import configparser
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """Configuração para extração de PDFs."""
    
    # Caminhos
    input_directory: Optional[str] = None
    output_directory: str = "./output"
    
    # Configurações de processamento
    max_workers: int = 4
    batch_size: int = 10
    max_file_size_mb: int = 100
    
    # Configurações de extração
    extraction_method: str = "hybrid"  # direct, ocr, hybrid, auto
    ocr_language: str = "por"
    ocr_dpi: int = 300
    ocr_max_pages: Optional[int] = None
    
    # Configurações de qualidade
    min_text_length: int = 10
    skip_password_protected: bool = True
    skip_corrupted_files: bool = True
    
    # Configurações de saída
    output_format: str = "txt"  # txt, json, csv
    include_metadata: bool = True
    create_summary_report: bool = True
    
    # Configurações de log
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "./logs/extraction.log"
    
    # Configurações avançadas
    preserve_structure: bool = False
    extract_images: bool = False
    extract_tables: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionConfig':
        """Cria instância a partir de dicionário."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class ConfigManager:
    """
    Gerenciador avançado de configurações.
    Suporta múltiplos formatos e validação.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self.config = ExtractionConfig()
        self.logger = logging.getLogger(__name__)
        
        if config_path and config_path.exists():
            self.load_config(config_path)
    
    def load_config(self, config_path: Path) -> ExtractionConfig:
        """
        Carrega configuração de arquivo.
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            Configuração carregada
        """
        try:
            if not config_path.exists():
                self.logger.warning(f"Arquivo de configuração não encontrado: {config_path}")
                return self.config
            
            file_extension = config_path.suffix.lower()
            
            if file_extension == '.ini':
                return self._load_ini_config(config_path)
            elif file_extension == '.json':
                return self._load_json_config(config_path)
            elif file_extension in ['.yml', '.yaml']:
                return self._load_yaml_config(config_path)
            else:
                self.logger.error(f"Formato de configuração não suportado: {file_extension}")
                return self.config
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração de {config_path}: {e}")
            return self.config
    
    def _load_ini_config(self, config_path: Path) -> ExtractionConfig:
        """Carrega configuração de arquivo INI."""
        config_parser = configparser.ConfigParser()
        
        # Tenta diferentes encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
            try:
                config_parser.read(config_path, encoding=encoding)
                break
            except Exception as e:
                self.logger.debug(f"Falha com encoding {encoding}: {e}")
                continue
        else:
            self.logger.error(f"Não foi possível carregar {config_path} com nenhum encoding")
            return self.config
        
        # Converte INI para dicionário
        config_dict = {}
        
        # Mapeamento de seções INI para campos da configuração
        section_mapping = {
            'Paths': ['input_directory', 'output_directory', 'log_file_path'],
            'Processing': ['max_workers', 'batch_size', 'max_file_size_mb'],
            'Extraction': ['extraction_method', 'ocr_language', 'ocr_dpi', 'ocr_max_pages'],
            'Quality': ['min_text_length', 'skip_password_protected', 'skip_corrupted_files'],
            'Output': ['output_format', 'include_metadata', 'create_summary_report'],
            'Logging': ['log_level', 'log_to_file'],
            'Advanced': ['preserve_structure', 'extract_images', 'extract_tables']
        }
        
        for section_name, fields in section_mapping.items():
            if config_parser.has_section(section_name):
                section = config_parser[section_name]
                for field in fields:
                    if field in section:
                        value = section[field]
                        # Conversão de tipos
                        config_dict[field] = self._convert_config_value(field, value)
        
        # Compatibilidade com config antigo
        if config_parser.has_section('Paths'):
            paths_section = config_parser['Paths']
            if 'PDF_PATH' in paths_section:
                pdf_path = paths_section['PDF_PATH']
                if pdf_path:
                    config_dict['input_directory'] = str(Path(pdf_path).parent)
        
        self.config = ExtractionConfig.from_dict(config_dict)
        self.logger.info(f"Configuração INI carregada de {config_path}")
        return self.config
    
    def _load_json_config(self, config_path: Path) -> ExtractionConfig:
        """Carrega configuração de arquivo JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            self.config = ExtractionConfig.from_dict(config_dict)
            self.logger.info(f"Configuração JSON carregada de {config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração JSON: {e}")
            return self.config
    
    def _load_yaml_config(self, config_path: Path) -> ExtractionConfig:
        """Carrega configuração de arquivo YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            self.config = ExtractionConfig.from_dict(config_dict)
            self.logger.info(f"Configuração YAML carregada de {config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração YAML: {e}")
            return self.config
    
    def _convert_config_value(self, field: str, value: str) -> Any:
        """
        Converte valores de string para o tipo apropriado.
        
        Args:
            field: Nome do campo
            value: Valor como string
            
        Returns:
            Valor convertido para o tipo apropriado
        """
        # Mapeamento de tipos por campo
        int_fields = ['max_workers', 'batch_size', 'max_file_size_mb', 'ocr_dpi', 
                      'ocr_max_pages', 'min_text_length']
        bool_fields = ['skip_password_protected', 'skip_corrupted_files', 
                      'include_metadata', 'create_summary_report', 'log_to_file',
                      'preserve_structure', 'extract_images', 'extract_tables']
        
        try:
            if field in int_fields:
                return int(value) if value else None
            elif field in bool_fields:
                return value.lower() in ['true', '1', 'yes', 'on']
            else:
                return value
        except ValueError:
            self.logger.warning(f"Erro ao converter valor '{value}' para campo '{field}'")
            return value
    
    def save_config(self, config_path: Path, format: str = 'json') -> bool:
        """
        Salva configuração em arquivo.
        
        Args:
            config_path: Caminho para salvar
            format: Formato do arquivo (json, yaml, ini)
            
        Returns:
            True se salvo com sucesso
        """
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                return self._save_json_config(config_path)
            elif format == 'yaml':
                return self._save_yaml_config(config_path)
            elif format == 'ini':
                return self._save_ini_config(config_path)
            else:
                self.logger.error(f"Formato não suportado: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}")
            return False
    
    def _save_json_config(self, config_path: Path) -> bool:
        """Salva configuração em formato JSON."""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
        return True
    
    def _save_yaml_config(self, config_path: Path) -> bool:
        """Salva configuração em formato YAML."""
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config.to_dict(), f, default_flow_style=False, allow_unicode=True)
        return True
    
    def _save_ini_config(self, config_path: Path) -> bool:
        """Salva configuração em formato INI."""
        config_parser = configparser.ConfigParser()
        
        # Organiza configurações por seções
        sections = {
            'Paths': {
                'input_directory': self.config.input_directory or '',
                'output_directory': self.config.output_directory,
                'log_file_path': self.config.log_file_path
            },
            'Processing': {
                'max_workers': str(self.config.max_workers),
                'batch_size': str(self.config.batch_size),
                'max_file_size_mb': str(self.config.max_file_size_mb)
            },
            'Extraction': {
                'extraction_method': self.config.extraction_method,
                'ocr_language': self.config.ocr_language,
                'ocr_dpi': str(self.config.ocr_dpi),
                'ocr_max_pages': str(self.config.ocr_max_pages) if self.config.ocr_max_pages else ''
            }
        }
        
        for section_name, section_data in sections.items():
            config_parser.add_section(section_name)
            for key, value in section_data.items():
                config_parser.set(section_name, key, str(value))
        
        with open(config_path, 'w', encoding='utf-8') as f:
            config_parser.write(f)
        
        return True
    
    def validate_config(self) -> List[str]:
        """
        Valida a configuração atual.
        
        Returns:
            Lista de erros encontrados (vazia se tudo estiver correto)
        """
        errors = []
        
        # Validação de diretórios
        if self.config.input_directory:
            input_path = Path(self.config.input_directory)
            if not input_path.exists():
                errors.append(f"Diretório de entrada não existe: {input_path}")
        
        # Validação de valores numéricos
        if self.config.max_workers < 1:
            errors.append("max_workers deve ser maior que 0")
        
        if self.config.batch_size < 1:
            errors.append("batch_size deve ser maior que 0")
        
        if self.config.ocr_dpi < 50:
            errors.append("ocr_dpi deve ser pelo menos 50")
        
        # Validação de enums
        valid_methods = ['direct', 'ocr', 'hybrid', 'auto']
        if self.config.extraction_method not in valid_methods:
            errors.append(f"extraction_method deve ser um de: {valid_methods}")
        
        valid_formats = ['txt', 'json', 'csv']
        if self.config.output_format not in valid_formats:
            errors.append(f"output_format deve ser um de: {valid_formats}")
        
        return errors
    
    def get_tesseract_config(self) -> Dict[str, Any]:
        """Retorna configuração específica para Tesseract."""
        return {
            'lang': self.config.ocr_language,
            'dpi': self.config.ocr_dpi,
            'max_pages': self.config.ocr_max_pages
        }
    
    def get_output_path(self, pdf_path: Path, suffix: str = '') -> Path:
        """
        Gera caminho de saída para um arquivo PDF.
        Inclui informações da estrutura de diretórios no nome do arquivo.
        
        Args:
            pdf_path: Caminho do arquivo PDF original
            suffix: Sufixo adicional para o nome do arquivo
            
        Returns:
            Caminho de saída
        """
        output_dir = Path(self.config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome base do arquivo original
        base_name = pdf_path.stem
        
        # Constrói informações hierárquicas dos diretórios
        path_parts = []
        current_path = pdf_path.parent
        
        # Coleta até 3 níveis de diretórios acima
        for _ in range(3):
            if current_path.name and current_path.name not in ['.', '..', 'pdfs']:
                folder_name = self._clean_filename(current_path.name)
                if folder_name:  # Só adiciona se não estiver vazio após limpeza
                    path_parts.append(folder_name)
                current_path = current_path.parent
            else:
                break
        
        # Inverte para ter a ordem correta (do mais geral para o mais específico)
        path_parts.reverse()
        
        # Combina informações hierárquicas com nome do arquivo
        if path_parts:
            hierarchy = '__'.join(path_parts)  # Usa __ para separar níveis
            base_name = f"{hierarchy}__{base_name}"
        
        # Adiciona sufixo se fornecido
        if suffix:
            base_name += f"_{suffix}"
        
        # Limita tamanho do nome (Windows tem limite de 255 caracteres)
        if len(base_name) > 200:
            base_name = base_name[:200] + "_truncated"
        
        # Determina extensão baseada no formato de saída
        if self.config.output_format == 'txt':
            return output_dir / f"{base_name}.txt"
        elif self.config.output_format == 'json':
            return output_dir / f"{base_name}.json"
        elif self.config.output_format == 'csv':
            return output_dir / f"{base_name}.csv"
        else:
            return output_dir / f"{base_name}.txt"
    
    def _clean_filename(self, filename: str) -> str:
        """
        Limpa nome de arquivo removendo caracteres especiais.
        
        Args:
            filename: Nome do arquivo original
            
        Returns:
            Nome limpo
        """
        import re
        # Remove caracteres especiais e substitui por underscore
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove espaços múltiplos e substitui por underscore
        cleaned = re.sub(r'\s+', '_', cleaned)
        # Remove underscores múltiplos
        cleaned = re.sub(r'_+', '_', cleaned)
        # Remove underscores no início e fim
        cleaned = cleaned.strip('_')
        return cleaned