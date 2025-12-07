# -*- coding: utf-8 -*-
"""
Script de verificação de configuração para OpenAI Vision
Verifica se todas as dependências estão instaladas e configuradas corretamente
"""
import os
import sys
import subprocess

def check_python_environment():
    """Verifica o ambiente Python"""
    print("🐍 VERIFICAÇÃO DO AMBIENTE PYTHON")
    print("=" * 50)
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()

def check_dependencies():
    """Verifica as dependências necessárias"""
    print("📦 VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("=" * 50)
    
    # Lista de dependências críticas
    dependencies = [
        'openai',
        'pdf2image', 
        'pillow',
        'asyncio'
    ]
    
    for dep in dependencies:
        try:
            if dep == 'asyncio':
                import asyncio
                print(f"✅ {dep}: Disponível (módulo padrão)")
            else:
                module = __import__(dep)
                if hasattr(module, '__version__'):
                    print(f"✅ {dep}: {module.__version__}")
                else:
                    print(f"✅ {dep}: Instalado")
        except ImportError:
            print(f"❌ {dep}: NÃO INSTALADO")
    print()

def check_poppler():
    """Verifica se o Poppler está configurado"""
    print("🔧 VERIFICAÇÃO DO POPPLER")
    print("=" * 50)
    
    poppler_path = "C:\\Users\\Maoki\\poppler\\poppler-23.11.0\\Library\\bin"
    
    if os.path.exists(poppler_path):
        print(f"✅ Poppler encontrado em: {poppler_path}")
        
        # Verifica se está no PATH
        current_path = os.environ.get('PATH', '')
        if poppler_path in current_path:
            print("✅ Poppler está no PATH")
        else:
            print("⚠️ Poppler NÃO está no PATH (será adicionado pelo script)")
        
        # Testa pdftoppm
        try:
            result = subprocess.run(
                [os.path.join(poppler_path, 'pdftoppm.exe'), '-h'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            print("✅ pdftoppm funcionando corretamente")
        except Exception as e:
            print(f"❌ Erro ao testar pdftoppm: {e}")
    else:
        print(f"❌ Poppler NÃO encontrado em: {poppler_path}")
    print()

def check_environment_variables():
    """Verifica as variáveis de ambiente"""
    print("🌍 VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE")
    print("=" * 50)
    
    env_vars = [
        'CURRENT_PROJECT',
        'PDF_BASE_PATH', 
        'RESULTS_BASE_PATH',
        'OPENAI_API_KEY'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if var == 'OPENAI_API_KEY':
                print(f"✅ {var}: {value[:20]}... (ocultado)")
            else:
                print(f"✅ {var}: {value}")
        else:
            if var == 'OPENAI_API_KEY':
                print(f"⚠️ {var}: Não definido (será usado padrão do script)")
            else:
                print(f"⚠️ {var}: Não definido (será usado padrão)")
    print()

def check_directories():
    """Verifica se os diretórios existem"""
    print("📁 VERIFICAÇÃO DE DIRETÓRIOS")
    print("=" * 50)
    
    current_project = os.environ.get('CURRENT_PROJECT', None)
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../../resultados')
    
    # Verifica pasta base de PDFs
    if os.path.exists(pdf_base_path):
        print(f"✅ Pasta base de PDFs: {pdf_base_path}")
        
        # Lista todas as pastas de projetos (exceto Processados)
        project_dirs = []
        for item in os.listdir(pdf_base_path):
            item_path = os.path.join(pdf_base_path, item)
            if os.path.isdir(item_path) and item.lower() != 'processados':
                pdf_files = [f for f in os.listdir(item_path) if f.endswith('.pdf')]
                if pdf_files:
                    project_dirs.append((item, len(pdf_files)))
        
        print(f"📂 Pastas de projetos encontradas: {len(project_dirs)}")
        for i, (project_dir, pdf_count) in enumerate(project_dirs[:5], 1):  # Mostra só os primeiros 5
            print(f"   {i}. {project_dir} ({pdf_count} PDFs)")
        
        if len(project_dirs) > 5:
            print(f"   ... e mais {len(project_dirs) - 5} pastas")
        
        # Se CURRENT_PROJECT está definido, verifica especificamente
        if current_project:
            project_path = f"{pdf_base_path}/{current_project}"
            if os.path.exists(project_path):
                pdf_files = [f for f in os.listdir(project_path) if f.endswith('.pdf')]
                print(f"✅ Projeto específico: {current_project} ({len(pdf_files)} PDFs)")
            else:
                print(f"❌ Projeto específico não encontrado: {current_project}")
    else:
        print(f"❌ Pasta base de PDFs não encontrada: {pdf_base_path}")
    
    # Verifica pasta de resultados (cria se não existir)
    if os.path.exists(results_base_path):
        print(f"✅ Pasta base de resultados: {results_base_path}")
    else:
        try:
            os.makedirs(results_base_path, exist_ok=True)
            print(f"✅ Pasta base de resultados criada: {results_base_path}")
        except Exception as e:
            print(f"❌ Erro ao criar pasta de resultados: {e}")
    
    # Verifica pasta de logs
    log_path = "logs"
    if os.path.exists(log_path):
        print(f"✅ Pasta de logs: {log_path}")
    else:
        try:
            os.makedirs(log_path, exist_ok=True)
            print(f"✅ Pasta de logs criada: {log_path}")
        except Exception as e:
            print(f"❌ Erro ao criar pasta de logs: {e}")
    
    # Verifica pasta Processados
    processados_path = f"{pdf_base_path}/Processados"
    if os.path.exists(processados_path):
        print(f"✅ Pasta Processados: {processados_path}")
    else:
        print(f"⚠️ Pasta Processados não existe (será criada quando necessário)")
    
    print()

def test_pdf_conversion():
    """Testa a conversão de PDF"""
    print("🧪 TESTE DE CONVERSÃO PDF")
    print("=" * 50)
    
    try:
        from pdf2image import convert_from_path
        print("✅ Módulo pdf2image importado com sucesso")
        
        # Procura um PDF para testar
        current_project = os.environ.get('CURRENT_PROJECT', None)
        pdf_base_path = os.environ.get('PDF_BASE_PATH', '../../pdfs')
        
        test_pdf = None
        
        # Se projeto específico foi definido
        if current_project and os.path.exists(f"{pdf_base_path}/{current_project}"):
            pdf_files = [f for f in os.listdir(f"{pdf_base_path}/{current_project}") if f.endswith('.pdf')]
            if pdf_files:
                test_pdf = os.path.join(f"{pdf_base_path}/{current_project}", pdf_files[0])
                print(f"📄 Testando conversão com: {current_project}/{pdf_files[0]}")
        
        # Senão, procura em qualquer pasta de projeto
        if not test_pdf and os.path.exists(pdf_base_path):
            for item in os.listdir(pdf_base_path):
                item_path = os.path.join(pdf_base_path, item)
                if os.path.isdir(item_path) and item.lower() != 'processados':
                    pdf_files = [f for f in os.listdir(item_path) if f.endswith('.pdf')]
                    if pdf_files:
                        test_pdf = os.path.join(item_path, pdf_files[0])
                        print(f"📄 Testando conversão com: {item}/{pdf_files[0]}")
                        break
        
        if test_pdf:
            # Tenta converter primeira página
            pages = convert_from_path(test_pdf, dpi=150, first_page=1, last_page=1)
            if pages:
                print(f"✅ Conversão bem-sucedida! Primeira página convertida")
                print(f"   Tamanho da imagem: {pages[0].size}")
            else:
                print("❌ Conversão falhou - nenhuma página retornada")
        else:
            print("⚠️ Nenhum PDF encontrado para teste")
            
    except Exception as e:
        print(f"❌ Erro no teste de conversão: {e}")
    print()

def main():
    """Executa todas as verificações"""
    print("🔍 DIAGNÓSTICO DE CONFIGURAÇÃO - OPENAI VISION")
    print("=" * 60)
    print()
    
    check_python_environment()
    check_dependencies()
    check_poppler()
    check_environment_variables()
    check_directories()
    test_pdf_conversion()
    
    print("🎯 DIAGNÓSTICO CONCLUÍDO!")
    print("=" * 60)
    print("Se todos os itens estão ✅, o sistema está pronto para executar.")
    print("Se há itens ❌ ou ⚠️, resolva-os antes de executar o script principal.")

if __name__ == "__main__":
    main()
