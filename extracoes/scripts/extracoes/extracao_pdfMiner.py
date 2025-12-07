"""
Extração usando PDFMiner - biblioteca para análise de PDFs
Biblioteca: pdfminer.six
Instalação: pip install pdfminer.six
"""
from pdfminer.high_level import extract_text
import os

def extract_text_pdfminer(pdf_path, txt_path):
    """
    Extrai texto usando PDFMiner - boa para documentos complexos
    """
    try:
        text = extract_text(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(text)
        print(f"PDFMiner: Texto extraído com sucesso para {txt_path}")
    except Exception as e:
        print(f"Erro no PDFMiner: {e}")

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
            txt_output = f"../resultados/{current_project}/txt/pdfMiner_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com PDFMiner...")
            extract_text_pdfminer(pdf_file, txt_output)