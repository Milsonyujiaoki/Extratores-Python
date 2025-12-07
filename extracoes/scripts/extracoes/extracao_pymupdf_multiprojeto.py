"""
Extração usando PyMuPDF (fitz) - Versão Multi-Projeto
Biblioteca: PyMuPDF
Instalação: pip install PyMuPDF
Suporta processamento de múltiplos projetos automaticamente
"""
import fitz
import os
import glob

def discover_projects():
    """Descobre automaticamente todos os projetos na pasta pdfs"""
    pdf_base_path = "../pdfs"
    projects = []
    
    # Verifica se há variável de ambiente para projeto específico
    current_project = os.environ.get('CURRENT_PROJECT')
    if current_project:
        project_path = os.path.join(pdf_base_path, current_project)
        if os.path.exists(project_path):
            pdf_files = glob.glob(os.path.join(project_path, "*.pdf"))
            if pdf_files:
                return [{
                    'id': current_project,
                    'pdfs': [(os.path.basename(f), f) for f in pdf_files]
                }]
    
    # Caso contrário, descobre todos os projetos
    if os.path.exists(pdf_base_path):
        project_dirs = [d for d in os.listdir(pdf_base_path) 
                       if os.path.isdir(os.path.join(pdf_base_path, d)) 
                       and d.startswith('000.')]
        
        for project_dir in sorted(project_dirs):
            project_path = os.path.join(pdf_base_path, project_dir)
            pdf_files = glob.glob(os.path.join(project_path, "*.pdf"))
            
            if pdf_files:
                projects.append({
                    'id': project_dir,
                    'pdfs': [(os.path.basename(f), f) for f in pdf_files]
                })
    
    return projects

def extract_text_pymupdf(pdf_path, txt_path):
    """
    Extrai texto usando PyMuPDF - biblioteca muito rápida e eficiente
    """
    try:
        doc = fitz.open(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            # Adiciona cabeçalho com informações do arquivo
            txt_file.write(f"EXTRAÇÃO PyMuPDF\\n")
            txt_file.write(f"Arquivo: {os.path.basename(pdf_path)}\\n")
            txt_file.write(f"Total de páginas: {len(doc)}\\n")
            txt_file.write(f"Data: {os.path.getmtime(pdf_path)}\\n")
            txt_file.write("="*50 + "\\n\\n")
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text("text")
                if text:
                    txt_file.write(f"--- PÁGINA {page_num} ---\\n")
                    txt_file.write(text + "\\n\\n")
        doc.close()
        print(f"PyMuPDF: ✅ {os.path.basename(pdf_path)} -> {os.path.basename(txt_path)}")
    except Exception as e:
        print(f"PyMuPDF: ❌ Erro em {os.path.basename(pdf_path)}: {e}")

def process_project(project_id, pdf_files):
    """Processa todos os PDFs de um projeto"""
    print(f"\\n📂 Processando projeto: {project_id}")
    
    # Garante que o diretório de saída existe
    output_dir = f"../resultados/{project_id}/txt"
    os.makedirs(output_dir, exist_ok=True)
    
    processed = 0
    for pdf_name, pdf_path in pdf_files:
        # Nome do arquivo de saída com identificação clara
        base_name = os.path.splitext(pdf_name)[0]
        txt_output = os.path.join(output_dir, f"PyMuPDF_{base_name}.txt")
        
        print(f"  📄 {pdf_name} -> PyMuPDF_{base_name}.txt")
        extract_text_pymupdf(pdf_path, txt_output)
        processed += 1
    
    print(f"  ✅ {processed} arquivos processados")
    return processed

# Execução principal
if __name__ == "__main__":
    print("🚀 PyMuPDF - EXTRAÇÃO MULTI-PROJETO")
    print("="*40)
    
    projects = discover_projects()
    
    if not projects:
        print("❌ Nenhum projeto encontrado!")
    else:
        total_files = 0
        for project in projects:
            files_processed = process_project(project['id'], project['pdfs'])
            total_files += files_processed
        
        print(f"\\n✅ CONCLUÍDO: {total_files} arquivos processados")
        print("📁 Resultados salvos em: ../resultados/[projeto]/txt/")
