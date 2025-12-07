#!/usr/bin/env python3
"""
Script de teste rápido para validar a nova arquitetura.
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Testa se todas as importações funcionam."""
    try:
        print("🔍 Testando importações...")
        
        # Core
        from src.core.base_extractor import BaseExtractor, ExtractionResult
        print("✅ BaseExtractor importado")
        
        from src.core.config_manager import ConfigManager, ExtractionConfig
        print("✅ ConfigManager importado")
        
        from src.core.extractor_factory import ExtractorFactory
        print("✅ ExtractorFactory importado")
        
        # Extractors
        from src.extractors.direct_extractor import DirectExtractor
        print("✅ DirectExtractor importado")
        
        from src.extractors.ocr_extractor import OCRExtractor
        print("✅ OCRExtractor importado")
        
        from src.extractors.hybrid_extractor import HybridExtractor
        print("✅ HybridExtractor importado")
        
        # Processors
        from src.processors.async_processor import AsyncPDFProcessor
        print("✅ AsyncPDFProcessor importado")
        
        # Utils
        from src.utils.logging_utils import LoggerSetup, PerformanceLogger
        print("✅ Logging utils importados")
        
        print("\n🎉 Todas as importações funcionaram!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def test_factory():
    """Testa o factory de extratores."""
    try:
        print("\n🏭 Testando ExtractorFactory...")
        
        from src.core.extractor_factory import ExtractorFactory
        
        # Listar extratores disponíveis
        available = ExtractorFactory.get_available_extractors()
        print(f"📋 Extratores disponíveis: {available}")
        
        # Testar criação de extratores
        for extractor_type in available:
            extractor = ExtractorFactory.create_extractor(extractor_type)
            print(f"✅ {extractor_type}: {extractor.__class__.__name__}")
        
        # Testar seleção automática (precisa de um arquivo de exemplo)
        test_pdf = Path("test.pdf")  # Arquivo fictício para teste
        if test_pdf.exists():
            auto_extractor = ExtractorFactory.auto_select_extractor(test_pdf)
            print(f"🤖 Seleção automática: {auto_extractor.__class__.__name__}")
        else:
            print("🤖 Seleção automática: Pulado (sem arquivo de teste)")
        
        print("\n🎉 Factory funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no factory: {e}")
        return False


def test_config():
    """Testa o gerenciador de configuração."""
    try:
        print("\n⚙️ Testando ConfigManager...")
        
        from src.core.config_manager import ConfigManager
        
        # Configuração padrão
        config = ConfigManager()
        print(f"📁 Diretório de saída padrão: {config.config.output_directory}")
        print(f"👥 Workers padrão: {config.config.max_workers}")
        print(f"📦 Tamanho do lote: {config.config.batch_size}")
        
        # Validação
        errors = config.validate_config()
        if errors:
            print(f"⚠️ Avisos de configuração: {errors}")
        else:
            print("✅ Configuração válida")
        
        print("\n🎉 ConfigManager funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False


def test_logging():
    """Testa o sistema de logging."""
    try:
        print("\n📝 Testando sistema de logging...")
        
        from src.utils.logging_utils import LoggerSetup, PerformanceLogger
        
        # Setup básico
        logger = LoggerSetup.setup_logging(log_level='INFO')
        
        # Testes de log
        logger.debug("🐛 Teste DEBUG")
        logger.info("ℹ️ Teste INFO")
        logger.warning("⚠️ Teste WARNING")
        logger.error("❌ Teste ERROR")
        
        # Performance logger
        perf_logger = PerformanceLogger()
        
        # Teste das métricas de performance
        perf_logger.log_batch_performance(
            batch_size=10,
            total_time=5.0,
            successful_count=8,
            failed_count=2,
            total_characters=50000
        )
        
        print("🔧 Performance logger testado com métricas de lote")
        
        print("✅ Sistema de logging funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no logging: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("🧪 TESTE DA NOVA ARQUITETURA")
    print("=" * 40)
    
    tests = [
        ("Importações", test_imports),
        ("Factory Pattern", test_factory),
        ("Configuração", test_config),
        ("Sistema de Logging", test_logging)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Falha no teste: {test_name}")
        except Exception as e:
            print(f"💥 Erro crítico em {test_name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! A arquitetura está funcionando.")
        print("\n🚀 Próximos passos:")
        print("   1. Execute: python example_usage.py")
        print("   2. Ou use: python pdf_extractor_advanced.py -d ./pdfs")
        print("   3. Coloque alguns PDFs na pasta 'pdfs' para testar")
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)