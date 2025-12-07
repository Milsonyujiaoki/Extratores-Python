"""
Extração usando Tika - Apache Tika para Python
Biblioteca: tika
Instalação: pip install tika
Requer Java instalado no sistema
"""
from tika import parser
import os

def extract_text_tika(pdf_path, txt_path):
    """
    Extrai texto usando Apache Tika - boa para diversos formatos
    """
    try:
        # Parse do arquivo PDF
        parsed = parser.from_file(pdf_path)
        
        # Extrai o texto
        text = parsed["content"]
        
        if text:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Tika: Texto extraído com sucesso para {txt_path}")
        else:
            print(f"Tika: Nenhum texto encontrado em {pdf_path}")
            
    except Exception as e:
        print(f"Erro no Tika: {e}")

def extract_metadata_tika(pdf_path, metadata_path):
    """
    Extrai metadados usando Apache Tika
    """
    try:
        parsed = parser.from_file(pdf_path)
        metadata = parsed["metadata"]
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write("Metadados do arquivo - Apache Tika\n")
            f.write("="*50 + "\n")
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
        
        print(f"Tika: Metadados extraídos para {metadata_path}")
        
    except Exception as e:
        print(f"Erro na extração de metadados com Tika: {e}")

# Exemplo de uso para os arquivos da pasta 000.002
if __name__ == "__main__":
    pdf_files = [
        "../pdfs/000.002/000.002.pdf",
        "../pdfs/000.002/CP_000.002.pdf"
    ]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Extração de texto
            txt_output = f"../resultados/000.002/txt/tika_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com Tika...")
            extract_text_tika(pdf_file, txt_output)
            
            # Extração de metadados
            metadata_output = f"../resultados/000.002/txt/tika_metadata_{filename}.txt"
            print(f"Extraindo metadados de {pdf_file} com Tika...")
            extract_metadata_tika(pdf_file, metadata_output)
