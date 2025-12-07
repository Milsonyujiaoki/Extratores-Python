"""
SCRIPT MESTRE - EXTRAÇÃO DE PDFs COM NOVA ESTRUTURA ORGANIZADA
Execute este script da pasta scripts/ para rodar todas as extrações
Detecta automaticamente todos os projetos e organiza resultados por projeto

CONFIGURAÇÃO:
- Modifique o arquivo config_extracoes.py para ajustar caminhos e configurações
- Suporte para diferentes estruturas de pasta e evita duplicatas
"""
import os
import sys
import time
import glob
import subprocess
from datetime import datetime

# Importa configurações do arquivo separado
try:
    from extracoes.scripts.config.config_extracoes import (
        PDF_BASE_PATH, RESULTS_BASE_PATH, PROJECT_PREFIX,
        EXTRACTION_SCRIPTS, SCRIPT_OUTPUT_PATTERNS, 
        PYTHON_EXECUTABLE, RESULT_SUBDIRS
    )
    print("✅ Configurações carregadas de config_extracoes.py")
except ImportError:
    print("⚠️ Arquivo config_extracoes.py não encontrado, usando configuração padrão")
    # Configuração padrão caso o arquivo não exista
    PDF_BASE_PATH = "../pdfs"
    RESULTS_BASE_PATH = "../resultados"
    PROJECT_PREFIX = "000."
    PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"
    RESULT_SUBDIRS = ['txt', 'csv', 'md', 'relatorios']
    
    EXTRACTION_SCRIPTS = [
        ("extracao_pyMuPdf.py", "🚀 PyMuPDF - Extração rápida e eficiente"),
        ("extracao_pdfPlumber.py", "📊 PDFPlumber - Estruturas e tabelas"),
        ("extracao_pdfMiner.py", "🔍 PDFMiner - Análise profunda"),
        ("extracao_pyPdf2.py", "📄 PyPDF2 - Biblioteca clássica"),
        ("extracao_pymupdf4llm.py", "🤖 PyMuPDF4LLM - Otimizado para IA"),
        ("extracao_pdfquery.py", "🔎 PDFQuery - Consultas estruturadas"),
        ("extracao_camelot_tabelas.py", "📈 Camelot - Extração e consolidação integrada"),
    ]
    
    SCRIPT_OUTPUT_PATTERNS = {
        'extracao_pyMuPdf.py': ['txt/PyMuPDF_*.txt'],
        'extracao_pdfPlumber.py': ['txt/pdfPlumber_*.txt'],
        'extracao_pdfMiner.py': ['txt/pdfMiner_*.txt'],
        'extracao_pyPdf2.py': ['txt/PyPDF2_*.txt'],
        'extracao_pymupdf4llm.py': ['txt/pymupdf4llm_*.txt', 'md/pymupdf4llm_*.md'],
        'extracao_pdfquery.py': ['txt/pdfquery_*.txt', 'txt/pdfquery_estruturado_*.txt'],
        'extracao_camelot_tabelas.py': ['csv/*_T*.csv', 'relatorios/camelot_consolidado_*.txt', 'relatorios/camelot_consolidado_*.xlsx'],
        'extracao_tabula.py': ['csv/tabula_*.csv'],
        'extracao_tika.py': ['txt/tika_*.txt']
    }

def discover_projects(pdf_base_path=None, project_prefix=None):
    """Descobre automaticamente todos os projetos na pasta especificada"""
    if pdf_base_path is None:
        pdf_base_path = PDF_BASE_PATH
    if project_prefix is None:
        project_prefix = PROJECT_PREFIX
        
    projects = []
    
    if os.path.exists(pdf_base_path):
        project_dirs = [d for d in os.listdir(pdf_base_path) 
                       if os.path.isdir(os.path.join(pdf_base_path, d)) 
                       and d.startswith(project_prefix)]
        
        for project_dir in sorted(project_dirs):
            project_path = os.path.join(pdf_base_path, project_dir)
            pdf_files = glob.glob(os.path.join(project_path, "*.pdf"))
            
            if pdf_files:
                projects.append({
                    'id': project_dir,
                    'path': project_path,
                    'pdfs': [os.path.basename(f) for f in pdf_files],
                    'pdf_count': len(pdf_files),
                    'base_path': pdf_base_path
                })
    else:
        print(f"⚠️ Pasta base não encontrada: {pdf_base_path}")
    
    return projects

