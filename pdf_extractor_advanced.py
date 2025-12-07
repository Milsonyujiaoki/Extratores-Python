"""
Script principal para extração avançada de PDFs.
Implementa processamento assíncrono, paralelo e descoberta recursiva.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
import json

# Adiciona o diretório src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config_manager import ConfigManager, ExtractionConfig
from src.core.extractor_factory import ExtractorFactory
from src.processors.async_processor import AsyncPDFProcessor
from src.utils.logging_utils import LoggerSetup, PerformanceLogger
from src.extractors import DirectExtractor, OCRExtractor, HybridExtractor


async def main():
    """Função principal assíncrona."""
    
    # Parse de argumentos
    parser = argparse.ArgumentParser(
        description='Extrator avançado de PDFs com processamento paralelo e assíncrono',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Processar diretório específico
  python pdf_extractor_advanced.py -d "/caminho/para/pdfs" -t hybrid

  # Processar com configuração personalizada
  python pdf_extractor_advanced.py -d "/pdfs" -c config.json -w 8

  # Apenas descobrir arquivos sem processar
  python pdf_extractor_advanced.py -d "/pdfs" --discover-only

  # Processar com relatório detalhado
  python pdf_extractor_advanced.py -d "/pdfs" -r relatorio.json --verbose

Tipos de extratores disponíveis:
  - auto: Seleção automática baseada no arquivo
  - direct: Extração direta (pdfplumber + PyPDF2)
  - ocr: OCR com Tesseract
  - hybrid: Combina direct + OCR (recomendado)
        """
    )
    
    # Argumentos principais
    parser.add_argument(
        '-d', '--directory',
        type=Path,
        required=True,
        help='Diretório contendo arquivos PDF'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Diretório de saída (padrão: ./output)'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=Path,
        help='Arquivo de configuração (JSON, YAML ou INI)'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['auto', 'direct', 'ocr', 'hybrid'],
        default='auto',
        help='Tipo de extrator (padrão: auto)'
    )
    
    # Configurações de processamento
    parser.add_argument(
        '-w', '--workers',
        type=int,
        help='Número de workers paralelos'
    )
    
    parser.add_argument(
        '-b', '--batch-size',
        type=int,
        help='Tamanho do lote para processamento'
    )
    
    parser.add_argument(
        '--max-file-size',
        type=int,
        help='Tamanho máximo de arquivo em MB'
    )
    
    # Opções de saída
    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'json', 'csv'],
        help='Formato de saída'
    )
    
    parser.add_argument(
        '-r', '--report',
        type=Path,
        help='Caminho para salvar relatório de processamento'
    )
    
    # Configurações de OCR
    parser.add_argument(
        '--ocr-lang',
        default='por',
        help='Idioma para OCR (padrão: por)'
    )
    
    parser.add_argument(
        '--ocr-dpi',
        type=int,
        help='DPI para OCR'
    )
    
    # Opções de execução
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Busca recursiva em subdiretórios (padrão: ativo)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Desabilita busca recursiva'
    )
    
    parser.add_argument(
        '--discover-only',
        action='store_true',
        help='Apenas descobre arquivos sem processar'
    )
    
    # Configurações de log
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Saída detalhada (DEBUG)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Saída mínima (ERROR apenas)'
    )
    
    parser.add_argument(
        '--log-file',
        type=Path,
        help='Arquivo de log personalizado'
    )
    
    args = parser.parse_args()
    
    # Configura logging
    log_level = 'DEBUG' if args.verbose else 'ERROR' if args.quiet else 'INFO'
    logger = LoggerSetup.setup_logging(
        log_level=log_level,
        log_file_path=args.log_file
    )
    
    logger.info("=== Extrator Avançado de PDFs ===")
    logger.info(f"Diretório de entrada: {args.directory}")
    
    # Valida diretório de entrada
    if not args.directory.exists():
        logger.error(f"Diretório não encontrado: {args.directory}")
        sys.exit(1)
    
    if not args.directory.is_dir():
        logger.error(f"Caminho não é um diretório: {args.directory}")
        sys.exit(1)
    
    # Carrega configuração
    config_manager = ConfigManager(args.config)
    
    # Sobrescreve configurações com argumentos da linha de comando
    if args.output:
        config_manager.config.output_directory = str(args.output)
    if args.workers:
        config_manager.config.max_workers = args.workers
    if args.batch_size:
        config_manager.config.batch_size = args.batch_size
    if args.max_file_size:
        config_manager.config.max_file_size_mb = args.max_file_size
    if args.format:
        config_manager.config.output_format = args.format
    if args.ocr_lang:
        config_manager.config.ocr_language = args.ocr_lang
    if args.ocr_dpi:
        config_manager.config.ocr_dpi = args.ocr_dpi
    
    # Configura diretório de entrada
    config_manager.config.input_directory = str(args.directory)
    
    # Valida configuração
    config_errors = config_manager.validate_config()
    if config_errors:
        logger.error("Erros na configuração:")
        for error in config_errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info(f"Configuração carregada: {config_manager.config.max_workers} workers, lote de {config_manager.config.batch_size}")
    
    # Cria processador assíncrono
    processor = AsyncPDFProcessor(config_manager)
    
    # Configurar callbacks de progresso
    def progress_callback(processed: int, total: int):
        percentage = (processed / total) * 100
        logger.info(f"Progresso: {processed}/{total} ({percentage:.1f}%)")
    
    def file_processed_callback(result):
        if result.success:
            logger.info(f"✅ {result.file_path.name} - {result.characters_extracted} caracteres")
        else:
            logger.warning(f"❌ {result.file_path.name} - {result.error_message}")
    
    processor.set_progress_callback(progress_callback)
    processor.set_file_processed_callback(file_processed_callback)
    
    # Determina se busca é recursiva
    recursive = args.recursive and not args.no_recursive
    
    try:
        # Descoberta de arquivos
        logger.info(f"Descobrindo arquivos PDF (recursivo: {recursive})...")
        pdf_files = await processor.discover_pdfs(args.directory, recursive)
        
        if not pdf_files:
            logger.warning("Nenhum arquivo PDF encontrado!")
            return
        
        logger.info(f"Encontrados {len(pdf_files)} arquivos PDF")
        
        # Se apenas descoberta, mostra arquivos e sai
        if args.discover_only:
            logger.info("Arquivos encontrados:")
            for pdf_file in pdf_files[:20]:  # Mostra apenas os primeiros 20
                logger.info(f"  - {pdf_file}")
            if len(pdf_files) > 20:
                logger.info(f"  ... e mais {len(pdf_files) - 20} arquivos")
            return
        
        # Processa arquivos
        logger.info(f"Iniciando processamento com extrator: {args.type}")
        results = await processor.process_files(pdf_files, args.type)
        
        # Estatísticas finais
        stats = processor.stats
        logger.info("=== Processamento Concluído ===")
        logger.info(f"Arquivos processados: {stats.processed_files}/{stats.total_files}")
        logger.info(f"Sucessos: {stats.successful_extractions}")
        logger.info(f"Falhas: {stats.failed_extractions}")
        logger.info(f"Taxa de sucesso: {stats.success_rate:.1%}")
        logger.info(f"Tempo total: {stats.total_processing_time:.1f}s")
        logger.info(f"Caracteres extraídos: {stats.total_characters_extracted:,}")
        logger.info(f"Velocidade: {stats.processing_speed:.0f} chars/s")
        
        # Gera relatório se solicitado
        if args.report:
            logger.info(f"Gerando relatório: {args.report}")
            report = processor.generate_report(results, args.report)
            logger.info("Relatório gerado com sucesso")
        
        # Performance logging
        perf_logger = PerformanceLogger()
        perf_logger.log_batch_performance(
            batch_size=len(pdf_files),
            total_time=stats.total_processing_time,
            successful_count=stats.successful_extractions,
            failed_count=stats.failed_extractions,
            total_characters=stats.total_characters_extracted
        )
        
        # Mostra arquivos com erro se houver
        failed_results = [r for r in results if not r.success]
        if failed_results:
            logger.warning(f"\n=== Arquivos com Erro ({len(failed_results)}) ===")
            for result in failed_results[:10]:  # Mostra apenas os primeiros 10
                logger.warning(f"❌ {result.file_path.name}: {result.error_message}")
            if len(failed_results) > 10:
                logger.warning(f"... e mais {len(failed_results) - 10} arquivos com erro")
        
    except KeyboardInterrupt:
        logger.info("\nProcessamento interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante processamento: {e}")
        sys.exit(1)


def setup_extractors():
    """Configura e registra todos os extratores disponíveis."""
    # Os extratores já são registrados automaticamente pelos decorators
    # Esta função apenas verifica se estão disponíveis
    
    available = ExtractorFactory.get_available_extractors()
    print(f"Extratores disponíveis: {', '.join(available)}")
    
    # Mostra informações dos extratores
    info = ExtractorFactory.get_extractor_info()
    for extractor_type, extractor_info in info.items():
        print(f"  {extractor_type}: {extractor_info.get('name', 'N/A')}")


if __name__ == "__main__":
    # Verifica se é chamada para mostrar extratores
    if len(sys.argv) > 1 and sys.argv[1] == '--list-extractors':
        setup_extractors()
        sys.exit(0)
    
    # Executa função principal
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)