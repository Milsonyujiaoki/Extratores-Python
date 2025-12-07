# -*- coding: utf-8 -*-
"""
Sistema Inteligente de Fallback - Extração Híbrida com OCR
Primeiro tenta métodos tradicionais, depois aplica OCR automaticamente se necessário
"""
import os
import sys
import glob
import subprocess
import time
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def count_meaningful_text(file_path):
    """Conta caracteres significativos em um arquivo de texto"""
    if not os.path.exists(file_path):
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove espaços, quebras de linha e caracteres especiais
        meaningful_chars = ''.join(c for c in content if c.isalnum())
        return len(meaningful_chars)
    except:
        return 0

def analyze_extraction_quality(pdf_dir, filename):
    """Analisa a qualidade das extrações tradicionais"""
    results = {
        'pdfquery': 0,
        'pymupdf': 0,
        'pdfplumber': 0,
        'total': 0,
        'needs_ocr': False
    }
    
    # Verifica arquivos de extração tradicional
    files_to_check = [
        f"pdfquery_{filename}.txt",
        f"PyMuPDF_{filename}.txt", 
        f"pdfPlumber_{filename}.txt"
    ]
    
    for file_name in files_to_check:
        file_path = os.path.join(pdf_dir, file_name)
        char_count = count_meaningful_text(file_path)
        
        if 'pdfquery' in file_name:
            results['pdfquery'] = char_count
        elif 'PyMuPDF' in file_name:
            results['pymupdf'] = char_count
        elif 'pdfPlumber' in file_name:
            results['pdfplumber'] = char_count
        
        results['total'] += char_count
    
    # Critérios para determinar se precisa OCR
    # Considera que precisa de OCR se:
    # 1. Total de caracteres < 100 (muito pouco texto)
    # 2. Todos os métodos falharam (0 caracteres cada)
    # 3. Diferença muito grande entre métodos (inconsistência)
    
    min_chars_threshold = 100
    
    if results['total'] < min_chars_threshold:
        results['needs_ocr'] = True
    elif results['pdfquery'] == 0 and results['pymupdf'] == 0 and results['pdfplumber'] == 0:
        results['needs_ocr'] = True
    
    return results

