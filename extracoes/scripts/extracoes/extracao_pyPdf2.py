"""
Extração usando PyPDF2 - biblioteca popular para manipulação de PDFs
Biblioteca: PyPDF2
Instalação: pip install PyPDF2
"""
import PyPDF2
import os

def extract_text_pypdf2(pdf_path, txt_path):
    """
    Extrai texto usando PyPDF2 - biblioteca clássica para PDFs
    """
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            with open(txt_path, "w", encoding="utf-8") as txt_file:
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        txt_file.write(f"--- Página {page_num} ---\n")
                        txt_file.write(text + "\n\n")
        print(f"PyPDF2: Texto extraído com sucesso para {txt_path}")
    except Exception as e:
        print(f"Erro no PyPDF2: {e}")

# Sistema multiprojeto - usa variável de ambiente CURRENT_PROJECT
if __name__ == "__main__":
    import glob
    
    # Obtém o projeto atual da variável de ambiente
    current_project = os.environ.get('CURRENT_PROJECT', '000.002')
    
    # Descobre automaticamente os PDFs do projeto
    pdf_pattern = f"../pdfs/{current_project}/*.pdf"
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"❌ Nenhum PDF encontrado em ../pdfs/{current_project}/")
    else:
        print(f"📂 Processando projeto {current_project} com {len(pdf_files)} PDFs")
        
        # Garante que o diretório de saída existe
        output_dir = f"../resultados/{current_project}/txt"
        os.makedirs(output_dir, exist_ok=True)
        
        for pdf_file in pdf_files:
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            txt_output = f"../resultados/{current_project}/txt/PyPDF2_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com PyPDF2...")
            extract_text_pypdf2(pdf_file, txt_output)
