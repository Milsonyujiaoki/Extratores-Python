"""
EXECUTÁVEL COMPLETO - TOP 3 + OCR INTELIGENTE
Sistema híbrido que combina os melhores métodos tradicionais com OCR avançado
Automaticamente detecta quando OCR é necessário e aplica as melhores tecnologias
"""
import os
import sys
import time
import glob
import subprocess
from datetime import datetime

# Configuração completa integrada (TOP 3 + OCR)
PDF_BASE_PATH = "../../pdfs"
RESULTS_BASE_PATH = "../../resultados"
PROJECT_PREFIX = "000."
PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"
RESULT_SUBDIRS = ['txt', 'csv', 'md', 'relatorios']

# Scripts TOP 3 otimizados
EXTRACTION_SCRIPTS_TOP3 = [
    ("../extracoes/extracao_pdfquery.py", "🥇 PDFQuery - MELHOR para arquivos CP (80% sucesso)"),
    ("../extracoes/extracao_pyMuPdf.py", "🥈 PyMuPDF - Rápido e eficiente (60% sucesso CP)"),
    ("../extracoes/extracao_pdfPlumber.py", "🥉 PDFPlumber - Estruturas e tabelas (60% sucesso CP)"),
]

# Scripts OCR para fallback automático
EXTRACTION_SCRIPTS_OCR = [
    ("../extracoes/extracao_tesseract_ocr.py", "🔍 Tesseract OCR - Para PDFs escaneados"),
    ("../extracoes/extracao_openai_vision.py", "🤖 OpenAI Vision - IA avançada para texto complexo"),
    ("../extracoes/extracao_hibrida_ocr.py", "🧠 Pipeline Híbrido - Automático com fallback"),
]

# Configuração completa com OCR
EXTRACTION_SCRIPTS_COMPLETE = EXTRACTION_SCRIPTS_TOP3 + EXTRACTION_SCRIPTS_OCR

# Padrões para detecção de arquivos existentes
SCRIPT_OUTPUT_PATTERNS_TOP3 = {
    '../extracoes/extracao_pdfquery.py': ['pdfquery_*.txt', 'pdfquery_estruturado_*.txt'],
    '../extracoes/extracao_pyMuPdf.py': ['PyMuPDF_*.txt'],
    '../extracoes/extracao_pdfPlumber.py': ['pdfPlumber_*.txt'],
}

# Padrões para scripts OCR
SCRIPT_OUTPUT_PATTERNS_OCR = {
    '../extracoes/extracao_tesseract_ocr.py': ['tesseract_ocr_*.txt', 'tesseract_enhanced_*.txt'],
    '../extracoes/extracao_openai_vision.py': ['openai_vision_*.txt', 'openai_structured_*.txt'],
    '../extracoes/extracao_hibrida_ocr.py': ['extraction_report_*.txt'],
}

# Padrões completos
SCRIPT_OUTPUT_PATTERNS_COMPLETE = {**SCRIPT_OUTPUT_PATTERNS_TOP3, **SCRIPT_OUTPUT_PATTERNS_OCR}

print("✅ Configurações completas integradas carregadas (TOP 3 + OCR)")

def discover_projects(pdf_base_path=None, project_prefix=None):
    """Descobre automaticamente todos os projetos na pasta especificada"""
    if pdf_base_path is None:
        pdf_base_path = PDF_BASE_PATH
    if project_prefix is None:
        project_prefix = PROJECT_PREFIX
        
    projects = []
    
    if os.path.exists(pdf_base_path):
        all_dirs = [d for d in os.listdir(pdf_base_path) 
                   if os.path.isdir(os.path.join(pdf_base_path, d))]
        
        for project_dir in sorted(all_dirs):
            project_path = os.path.join(pdf_base_path, project_dir)
            pdf_files = glob.glob(os.path.join(project_path, "*.pdf"))
            
            if pdf_files:
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