def run_ocr_extraction(pdf_file, pdf_dir, filename, ocr_method='tesseract'):
    """Executa extração OCR"""
    current_project = os.environ.get('CURRENT_PROJECT', 'unknown')
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../resultados')
    python_executable = os.environ.get('PYTHON_EXECUTABLE', 'python')
    
    if ocr_method == 'tesseract':
        script_path = '../extracoes/extracao_tesseract_ocr.py'
        print(f"🔍 Aplicando Tesseract OCR em {filename}...")
    elif ocr_method == 'openai':
        script_path = '../extracoes/extracao_openai_vision.py'
        print(f"🤖 Aplicando OpenAI Vision em {filename}...")
    else:
        print(f"❌ Método OCR desconhecido: {ocr_method}")
        return False
    
    try:
        # Configura ambiente para o script OCR
        env = os.environ.copy()
        env['CURRENT_PROJECT'] = current_project
        env['PDF_BASE_PATH'] = pdf_base_path
        env['RESULTS_BASE_PATH'] = results_base_path
        
        # Executa script OCR
        result = subprocess.run(
            [python_executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            print(f"✅ OCR {ocr_method} executado com sucesso!")
            return True
        else:
            print(f"⚠️ OCR {ocr_method} terminou com código: {result.returncode}")
            print(f"Erro: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout no OCR {ocr_method} após 5 minutos")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar OCR {ocr_method}: {e}")
        return False

def create_extraction_report(pdf_dir, filename):
    """Cria relatório detalhado das extrações"""
    report_path = os.path.join(pdf_dir, f"extraction_report_{filename}.txt")
    
    analysis = analyze_extraction_quality(pdf_dir, filename)
    
    report_lines = []
    report_lines.append("=== RELATÓRIO DE EXTRAÇÃO ===\n")
    report_lines.append(f"Arquivo: {filename}\n")
    report_lines.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    report_lines.append("="*40 + "\n\n")
    
    report_lines.append("📊 ANÁLISE DE QUALIDADE:\n")
    report_lines.append(f"PDFQuery: {analysis['pdfquery']} caracteres\n")
    report_lines.append(f"PyMuPDF: {analysis['pymupdf']} caracteres\n")
    report_lines.append(f"PDFPlumber: {analysis['pdfplumber']} caracteres\n")
    report_lines.append(f"Total: {analysis['total']} caracteres\n")
    report_lines.append(f"Necessita OCR: {'SIM' if analysis['needs_ocr'] else 'NÃO'}\n\n")
    
    # Lista arquivos disponíveis
    report_lines.append("📁 ARQUIVOS GERADOS:\n")
    if os.path.exists(pdf_dir):
        for file in sorted(os.listdir(pdf_dir)):
            if file.endswith('.txt') and file != f"extraction_report_{filename}.txt":
                file_path = os.path.join(pdf_dir, file)
                size = count_meaningful_text(file_path)
                report_lines.append(f"  📝 {file}: {size} caracteres\n")
    
    # Recomendações
    report_lines.append(f"\n💡 RECOMENDAÇÕES:\n")
    if analysis['needs_ocr']:
        report_lines.append("⚠️ Extração tradicional insuficiente\n")
        report_lines.append("🔍 OCR recomendado (Tesseract ou OpenAI Vision)\n")
        report_lines.append("📄 Possível PDF escaneado ou texto ilegível\n")
    else:
        best_method = max(['pdfquery', 'pymupdf', 'pdfplumber'], 
                         key=lambda x: analysis[x])
        report_lines.append(f"✅ Extração tradicional suficiente\n")
        report_lines.append(f"🏆 Melhor resultado: {best_method.upper()}\n")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.writelines(report_lines)
    
    return report_path, analysis

def intelligent_extraction_pipeline(project_id=None, force_ocr=False, ocr_methods=['tesseract']):
    """Pipeline inteligente de extração com fallback automático para OCR"""
    
    if project_id is None:
        project_id = os.environ.get('CURRENT_PROJECT', '000.002')
    
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../resultados')
    
    print("🧠 PIPELINE INTELIGENTE DE EXTRAÇÃO")
    print("="*50)
    print(f"📂 Projeto: {project_id}")
    print(f"🔍 Métodos OCR disponíveis: {', '.join(ocr_methods)}")
    print(f"🔄 Forçar OCR: {'SIM' if force_ocr else 'NÃO'}")
    print("="*50)
    
    # Encontra PDFs do projeto
    pdf_pattern = f"{pdf_base_path}/{project_id}/*.pdf"
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"❌ Nenhum PDF encontrado em {pdf_base_path}/{project_id}/")
        return
    
    results_summary = {
        'total_files': len(pdf_files),
        'traditional_sufficient': 0,
        'ocr_applied': 0,
        'failed': 0
    }
    
    for pdf_file in pdf_files:
        filename = os.path.splitext(os.path.basename(pdf_file))[0]
        pdf_dir = f"{results_base_path}/{project_id}/{filename}"
        
        print(f"\n📄 Processando: {filename}")
        print("-" * 30)
        
        # Analisa extrações existentes
        report_path, analysis = create_extraction_report(pdf_dir, filename)
        print(f"📊 Relatório criado: {os.path.basename(report_path)}")
        
        # Decide se precisa OCR
        needs_ocr = force_ocr or analysis['needs_ocr']
        
        if needs_ocr:
            print(f"🔍 Aplicando OCR...")
            ocr_success = False
            
            for ocr_method in ocr_methods:
                print(f"Tentando {ocr_method.upper()}...")
                success = run_ocr_extraction(pdf_file, pdf_dir, filename, ocr_method)
                if success:
                    ocr_success = True
                    results_summary['ocr_applied'] += 1
                    break
            
            if not ocr_success:
                print(f"❌ Todos os métodos OCR falharam para {filename}")
                results_summary['failed'] += 1
        else:
            print(f"✅ Extração tradicional suficiente ({analysis['total']} caracteres)")
            results_summary['traditional_sufficient'] += 1
    
    # Relatório final
    print(f"\n{'='*50}")
    print("📋 RELATÓRIO FINAL DO PIPELINE")
    print(f"{'='*50}")
    print(f"📂 Total de arquivos: {results_summary['total_files']}")
    print(f"✅ Tradicionais suficientes: {results_summary['traditional_sufficient']}")
    print(f"🔍 OCR aplicado: {results_summary['ocr_applied']}")
    print(f"❌ Falharam: {results_summary['failed']}")
    
    success_rate = ((results_summary['traditional_sufficient'] + results_summary['ocr_applied']) 
                   / results_summary['total_files'] * 100)
    print(f"📊 Taxa de sucesso: {success_rate:.1f}%")

if __name__ == "__main__":
    import sys
    
    # Permite executar com parâmetros
    force_ocr = '--force-ocr' in sys.argv
    
    # Métodos OCR disponíveis
    available_methods = ['tesseract']
    
    # Verifica se OpenAI está disponível
    if os.environ.get('OPENAI_API_KEY'):
        available_methods.append('openai')
    
    # Executa pipeline
    intelligent_extraction_pipeline(
        force_ocr=force_ocr,
        ocr_methods=available_methods
    )
