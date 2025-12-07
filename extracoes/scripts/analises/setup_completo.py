"""
Script para instalar todas as bibliotecas de extração e executar testes
"""
import subprocess
import sys
import os

def install_libraries():
    """
    Instala todas as bibliote    print("\nPara executar os testes:")
    print("1. Execute scripts individuais: python extracao_[nome].py")
    print("2. Execute todos: python teste_todas_bibliotecas.py")de extração necessárias
    """
    libraries = [
        "PyPDF2",
        "pdfminer.six", 
        "PyMuPDF",
        "pdfplumber",
        "camelot-py[cv]",
        "tabula-py",
        "tika",
        "pdfquery",
        "pymupdf4llm",
        "python-docx",
        "openpyxl",
        "xlrd",
        "python-tika",
        "slate3k",
        "pdfminer3k",
        "textract"
    ]
    
    print("Instalando bibliotecas de extração de PDF...")
    print("="*50)
    
    for lib in libraries:
        try:
            print(f"Instalando {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print(f"✓ {lib} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"✗ Erro ao instalar {lib}: {e}")
        except Exception as e:
            print(f"✗ Erro inesperado com {lib}: {e}")
        print()
    
    print("Instalação concluída!")

def update_existing_scripts():
    """
    Atualiza os scripts existentes para usar os arquivos da pasta 000.002
    """
    # Atualizar PyPDF2
    update_pypdf2()
    update_pdfminer()
    update_pymupdf()
    update_pdfplumber()

def update_pypdf2():
    """Atualiza o script do PyPDF2 para pasta 000.002"""
    script_content = '''import PyPDF2
import os

def extract_text_pypdf2(pdf_path, txt_path):
    """Extrai texto usando PyPDF2"""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            with open(txt_path, "w", encoding="utf-8") as txt_file:
                for page_num, page in enumerate(reader.pages):
                    txt_file.write(f"=== Página {page_num + 1} ===\\n")
                    txt_file.write(page.extract_text() + "\\n\\n")
        print(f"PyPDF2: Texto extraído para {txt_path}")
    except Exception as e:
        print(f"Erro no PyPDF2: {e}")

# Executa para arquivos da pasta 000.002
if __name__ == "__main__":
    pdf_files = ["000.002/000.002.pdf", "000.002/CP_000.002.pdf"]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            txt_output = f"000.002/pypdf2_{filename}.txt"
            print(f"Processando {pdf_file}...")
            extract_text_pypdf2(pdf_file, txt_output)
'''
    
    with open("extracao_pyPdf2.py", "w", encoding="utf-8") as f:
        f.write(script_content)

def update_pdfminer():
    """Atualiza o script do PDFMiner para pasta 000.002"""
    script_content = '''from pdfminer.high_level import extract_text
import os

def extract_text_pdfminer(pdf_path, txt_path):
    """Extrai texto usando PDFMiner"""
    try:
        text = extract_text(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(text)
        print(f"PDFMiner: Texto extraído para {txt_path}")
    except Exception as e:
        print(f"Erro no PDFMiner: {e}")

# Executa para arquivos da pasta 000.002
if __name__ == "__main__":
    pdf_files = ["000.002/000.002.pdf", "000.002/CP_000.002.pdf"]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            txt_output = f"000.002/pdfminer_{filename}.txt"
            print(f"Processando {pdf_file}...")
            extract_text_pdfminer(pdf_file, txt_output)
'''
    
    with open("extracao_pdfMiner.py", "w", encoding="utf-8") as f:
        f.write(script_content)

def update_pymupdf():
    """Atualiza o script do PyMuPDF para pasta 000.002"""
    script_content = '''import fitz
import os

def extract_text_pymupdf(pdf_path, txt_path):
    """Extrai texto usando PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            for page_num, page in enumerate(doc):
                txt_file.write(f"=== Página {page_num + 1} ===\\n")
                txt_file.write(page.get_text("text") + "\\n\\n")
        doc.close()
        print(f"PyMuPDF: Texto extraído para {txt_path}")
    except Exception as e:
        print(f"Erro no PyMuPDF: {e}")

# Executa para arquivos da pasta 000.002
if __name__ == "__main__":
    pdf_files = ["000.002/000.002.pdf", "000.002/CP_000.002.pdf"]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            txt_output = f"000.002/pymupdf_{filename}.txt"
            print(f"Processando {pdf_file}...")
            extract_text_pymupdf(pdf_file, txt_output)
'''
    
    with open("extracao_pyMuPdf.py", "w", encoding="utf-8") as f:
        f.write(script_content)

def update_pdfplumber():
    """Atualiza o script do PDFPlumber para pasta 000.002"""
    script_content = '''import pdfplumber
import os

def extract_text_pdfplumber(pdf_path, txt_path):
    """Extrai texto usando PDFPlumber"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            with open(txt_path, "w", encoding="utf-8") as txt_file:
                for page_num, page in enumerate(pdf.pages):
                    txt_file.write(f"=== Página {page_num + 1} ===\\n")
                    text = page.extract_text()
                    if text:
                        txt_file.write(text + "\\n\\n")
        print(f"PDFPlumber: Texto extraído para {txt_path}")
    except Exception as e:
        print(f"Erro no PDFPlumber: {e}")

# Executa para arquivos da pasta 000.002
if __name__ == "__main__":
    pdf_files = ["000.002/000.002.pdf", "000.002/CP_000.002.pdf"]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            txt_output = f"000.002/pdfplumber_{filename}.txt"
            print(f"Processando {pdf_file}...")
            extract_text_pdfplumber(pdf_file, txt_output)
'''
    
    with open("extracao_pdfPlumber.py", "w", encoding="utf-8") as f:
        f.write(script_content)

if __name__ == "__main__":
    print("SETUP COMPLETO PARA TESTES DE EXTRAÇÃO")
    print("="*50)
    
    choice = input("Deseja instalar as bibliotecas? (s/n): ").lower()
    if choice == 's':
        install_libraries()
    
    print("\\nAtualizando scripts existentes...")
    update_existing_scripts()
    
    print("\n✓ Setup concluído!")
    print("\nPara executar os testes:")
    print("1. Execute scripts individuais: python extracao_[nome].py")
    print("2. Execute todos: python teste_todas_bibliotecas.py")