def check_existing_files(project_id, script_name, results_base_path=None):
    """Verifica se já existem arquivos gerados para evitar duplicatas"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
        
    project_results_path = os.path.join(results_base_path, project_id)
    
    if script_name not in SCRIPT_OUTPUT_PATTERNS:
        return False, []
    
    existing_files = []
    patterns = SCRIPT_OUTPUT_PATTERNS[script_name]
    
    for pattern in patterns:
        full_pattern = os.path.join(project_results_path, pattern)
        found_files = glob.glob(full_pattern)
        existing_files.extend(found_files)
    
    return len(existing_files) > 0, existing_files

def ensure_result_directories(project_id, results_base_path=None):
    """Garante que os diretórios de resultado existem para um projeto"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
        
    base_path = os.path.join(results_base_path, project_id)
    
    for subdir in RESULT_SUBDIRS:
        dir_path = os.path.join(base_path, subdir)
        os.makedirs(dir_path, exist_ok=True)

def run_extraction_script(script_name, description, project_id, skip_existing=True, results_base_path=None):
    """Executa um script de extração individual para um projeto específico"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
    
    # Verifica se já existem arquivos para este script e projeto
    if skip_existing:
        has_existing, existing_files = check_existing_files(project_id, script_name, results_base_path)
        if has_existing:
            print(f"\n{'='*60}")
            print(f"⏭️ {description}")
            print(f"📄 Script: {script_name}")
            print(f"📁 Projeto: {project_id}")
            print(f"✅ Arquivos já existem ({len(existing_files)} encontrados) - PULANDO")
            print(f"💡 Para forçar re-execução, use skip_existing=False")
            return True
    
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"📄 Executando: {script_name}")
    print(f"📁 Projeto: {project_id}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Define variável de ambiente para o projeto atual
        env = os.environ.copy()
        env['CURRENT_PROJECT'] = project_id
        env['PDF_BASE_PATH'] = PDF_BASE_PATH
        env['RESULTS_BASE_PATH'] = results_base_path
        
        # Usar subprocess para melhor controle da execução
        python_path = PYTHON_EXECUTABLE
        
        result = subprocess.run(
            [python_path, script_name],
            env=env,
            capture_output=False,
            shell=False
        )
        
        exit_code = result.returncode
        
        if exit_code == 0:
            print(f"✅ {script_name} executado com sucesso para {project_id}!")
            return True
        else:
            print(f"⚠️ {script_name} terminou com código: {exit_code} para {project_id}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar {script_name} para {project_id}: {e}")
        return False
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️ Tempo decorrido: {elapsed:.2f}s")

def main():
    """Função principal - executa todas as extrações para todos os projetos"""
    print("🏁 INICIANDO EXTRAÇÃO COMPLETA DE PDFs")
    print("📁 Estrutura organizada ativa!")
    print(f"📍 Diretório atual: {os.getcwd()}")
    print(f"📂 Pasta PDFs: {os.path.abspath(PDF_BASE_PATH)}")
    print(f"📊 Pasta Resultados: {os.path.abspath(RESULTS_BASE_PATH)}")
    print(f"🏷️ Prefixo de projetos: '{PROJECT_PREFIX}*'")
    
    # Descobre automaticamente todos os projetos
    projects = discover_projects()
    
    if not projects:
        print(f"❌ Nenhum projeto encontrado na pasta {PDF_BASE_PATH}/")
        print(f"💡 Verifique se existem pastas com prefixo '{PROJECT_PREFIX}' contendo PDFs")
        return
    
    print(f"\n🔍 Projetos descobertos: {len(projects)}")
    for project in projects:
        print(f"  📂 {project['id']}: {project['pdf_count']} PDFs")
    
    # Lista de scripts para executar (carregada da configuração)
    extraction_scripts = EXTRACTION_SCRIPTS
    
    total_start = time.time()
    successful = 0
    failed = 0
    skipped = 0
    total_projects_processed = 0
    
    # Opções de execução
    print(f"\n🔧 OPÇÕES DE EXECUÇÃO:")
    print("1. Pular arquivos já existentes (recomendado)")
    print("2. Re-executar tudo (força recriação)")
    print("Digite 1 ou 2 (padrão: 1): ", end="")
    
    try:
        skip_option = input().strip()
        skip_existing = skip_option != '2'
    except (EOFError, KeyboardInterrupt):
        skip_existing = True
    
    if skip_existing:
        print("✅ Modo: Pular arquivos existentes")
    else:
        print("🔄 Modo: Re-executar tudo")
    
    # Pergunta se o usuário quer processar todos os projetos ou escolher
    print(f"\n❓ Deseja processar todos os {len(projects)} projetos? (s/n): ", end="")
    try:
        response = input().lower().strip()
        if response not in ['s', 'sim', 'y', 'yes', '']:
            print("📋 Projetos disponíveis:")
            for i, project in enumerate(projects, 1):
                print(f"  {i}. {project['id']}")
            
            print("Digite os números dos projetos (separados por vírgula) ou 'all' para todos: ", end="")
            selection = input().strip()
            
            if selection.lower() != 'all':
                try:
                    selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    projects = [projects[i] for i in selected_indices if 0 <= i < len(projects)]
                except ValueError:
                    print("❌ Seleção inválida. Processando todos os projetos.")
    except (EOFError, KeyboardInterrupt):
        # Se executado automaticamente, processa todos
        pass
    
    # Executa para cada projeto
    for project in projects:
        project_id = project['id']
        total_projects_processed += 1
        
        print(f"\n🎯 PROCESSANDO PROJETO: {project_id}")
        print(f"📄 PDFs: {', '.join(project['pdfs'])}")
        print(f"📂 Pasta origem: {project['path']}")
        
        # Garante que os diretórios existem
        ensure_result_directories(project_id)
        
        # Executa cada script para este projeto
        for script_name, description in extraction_scripts:
            if os.path.exists(script_name):
                success = run_extraction_script(script_name, description, project_id, skip_existing)
                if success is True:
                    successful += 1
                elif success is False:
                    failed += 1
                else:
                    skipped += 1
            else:
                print(f"⚠️ Script não encontrado: {script_name}")
                failed += 1
    
    # Relatório final
    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print("📋 RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"📂 Projetos processados: {total_projects_processed}")
    print(f"✅ Scripts executados: {successful}")
    print(f"⏭️ Scripts pulados (já existem): {skipped}")
    print(f"❌ Scripts com erro/faltando: {failed}")
    print(f"⏱️ Tempo total: {total_elapsed:.2f}s")
    print(f"📅 Concluído em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    print(f"\n📁 Estrutura de resultados:")
    for project in projects:
        project_id = project['id']
        results_path = os.path.abspath(os.path.join(RESULTS_BASE_PATH, project_id))
        print(f"  📂 {project_id}/")
        print(f"    📊 Tabelas: {results_path}/csv/")
        print(f"    📝 Textos: {results_path}/txt/")
        print(f"    🤖 Markdown: {results_path}/md/")
        print(f"    📋 Relatórios: {results_path}/relatorios/")
    
    print("\n🎉 EXTRAÇÃO COMPLETA FINALIZADA!")
    print("💡 Dica: As tabelas Camelot já foram automaticamente consolidadas durante a extração")
    
    if skipped > 0:
        print("📝 Nota: Alguns scripts foram pulados porque os arquivos já existiam.")
        print("     Para forçar re-execução, escolha a opção '2' no início do script.")

if __name__ == "__main__":
    main()
