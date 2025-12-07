"""
EXECUTÁVEL SIMPLIFICADO - TOP 3 SCRIPTS DE EXTRAÇÃO
Sistema otimizado com apenas os 3 melhores scripts baseado na análise de qualidade:
1. PDFQuery (melhor para arquivos CP - 80% sucesso)
2. PyMuPDF (rápido e eficiente - 60% sucesso CP)
3. PDFPlumber (estruturas e tabelas - 60% sucesso CP)

Inclui todas as funcionalidades:
- Detecção de duplicatas
- Organização automática de pastas
- Configuração flexível
- Relatórios detalhados
"""
import os
import sys
import time
import glob
import subprocess
from datetime import datetime

# Configuração TOP 3 integrada (para evitar problemas de importação)
PDF_BASE_PATH = "../../pdfs"
RESULTS_BASE_PATH = "../../resultados"
PROJECT_PREFIX = "000."
PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"
RESULT_SUBDIRS = ['txt', 'csv', 'md', 'relatorios']

# Scripts TOP 3 otimizados (melhor qualidade para arquivos CP)
EXTRACTION_SCRIPTS = [
    ("../extracoes/extracao_pdfquery.py", "🥇 PDFQuery - MELHOR para arquivos CP (80% sucesso)"),
    ("../extracoes/extracao_pyMuPdf.py", "🥈 PyMuPDF - Rápido e eficiente (60% sucesso CP)"),
    ("../extracoes/extracao_pdfPlumber.py", "🥉 PDFPlumber - Estruturas e tabelas (60% sucesso CP)"),
]

# Padrões para detecção de arquivos existentes (evita duplicatas)
SCRIPT_OUTPUT_PATTERNS = {
    '../extracoes/extracao_pdfquery.py': ['pdfquery_*.txt', 'pdfquery_estruturado_*.txt'],
    '../extracoes/extracao_pyMuPdf.py': ['PyMuPDF_*.txt'],
    '../extracoes/extracao_pdfPlumber.py': ['pdfPlumber_*.txt'],
}

print("✅ Configurações TOP 3 integradas carregadas")

