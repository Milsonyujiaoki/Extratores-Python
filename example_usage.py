#!/usr/bin/env python3
"""
Script de exemplo para demonstrar o uso da nova arquitetura de extração de PDFs.
Este script implementa todas as melhorias solicitadas:
- Percorre pastas e subpastas recursivamente
- Executa em paralelo e assincronamente
- Usa arquitetura modular escalável
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config_manager import ConfigManager
from src.processors.async_processor import AsyncPDFProcessor
from src.utils.logging_utils import LoggerSetup


async def example_directory_processing():
    """
    Exemplo de processamento recursivo de diretório com execução paralela e assíncrona.
    """
    
    # Configura logging com cores
    logger = LoggerSetup.setup_logging(log_level='INFO')
    
    logger.info("🚀 Iniciando exemplo de processamento avançado de PDFs")
    
    # Configuração personalizada
    config = ConfigManager()
    config.config.max_workers = 4  # Processamento paralelo com 4 workers
    config.config.batch_size = 10  # Processa em lotes de 10 arquivos
    config.config.output_format = 'json'  # Saída em JSON
    config.config.output_directory = './output_example'
    
    logger.info(f"⚙️  Configuração: {config.config.max_workers} workers, lotes de {config.config.batch_size}")
    
    # Cria o processador assíncrono
    processor = AsyncPDFProcessor(config)
    
    # Define callbacks para acompanhar o progresso
    def on_progress(processed: int, total: int):
        percentage = (processed / total) * 100
        logger.info(f"📊 Progresso: {processed}/{total} ({percentage:.1f}%)")
    
    def on_file_processed(result):
        if result.success:
            chars = result.characters_extracted
            time_taken = result.processing_time
            logger.info(f"✅ {result.file_path.name} - {chars:,} caracteres em {time_taken:.2f}s")
        else:
            logger.warning(f"❌ {result.file_path.name} - Erro: {result.error_message}")
    
    processor.set_progress_callback(on_progress)
    processor.set_file_processed_callback(on_file_processed)
    
    # Diretório de teste (você pode modificar este caminho)
    test_directory = Path.cwd() / "pdfs"  # Pasta 'pdfs' no diretório atual
    
    if not test_directory.exists():
        logger.warning(f"⚠️  Diretório {test_directory} não encontrado")
        logger.info("📁 Criando diretório de exemplo...")
        test_directory.mkdir(exist_ok=True)
        logger.info("ℹ️  Coloque alguns arquivos PDF na pasta 'pdfs' e execute novamente")
        return
    
    try:
        # 1. DESCOBERTA RECURSIVA
        logger.info(f"🔍 Descobrindo PDFs recursivamente em: {test_directory}")
        pdf_files = await processor.discover_pdfs(test_directory, recursive=True)
        
        if not pdf_files:
            logger.warning("⚠️  Nenhum arquivo PDF encontrado!")
            logger.info("💡 Dica: Coloque arquivos PDF na pasta 'pdfs' para testar")
            return
        
        logger.info(f"📋 Encontrados {len(pdf_files)} arquivos PDF")
        
        # Mostra alguns arquivos encontrados
        for i, pdf_file in enumerate(pdf_files[:5]):
            logger.info(f"   {i+1}. {pdf_file}")
        if len(pdf_files) > 5:
            logger.info(f"   ... e mais {len(pdf_files) - 5} arquivos")
        
        # 2. PROCESSAMENTO PARALELO E ASSÍNCRONO
        logger.info("🚀 Iniciando processamento paralelo...")
        results = await processor.process_files(pdf_files, extractor_type='hybrid')
        
        # 3. ESTATÍSTICAS FINAIS
        stats = processor.stats
        logger.info("\n" + "="*50)
        logger.info("📈 RELATÓRIO FINAL")
        logger.info("="*50)
        logger.info(f"📁 Arquivos processados: {stats.processed_files}/{stats.total_files}")
        logger.info(f"✅ Sucessos: {stats.successful_extractions}")
        logger.info(f"❌ Falhas: {stats.failed_extractions}")
        logger.info(f"📊 Taxa de sucesso: {stats.success_rate:.1%}")
        logger.info(f"⏱️  Tempo total: {stats.total_processing_time:.1f}s")
        logger.info(f"📝 Caracteres extraídos: {stats.total_characters_extracted:,}")
        logger.info(f"⚡ Velocidade: {stats.processing_speed:.0f} chars/s")
        
        # 4. ARQUIVOS DE SAÍDA
        output_dir = Path(config.config.output_directory)
        if output_dir.exists():
            output_files = list(output_dir.glob("*.json"))
            logger.info(f"\n📄 Arquivos de saída criados: {len(output_files)}")
            for output_file in output_files[:3]:
                logger.info(f"   📄 {output_file}")
        
        # 5. DEMONSTRAÇÃO DE RECURSOS AVANÇADOS
        logger.info("\n🔧 RECURSOS IMPLEMENTADOS:")
        logger.info("   ✅ Descoberta recursiva de arquivos")
        logger.info("   ✅ Processamento paralelo com workers")
        logger.info("   ✅ Execução assíncrona (async/await)")
        logger.info("   ✅ Arquitetura modular escalável")
        logger.info("   ✅ Factory pattern para extratores")
        logger.info("   ✅ Configuração flexível (JSON/YAML/INI)")
        logger.info("   ✅ Logging avançado com cores")
        logger.info("   ✅ Métricas de performance")
        logger.info("   ✅ Callbacks de progresso")
        logger.info("   ✅ Tratamento robusto de erros")
        
    except Exception as e:
        logger.error(f"💥 Erro durante processamento: {e}")
        raise


async def example_specific_file():
    """Exemplo de processamento de um arquivo específico."""
    
    logger = LoggerSetup.setup_logging(log_level='INFO')
    
    # Procura por qualquer PDF no diretório atual
    current_dir = Path.cwd()
    pdf_files = list(current_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.info("📁 Nenhum PDF encontrado no diretório atual")
        return
    
    pdf_file = pdf_files[0]
    logger.info(f"🔍 Testando com arquivo: {pdf_file.name}")
    
    # Processamento simples
    config = ConfigManager()
    processor = AsyncPDFProcessor(config)
    
    results = await processor.process_files([pdf_file], extractor_type='hybrid')
    
    if results and results[0].success:
        result = results[0]
        logger.info(f"✅ Sucesso: {result.characters_extracted:,} caracteres extraídos")
        logger.info(f"⏱️  Tempo: {result.processing_time:.2f}s")
    else:
        logger.warning(f"❌ Falha na extração")


def main():
    """Função principal com menu de exemplos."""
    
    print("🔧 Extrator Avançado de PDFs - Exemplos")
    print("=" * 40)
    print("1. Processamento recursivo completo")
    print("2. Teste com arquivo único")
    print("3. Sair")
    
    choice = input("\nEscolha uma opção (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Executando processamento recursivo...")
        asyncio.run(example_directory_processing())
    elif choice == "2":
        print("\n🔍 Testando arquivo único...")
        asyncio.run(example_specific_file())
    elif choice == "3":
        print("👋 Até logo!")
    else:
        print("❌ Opção inválida!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro: {e}")