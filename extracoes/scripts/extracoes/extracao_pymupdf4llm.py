"""
Extração usando pymupdf4llm - Otimizado para LLMs (Large Language Models)
Biblioteca: pymupdf4llm
Instalação: pip install pymupdf4llm
"""
try:
    import pymupdf4llm
except ImportError:
    print("pymupdf4llm não está instalado. Execute: pip install pymupdf4llm")
    pymupdf4llm = None

import os

def extract_text_pymupdf4llm(pdf_path, txt_path):
    """
    Extrai texto usando pymupdf4llm - otimizado para LLMs
    Mantém melhor formatação e estrutura para processamento por IA
    """
    if pymupdf4llm is None:
        print("Biblioteca pymupdf4llm não disponível")
        return
        
    try:
        # Extrai texto otimizado para LLMs
        text = pymupdf4llm.to_markdown(pdf_path)
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"PyMuPDF4LLM: Texto extraído para {txt_path}")
        
    except Exception as e:
        print(f"Erro no PyMuPDF4LLM: {e}")

def extract_markdown_pymupdf4llm(pdf_path, md_path):
    """
    Extrai e converte para Markdown usando pymupdf4llm
    """
    if pymupdf4llm is None:
        print("Biblioteca pymupdf4llm não disponível")
        return
        
    try:
        # Extrai como Markdown
        markdown_text = pymupdf4llm.to_markdown(pdf_path)
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        
        print(f"PyMuPDF4LLM: Markdown extraído para {md_path}")
        
    except Exception as e:
        print(f"Erro na conversão para Markdown: {e}")

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
        
        # Garante que os diretórios de saída existem
        txt_dir = f"../resultados/{current_project}/txt"
        md_dir = f"../resultados/{current_project}/md"
        os.makedirs(txt_dir, exist_ok=True)
        os.makedirs(md_dir, exist_ok=True)
        
        for pdf_file in pdf_files:
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Extração de texto otimizado para LLM
            txt_output = f"../resultados/{current_project}/txt/pymupdf4llm_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com PyMuPDF4LLM...")
            extract_text_pymupdf4llm(pdf_file, txt_output)
            
            # Extração como Markdown
            md_output = f"../resultados/{current_project}/md/pymupdf4llm_{filename}.md"
            print(f"Convertendo {pdf_file} para Markdown...")
            extract_markdown_pymupdf4llm(pdf_file, md_output)
