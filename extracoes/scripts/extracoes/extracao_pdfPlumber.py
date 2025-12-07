"""
Extração usando PDFPlumber - biblioteca para extração de texto e tabelas
Biblioteca: pdfplumber
Instalação: pip install pdfplumber
"""
import pdfplumber
import os

def extract_text_pdfplumber(pdf_path, txt_path):
    """
    Extrai texto usando PDFPlumber - excelente para tabelas e estruturas
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            with open(txt_path, "w", encoding="utf-8") as txt_file:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        txt_file.write(f"--- Página {page_num} ---\n")
                        txt_file.write(text + "\n\n")
        print(f"PDFPlumber: Texto extraído com sucesso para {txt_path}")
    except Exception as e:
        print(f"Erro no PDFPlumber: {e}")

# Sistema multiprojeto - usa variável de ambiente CURRENT_PROJECT
if __name__ == "__main__":
    import glob
    
    # Obtém o projeto atual da variável de ambiente
    current_project = os.environ.get('CURRENT_PROJECT', '000.002')
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../resultados')
    
    # Descobre automaticamente os PDFs do projeto
    pdf_pattern = f"{pdf_base_path}/{current_project}/*.pdf"
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"❌ Nenhum PDF encontrado em {pdf_base_path}/{current_project}/")
    else:
        print(f"📂 Processando projeto {current_project} com {len(pdf_files)} PDFs")
        
        # Garante que o diretório de saída existe para o projeto
        project_output_dir = f"{results_base_path}/{current_project}"
        os.makedirs(project_output_dir, exist_ok=True)
        
        for pdf_file in pdf_files:
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Cria pasta individual para cada arquivo PDF
            pdf_dir = f"{project_output_dir}/{filename}"
            os.makedirs(pdf_dir, exist_ok=True)
            
            txt_output = f"{pdf_dir}/pdfPlumber_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com PDFPlumber...")
            extract_text_pdfplumber(pdf_file, txt_output)