def discover_projects(pdf_base_path=None, project_prefix=None):
    """Descobre automaticamente todos os projetos na pasta especificada"""
    if pdf_base_path is None:
        pdf_base_path = PDF_BASE_PATH
    if project_prefix is None:
        project_prefix = PROJECT_PREFIX
        
    projects = []
    
    if os.path.exists(pdf_base_path):
        # Busca todas as pastas que contêm PDFs, não apenas com prefixo específico
        all_dirs = [d for d in os.listdir(pdf_base_path) 
                   if os.path.isdir(os.path.join(pdf_base_path, d))]
        
        for project_dir in sorted(all_dirs):
            project_path = os.path.join(pdf_base_path, project_dir)
            pdf_files = glob.glob(os.path.join(project_path, "*.pdf"))
            
            if pdf_files:
                # Verifica se segue o padrão ou se é uma pasta especial
                matches_prefix = project_dir.startswith(project_prefix)
                is_special_folder = project_dir in ['novos_arquivos', 'documentos', 'teste']
                
                if matches_prefix or is_special_folder:
                    projects.append({
                        'id': project_dir,
                        'path': project_path,
                        'pdfs': [os.path.basename(f) for f in pdf_files],
                        'pdf_count': len(pdf_files),
                        'base_path': pdf_base_path,
                        'type': 'padrão' if matches_prefix else 'especial'
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
    
    # Busca em todas as subpastas de arquivos individuais
    if os.path.exists(project_results_path):
        for item in os.listdir(project_results_path):
            item_path = os.path.join(project_results_path, item)
            if os.path.isdir(item_path):
                for pattern in patterns:
                    # Adapta o padrão para buscar dentro das pastas de arquivos
                    pattern_without_txt = pattern.replace('txt/', '')
                    full_pattern = os.path.join(item_path, pattern_without_txt)
                    found_files = glob.glob(full_pattern)
                    existing_files.extend(found_files)
    
    return len(existing_files) > 0, existing_files

def ensure_result_directories(project_id, pdf_files, results_base_path=None):
    """Garante que os diretórios de resultado existem para cada arquivo PDF do projeto"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
        
    base_path = os.path.join(results_base_path, project_id)
    
    # Cria uma pasta para cada arquivo PDF
    created_dirs = []
    for pdf_file in pdf_files:
        # Remove a extensão .pdf do nome
        pdf_name = os.path.splitext(pdf_file)[0]
        pdf_dir = os.path.join(base_path, pdf_name)
        os.makedirs(pdf_dir, exist_ok=True)
        created_dirs.append(pdf_name)
        
    print(f"📁 Pastas individuais criadas para {project_id}: {len(created_dirs)} arquivos")
    for pdf_dir in created_dirs[:3]:  # Mostra apenas os primeiros 3 para não poluir o log
        print(f"  📂 {pdf_dir}/")
    if len(created_dirs) > 3:
        print(f"  ... e mais {len(created_dirs) - 3} pastas")

def run_extraction_script(script_name, description, project_id, skip_existing=True, results_base_path=None):
    """Executa um script de extração individual para um projeto específico"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
    
    # Verifica se já existem arquivos para este script e projeto
    if skip_existing:
        has_existing, existing_files = check_existing_files(project_id, script_name, results_base_path)
        if has_existing:
            print(f"\n{'='*70}")
            print(f"⏭️ {description}")
            print(f"📄 Script: {os.path.basename(script_name)}")
            print(f"📁 Projeto: {project_id}")
            print(f"✅ Arquivos já existem ({len(existing_files)} encontrados) - PULANDO")
            print(f"💡 Para forçar re-execução, use modo 'Re-executar tudo'")
            return True
    
    print(f"\n{'='*70}")
    print(f"🚀 {description}")
    print(f"📄 Executando: {os.path.basename(script_name)}")
    print(f"📁 Projeto: {project_id}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        # Verifica se o script existe
        if not os.path.exists(script_name):
            print(f"❌ Script não encontrado: {script_name}")
            return False
            
        # Define variável de ambiente para o projeto atual
        env = os.environ.copy()
        env['CURRENT_PROJECT'] = project_id
        env['PDF_BASE_PATH'] = PDF_BASE_PATH
        env['RESULTS_BASE_PATH'] = results_base_path
        
        result = subprocess.run(
            [PYTHON_EXECUTABLE, script_name],
            env=env,
            capture_output=False,
            shell=False
        )
        
        exit_code = result.returncode
        
        if exit_code == 0:
            print(f"✅ {os.path.basename(script_name)} executado com sucesso para {project_id}!")
            return True
        else:
            print(f"⚠️ {os.path.basename(script_name)} terminou com código: {exit_code} para {project_id}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar {os.path.basename(script_name)} para {project_id}: {e}")
        return False
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️ Tempo decorrido: {elapsed:.2f}s")

def main():
    """Função principal - executa extrações com TOP 3 scripts otimizados"""
    print("🏆 EXECUTÁVEL SIMPLIFICADO - TOP 3 SCRIPTS OTIMIZADOS")
    print("="*70)
    print("📊 Scripts selecionados por qualidade em arquivos CP:")
    print("🥇 PDFQuery (80% sucesso CP) + 🥈 PyMuPDF (60% sucesso CP) + 🥉 PDFPlumber (60% sucesso CP)")
    print("="*70)
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
        project_type = project.get('type', 'padrão')
        type_icon = "📂" if project_type == 'padrão' else "📁"
        print(f"  {type_icon} {project['id']}: {project['pdf_count']} PDFs ({project_type})")
    
    # Scripts TOP 3 otimizados
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
        
        # Garante que os diretórios existem para cada arquivo PDF
        ensure_result_directories(project_id, project['pdfs'])
        
        # Executa cada script TOP 3 para este projeto
        for script_name, description in extraction_scripts:
            success = run_extraction_script(script_name, description, project_id, skip_existing)
            if success is True:
                successful += 1
            elif success is False:
                failed += 1
            else:
                skipped += 1
    
    # Relatório final
    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print("📋 RELATÓRIO FINAL - TOP 3 SCRIPTS")
    print(f"{'='*70}")
    print(f"📂 Projetos processados: {total_projects_processed}")
    print(f"✅ Scripts executados: {successful}")
    print(f"⏭️ Scripts pulados (já existem): {skipped}")
    print(f"❌ Scripts com erro/faltando: {failed}")
    print(f"⏱️ Tempo total: {total_elapsed:.2f}s")
    print(f"📅 Concluído em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Resumo da performance
    total_scripts = successful + failed + skipped
    if total_scripts > 0:
        success_rate = (successful / total_scripts) * 100
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
    
    print(f"\n📁 Estrutura de resultados (por arquivo individual):")
    for project in projects:
        project_id = project['id']
        results_path = os.path.abspath(os.path.join(RESULTS_BASE_PATH, project_id))
        print(f"  📂 {project_id}/")
        
        # Mostra algumas pastas de exemplo dos PDFs
        sample_pdfs = project['pdfs'][:2]  # Mostra apenas os primeiros 2 para não poluir o log
        for pdf_file in sample_pdfs:
            pdf_name = os.path.splitext(pdf_file)[0]
            print(f"    📁 {pdf_name}/")
            print(f"      � pdfquery_{pdf_name}.txt")
            print(f"      📝 pdfquery_estruturado_{pdf_name}.txt")
            print(f"      📝 PyMuPDF_{pdf_name}.txt")
            print(f"      � pdfPlumber_{pdf_name}.txt")
        
        if len(project['pdfs']) > 2:
            print(f"    ... e mais {len(project['pdfs']) - 2} pastas de arquivos")
    
    print("\n🎉 EXTRAÇÃO TOP 3 FINALIZADA!")
    print("💡 Scripts otimizados para máxima qualidade em arquivos CP")
    
    if skipped > 0:
        print("📝 Nota: Alguns scripts foram pulados porque os arquivos já existiam.")
        print("     Para forçar re-execução, escolha a opção '2' no início do script.")

if __name__ == "__main__":
    main()
