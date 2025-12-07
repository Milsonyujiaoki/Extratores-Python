# -*- coding: utf-8 -*-
"""
Extração usando Tesseract OCR - Para PDFs escaneados ou com texto ilegível
Biblioteca: pytesseract + pdf2image
Instalação: 
- pip install pytesseract pdf2image pillow
- Baixar Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
"""
import os
import sys
import pytesseract
from pdf2image import convert_from_path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from PIL import Image
import tempfile
import shutil

# Configuração do Tesseract (ajustar conforme instalação)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_tesseract_ocr(pdf_path, txt_path, language='por'):
    """
    Extrai texto usando OCR via Tesseract
    """
    try:
        print(f"🔍 Iniciando OCR Tesseract para {os.path.basename(pdf_path)}...")
        
        # Converte PDF para imagens
        with tempfile.TemporaryDirectory() as temp_dir:
            print("📄 Convertendo PDF para imagens...")
            pages = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir)
            
            extracted_text = []
            extracted_text.append("=== EXTRAÇÃO OCR TESSERACT ===\n")
            extracted_text.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            extracted_text.append(f"Páginas processadas: {len(pages)}\n")
            extracted_text.append("="*50 + "\n\n")
            
            # Processa cada página
            for i, page in enumerate(pages, 1):
                print(f"🔍 Processando página {i}/{len(pages)} com OCR...")
                
                # Aplica OCR na imagem
                try:
                    # Configurações otimizadas para documentos
                    custom_config = r'--oem 3 --psm 6 -l por'
                    page_text = pytesseract.image_to_string(page, config=custom_config)
                    
                    if page_text.strip():
                        extracted_text.append(f"=== PÁGINA {i} ===\n")
                        extracted_text.append(page_text.strip())
                        extracted_text.append(f"\n\n{'='*30}\n\n")
                    else:
                        extracted_text.append(f"=== PÁGINA {i} ===\n")
                        extracted_text.append("[PÁGINA EM BRANCO OU SEM TEXTO DETECTADO]")
                        extracted_text.append(f"\n\n{'='*30}\n\n")
                        
                except Exception as e:
                    print(f"⚠️ Erro na página {i}: {e}")
                    extracted_text.append(f"=== PÁGINA {i} ===\n")
                    extracted_text.append(f"[ERRO NO OCR: {e}]")
                    extracted_text.append(f"\n\n{'='*30}\n\n")
        
        # Salva resultado
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(extracted_text))
        
        print(f"✅ Tesseract OCR: Texto extraído para {txt_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no Tesseract OCR: {e}")
        # Salva erro no arquivo
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"ERRO NO TESSERACT OCR: {e}\n")
            f.write("Verifique se o Tesseract está instalado corretamente.\n")
            f.write("Download: https://github.com/UB-Mannheim/tesseract/wiki\n")
        return False

def extract_enhanced_ocr(pdf_path, output_path):
    """
    Extração OCR com técnicas avançadas de pré-processamento
    """
    try:
        print(f"🚀 OCR Avançado para {os.path.basename(pdf_path)}...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Converte com alta resolução
            pages = convert_from_path(pdf_path, dpi=400, output_folder=temp_dir)
            
            results = []
            results.append("=== OCR TESSERACT AVANÇADO ===\n")
            results.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            results.append(f"Resolução: 400 DPI\n")
            results.append(f"Total de páginas: {len(pages)}\n")
            results.append("="*50 + "\n\n")
            
            for i, page in enumerate(pages, 1):
                print(f"🔍 Página {i}: Aplicando pré-processamento...")
                
                # Diferentes configurações de OCR para tentar
                configs = [
                    ('Padrão', r'--oem 3 --psm 6 -l por'),
                    ('Documento Único', r'--oem 3 --psm 3 -l por'),
                    ('Bloco de Texto', r'--oem 3 --psm 8 -l por'),
                    ('Linha Única', r'--oem 3 --psm 7 -l por')
                ]
                
                best_text = ""
                best_config = ""
                
                for config_name, config in configs:
                    try:
                        text = pytesseract.image_to_string(page, config=config)
                        if len(text.strip()) > len(best_text.strip()):
                            best_text = text
                            best_config = config_name
                    except:
                        continue
                
                results.append(f"=== PÁGINA {i} ===\n")
                results.append(f"Melhor configuração: {best_config}\n")
                results.append(f"Caracteres extraídos: {len(best_text.strip())}\n")
                results.append("-" * 30 + "\n")
                results.append(best_text.strip() if best_text.strip() else "[SEM TEXTO DETECTADO]")
                results.append(f"\n\n{'='*40}\n\n")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(results))
        
        print(f"✅ OCR Avançado: Resultado salvo em {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no OCR Avançado: {e}")
        return False

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
            
            # OCR básico
            txt_output = f"{pdf_dir}/tesseract_ocr_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com Tesseract OCR...")
            extract_text_tesseract_ocr(pdf_file, txt_output)
            
            # OCR avançado
            enhanced_output = f"{pdf_dir}/tesseract_enhanced_{filename}.txt"
            print(f"Aplicando OCR avançado em {pdf_file}...")
            extract_enhanced_ocr(pdf_file, enhanced_output)
