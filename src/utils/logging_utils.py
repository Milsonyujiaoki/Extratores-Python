"""
Utilitários de logging para o sistema de extração.
Configuração avançada de logs com múltiplos handlers.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Formatter colorido para console."""
    
    # Códigos ANSI para cores
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Formata log com cores."""
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class LoggerSetup:
    """
    Configurador de sistema de logging.
    Suporta múltiplos handlers e formatações.
    """
    
    @staticmethod
    def setup_logging(
        log_level: str = 'INFO',
        log_to_file: bool = True,
        log_file_path: Optional[Path] = None,
        log_to_console: bool = True,
        colored_console: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Configura sistema de logging.
        
        Args:
            log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Se deve logar em arquivo
            log_file_path: Caminho do arquivo de log
            log_to_console: Se deve logar no console
            colored_console: Se deve usar cores no console
            max_file_size: Tamanho máximo do arquivo de log
            backup_count: Número de arquivos de backup
            
        Returns:
            Logger configurado
        """
        # Converte nível de string para constante
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configuração básica
        logging.basicConfig(level=numeric_level, handlers=[])
        
        # Remove handlers existentes para evitar duplicação
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Formato base para logs
        base_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        detailed_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        
        # Handler para console
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            
            if colored_console:
                console_formatter = ColoredFormatter(base_format)
            else:
                console_formatter = logging.Formatter(base_format)
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Handler para arquivo
        if log_to_file:
            if log_file_path is None:
                log_file_path = Path('./logs/extraction.log')
            
            # Cria diretório se não existir
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Usa RotatingFileHandler para gerenciar tamanho
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            
            # Formato mais detalhado para arquivo
            file_formatter = logging.Formatter(detailed_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        logger = logging.getLogger('pdf_extractor')
        logger.info(f"Sistema de logging configurado - nível: {log_level}")
        
        return logger
    
    @staticmethod
    def setup_performance_logger(log_file_path: Optional[Path] = None) -> logging.Logger:
        """
        Configura logger específico para métricas de performance.
        
        Args:
            log_file_path: Caminho do arquivo de log de performance
            
        Returns:
            Logger de performance
        """
        if log_file_path is None:
            log_file_path = Path('./logs/performance.log')
        
        # Cria logger específico
        perf_logger = logging.getLogger('pdf_extractor.performance')
        perf_logger.setLevel(logging.INFO)
        
        # Remove handlers existentes
        for handler in perf_logger.handlers[:]:
            perf_logger.removeHandler(handler)
        
        # Handler para arquivo de performance
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        
        # Formato específico para performance
        perf_format = '%(asctime)s - %(message)s'
        file_formatter = logging.Formatter(perf_format)
        file_handler.setFormatter(file_formatter)
        
        perf_logger.addHandler(file_handler)
        perf_logger.propagate = False  # Não propaga para logger pai
        
        return perf_logger


class PerformanceLogger:
    """
    Logger especializado para métricas de performance.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa logger de performance.
        
        Args:
            logger: Logger específico (opcional)
        """
        self.logger = logger or LoggerSetup.setup_performance_logger()
    
    def log_extraction_performance(
        self,
        file_path: Path,
        extraction_method: str,
        processing_time: float,
        file_size: int,
        pages_processed: int,
        characters_extracted: int,
        success: bool
    ) -> None:
        """
        Loga métricas de performance de extração.
        
        Args:
            file_path: Caminho do arquivo processado
            extraction_method: Método de extração usado
            processing_time: Tempo de processamento
            file_size: Tamanho do arquivo
            pages_processed: Páginas processadas
            characters_extracted: Caracteres extraídos
            success: Se a extração foi bem-sucedida
        """
        metrics = {
            'file': str(file_path),
            'method': extraction_method,
            'time': round(processing_time, 3),
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'pages': pages_processed,
            'characters': characters_extracted,
            'success': success,
            'chars_per_second': round(characters_extracted / processing_time, 2) if processing_time > 0 else 0,
            'pages_per_second': round(pages_processed / processing_time, 2) if processing_time > 0 else 0
        }
        
        metric_str = ' | '.join([f"{k}={v}" for k, v in metrics.items()])
        self.logger.info(f"EXTRACTION_METRICS | {metric_str}")
    
    def log_batch_performance(
        self,
        batch_size: int,
        total_time: float,
        successful_count: int,
        failed_count: int,
        total_characters: int
    ) -> None:
        """
        Loga métricas de performance de lote.
        
        Args:
            batch_size: Tamanho do lote
            total_time: Tempo total de processamento
            successful_count: Número de sucessos
            failed_count: Número de falhas
            total_characters: Total de caracteres extraídos
        """
        metrics = {
            'batch_size': batch_size,
            'total_time': round(total_time, 3),
            'successful': successful_count,
            'failed': failed_count,
            'success_rate': round(successful_count / (successful_count + failed_count), 3) if (successful_count + failed_count) > 0 else 0,
            'files_per_second': round(batch_size / total_time, 2) if total_time > 0 else 0,
            'chars_per_second': round(total_characters / total_time, 2) if total_time > 0 else 0
        }
        
        metric_str = ' | '.join([f"{k}={v}" for k, v in metrics.items()])
        self.logger.info(f"BATCH_METRICS | {metric_str}")


def get_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Obtém logger configurado.
    
    Args:
        name: Nome do logger
        level: Nível de log
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Se o logger não tem handlers, configura com setup básico
        LoggerSetup.setup_logging(log_level=level)
    
    return logger


def log_function_call(func):
    """
    Decorator para logar chamadas de função.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        Função decorada
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log entrada
        logger.debug(f"Chamando {func.__name__} com args={args}, kwargs={kwargs}")
        
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log sucesso
            logger.debug(f"{func.__name__} concluída em {duration:.3f}s")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log erro
            logger.error(f"{func.__name__} falhou após {duration:.3f}s: {e}")
            raise
    
    return wrapper