def check_existing_files(project_id, script_name, patterns_dict, results_base_path=None):
    """Verifica se já existem arquivos gerados para evitar duplicatas"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
        
    project_results_path = os.path.join(results_base_path, project_id)
    
    if script_name not in patterns_dict:
        return False, []
    
    existing_files = []
    patterns = patterns_dict[script_name]
    
    if os.path.exists(project_results_path):
        for item in os.listdir(project_results_path):
            item_path = os.path.join(project_results_path, item)
            if os.path.isdir(item_path):
                for pattern in patterns:
                    full_pattern = os.path.join(item_path, pattern)
                    found_files = glob.glob(full_pattern)
                    existing_files.extend(found_files)
    
    return len(existing_files) > 0, existing_files

def ensure_result_directories(project_id, pdf_files, results_base_path=None):
    """Garante que os diretórios de resultado existem para cada arquivo PDF"""
    if results_base_path is None:
        results_base_path = RESULTS_BASE_PATH
        
    base_path = os.path.join(results_base_path, project_id)
    
    created_dirs = []
    for pdf_file in pdf_files:
        pdf_name = os.path.splitext(pdf_file)[0]
        pdf_dir = os.path.join(base_path, pdf_name)
        os.makedirs(pdf_dir, exist_ok=True)
        created_dirs.append(pdf_name)
        
    print(f"📁 Pastas individuais criadas para {project_id}: {len(created_dirs)} arquivos")
    for pdf_dir in created_dirs[:3]:
        print(f"  📂 {pdf_dir}/")
    if len(created_dirs) > 3:
        print(f"  ... e mais {len(created_dirs) - 3} pastas")

def run_extraction_script(script_name, description, project_id, patterns_dict, skip_existing=True):
    """Executa um script de extração individual"""
    if skip_existing:
        has_existing, existing_files = check_existing_files(project_id, script_name, patterns_dict)
        if has_existing:
            print(f"\n{'='*70}")
            print(f"⏭️ {description}")
            print(f"📄 Script: {os.path.basename(script_name)}")
            print(f"📁 Projeto: {project_id}")
            print(f"✅ Arquivos já existem ({len(existing_files)} encontrados) - PULANDO")
            return True
    
    print(f"\n{'='*70}")
    print(f"🚀 {description}")
    print(f"📄 Executando: {os.path.basename(script_name)}")
    print(f"📁 Projeto: {project_id}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        if not os.path.exists(script_name):
            print(f"❌ Script não encontrado: {script_name}")
            return False
            
        env = os.environ.copy()
        env['CURRENT_PROJECT'] = project_id
        env['PDF_BASE_PATH'] = PDF_BASE_PATH
        env['RESULTS_BASE_PATH'] = RESULTS_BASE_PATH
        env['PYTHON_EXECUTABLE'] = PYTHON_EXECUTABLE
        
        result = subprocess.run(
            [PYTHON_EXECUTABLE, script_name],
            env=env,
            capture_output=False,
            shell=False,
            timeout=600  # 10 minutos timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {os.path.basename(script_name)} executado com sucesso!")
            return True
        else:
            print(f"⚠️ {os.path.basename(script_name)} terminou com código: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout após 10 minutos")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar {os.path.basename(script_name)}: {e}")
        return False
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️ Tempo decorrido: {elapsed:.2f}s")

def main():
    """Função principal com opções de execução flexíveis"""
    print("🚀 EXECUTÁVEL COMPLETO - TOP 3 + OCR INTELIGENTE")
    print("="*70)
    print("🎯 Modos disponíveis:")
    print("1. TOP 3 apenas (PDFQuery + PyMuPDF + PDFPlumber)")
    print("2. OCR apenas (Tesseract + OpenAI Vision)")
    print("3. Pipeline Híbrido (TOP 3 + OCR automático)")
    print("4. Tudo (TOP 3 + OCR + Pipeline)")
    print("="*70)
    
    projects = discover_projects()
    
    if not projects:
        print(f"❌ Nenhum projeto encontrado na pasta {PDF_BASE_PATH}/")
        return
    
    print(f"\n🔍 Projetos descobertos: {len(projects)}")
    for project in projects:
        project_type = project.get('type', 'padrão')
        type_icon = "📂" if project_type == 'padrão' else "📁"
        print(f"  {type_icon} {project['id']}: {project['pdf_count']} PDFs ({project_type})")
    
    # Seleção do modo
    print(f"\n🔧 Escolha o modo de execução (1-4): ", end="")
    try:
        mode = input().strip()
        if mode not in ['1', '2', '3', '4']:
            mode = '1'
    except (EOFError, KeyboardInterrupt):
        mode = '1'
    
    # Define scripts baseado no modo
    if mode == '1':
        extraction_scripts = EXTRACTION_SCRIPTS_TOP3
        patterns_dict = SCRIPT_OUTPUT_PATTERNS_TOP3
        mode_name = "TOP 3 TRADICIONAL"
    elif mode == '2':
        extraction_scripts = EXTRACTION_SCRIPTS_OCR
        patterns_dict = SCRIPT_OUTPUT_PATTERNS_OCR
        mode_name = "OCR ESPECIALIZADO"
    elif mode == '3':
        # Pipeline híbrido usa apenas o script inteligente
        extraction_scripts = [("../extracoes/extracao_hibrida_ocr.py", 
                              "🧠 Pipeline Híbrido - TOP 3 + OCR automático")]
        patterns_dict = SCRIPT_OUTPUT_PATTERNS_OCR
        mode_name = "PIPELINE HÍBRIDO"
    else:  # mode == '4'
        extraction_scripts = EXTRACTION_SCRIPTS_COMPLETE
        patterns_dict = SCRIPT_OUTPUT_PATTERNS_COMPLETE
        mode_name = "COMPLETO"
    
    print(f"✅ Modo selecionado: {mode_name}")
    
    # Opção de pular existentes
    print(f"\n🔧 Pular arquivos já existentes? (s/n): ", end="")
    try:
        skip_option = input().strip().lower()
        skip_existing = skip_option in ['s', 'sim', 'y', 'yes', '']
    except (EOFError, KeyboardInterrupt):
        skip_existing = True
    
    # Seleção de projetos
    print(f"\n❓ Processar todos os {len(projects)} projetos? (s/n): ", end="")
    try:
        response = input().lower().strip()
        if response not in ['s', 'sim', 'y', 'yes', '']:
            print("📋 Projetos disponíveis:")
            for i, project in enumerate(projects, 1):
                print(f"  {i}. {project['id']}")
            
            print("Digite os números (separados por vírgula) ou 'all': ", end="")
            selection = input().strip()
            
            if selection.lower() != 'all':
                try:
                    selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    projects = [projects[i] for i in selected_indices if 0 <= i < len(projects)]
                except ValueError:
                    print("❌ Seleção inválida. Processando todos.")
    except (EOFError, KeyboardInterrupt):
        pass
    
    # Execução
    total_start = time.time()
    successful = 0
    failed = 0
    skipped = 0
    
    for project in projects:
        project_id = project['id']
        
        print(f"\n🎯 PROCESSANDO PROJETO: {project_id}")
        print(f"📄 PDFs: {', '.join(project['pdfs'])}")
        
        ensure_result_directories(project_id, project['pdfs'])
        
        for script_name, description in extraction_scripts:
            success = run_extraction_script(script_name, description, project_id, 
                                          patterns_dict, skip_existing)
            if success is True:
                successful += 1
            elif success is False:
                failed += 1
            else:
                skipped += 1
    
    # Relatório final
    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"📋 RELATÓRIO FINAL - {mode_name}")
    print(f"{'='*70}")
    print(f"📂 Projetos processados: {len(projects)}")
    print(f"✅ Scripts executados: {successful}")
    print(f"⏭️ Scripts pulados: {skipped}")
    print(f"❌ Scripts com erro: {failed}")
    print(f"⏱️ Tempo total: {total_elapsed:.2f}s")
    print(f"📅 Concluído em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    total_scripts = successful + failed + skipped
    if total_scripts > 0:
        success_rate = (successful / total_scripts) * 100
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
    
    print(f"\n🎉 EXTRAÇÃO FINALIZADA!")
    
    if mode == '3':
        print("💡 O Pipeline Híbrido automaticamente aplicou OCR onde necessário")
    elif mode == '4':
        print("💡 Extração completa com todos os métodos disponíveis")

if __name__ == "__main__":
    main()
