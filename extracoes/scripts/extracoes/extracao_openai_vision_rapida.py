# -*- coding: utf-8 -*-
"""
Extração OpenAI Vision OTIMIZADA - Versão rápida e eficiente
"""
import os
import sys
import base64
from pdf2image import convert_from_path
import tempfile
import time
import glob

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def extract_text_openai_vision_fast(pdf_path, txt_path, api_key=None):
    """
    Extração OpenAI Vision OTIMIZADA para velocidade
    """
    if not OPENAI_AVAILABLE:
        error_msg = "❌ Biblioteca OpenAI não está instalada"
        print(error_msg)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
        return False
    
    if api_key is None:
        api_key = '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'
    
    try:
        client = OpenAI(api_key=api_key)
        print(f"🤖 Iniciando OpenAI Vision: {os.path.basename(pdf_path)}")
        
        start_time = time.time()
        
        # Converte PDF com DPI menor para velocidade
        with tempfile.TemporaryDirectory() as temp_dir:
            print("📄 Convertendo PDF...")
            pages = convert_from_path(pdf_path, dpi=200, output_folder=temp_dir)
            print(f"✅ {len(pages)} páginas convertidas")
            
            extracted_text = []
            extracted_text.append("=== EXTRAÇÃO OPENAI VISION (OTIMIZADA) ===\n")
            extracted_text.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            extracted_text.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            extracted_text.append(f"Páginas: {len(pages)}\n")
            extracted_text.append("="*50 + "\n\n")
            
            # Processa cada página
            for i, page in enumerate(pages, 1):
                page_start = time.time()
                print(f"🤖 Página {i}/{len(pages)}...", end=" ")
                
                try:
                    # Salva página
                    page_path = os.path.join(temp_dir, f"page_{i}.png")
                    page.save(page_path, "PNG", optimize=True)
                    
                    # Base64
                    with open(page_path, "rb") as f:
                        base64_image = base64.b64encode(f.read()).decode('utf-8')
                    
                    # API call
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Extraia todo o texto desta imagem. Mantenha formatação e estrutura."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=3000,
                        temperature=0
                    )
                    
                    page_text = response.choices[0].message.content
                    page_elapsed = time.time() - page_start
                    
                    if page_text and page_text.strip():
                        extracted_text.append(f"=== PÁGINA {i} ===\n")
                        extracted_text.append(page_text.strip())
                        extracted_text.append(f"\n\n{'='*30}\n\n")
                        print(f"✅ {len(page_text)} chars ({page_elapsed:.1f}s)")
                    else:
                        extracted_text.append(f"=== PÁGINA {i} ===\n")
                        extracted_text.append("[SEM TEXTO DETECTADO]")
                        extracted_text.append(f"\n\n{'='*30}\n\n")
                        print(f"⚠️ Sem texto ({page_elapsed:.1f}s)")
                        
                except Exception as e:
                    page_elapsed = time.time() - page_start
                    print(f"❌ Erro ({page_elapsed:.1f}s)")
                    extracted_text.append(f"=== PÁGINA {i} ===\n")
                    extracted_text.append(f"[ERRO: {e}]")
                    extracted_text.append(f"\n\n{'='*30}\n\n")
        
        # Salva resultado
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(extracted_text))
        
        total_elapsed = time.time() - start_time
        file_size = os.path.getsize(txt_path) if os.path.exists(txt_path) else 0
        
        print(f"✅ Concluído: {file_size} bytes em {total_elapsed:.1f}s")
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"ERRO: {e}\n")
        return False

def extract_structured_openai_vision_fast(pdf_path, output_path, api_key=None):
    """Análise estruturada rápida"""
    if not OPENAI_AVAILABLE:
        return False
    
    if api_key is None:
        api_key = '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'
    
    try:
        client = OpenAI(api_key=api_key)
        print(f"🧠 Análise estruturada: {os.path.basename(pdf_path)}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Converte apenas primeira página para análise geral
            pages = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)
            
            if not pages:
                return False
            
            page_path = os.path.join(temp_dir, "page_1.png")
            pages[0].save(page_path, "PNG")
            
            with open(page_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            # Análise estruturada
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analise este documento e extraia:
                                1. Tipo de documento
                                2. Datas importantes
                                3. Valores monetários
                                4. Nomes/empresas
                                5. Números de documento
                                6. Estrutura geral
                                
                                Seja objetivo e organizado."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            
            # Salva análise
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=== ANÁLISE ESTRUTURADA OPENAI VISION ===\n")
                f.write(f"Arquivo: {os.path.basename(pdf_path)}\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*50 + "\n\n")
                f.write(analysis)
            
            print(f"✅ Análise estruturada salva")
            return True
            
    except Exception as e:
        print(f"❌ Erro na análise estruturada: {e}")
        return False

# Sistema multiprojeto otimizado
if __name__ == "__main__":
    print("🚀 OPENAI VISION - EXTRAÇÃO OTIMIZADA")
    print("="*50)
    
    current_project = os.environ.get('CURRENT_PROJECT', 'novos_arquivos')
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../../resultados')
    
    print(f"📂 Projeto: {current_project}")
    print(f"📁 Base PDFs: {pdf_base_path}")
    print(f"💾 Base resultados: {results_base_path}")
    
    # Busca PDFs
    pdf_pattern = f"{pdf_base_path}/{current_project}/*.pdf"
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"❌ Nenhum PDF em {pdf_pattern}")
        exit(1)
    
    print(f"📄 PDFs encontrados: {len(pdf_files)}")
    
    # Cria diretório de resultados
    project_output_dir = f"{results_base_path}/{current_project}"
    os.makedirs(project_output_dir, exist_ok=True)
    
    # Estatísticas
    total_start = time.time()
    success_count = 0
    error_count = 0
    
    # Processa cada PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        filename = os.path.splitext(os.path.basename(pdf_file))[0]
        
        print(f"\n📄 [{i}/{len(pdf_files)}] {filename}")
        print("-" * 50)
        
        # Cria pasta individual
        pdf_dir = f"{project_output_dir}/{filename}"
        os.makedirs(pdf_dir, exist_ok=True)
        
        file_start = time.time()
        
        # Extração básica
        txt_output = f"{pdf_dir}/openai_vision_{filename}.txt"
        if extract_text_openai_vision_fast(pdf_file, txt_output):
            success_count += 1
        else:
            error_count += 1
        
        # Análise estruturada
        structured_output = f"{pdf_dir}/openai_structured_{filename}.txt"
        if extract_structured_openai_vision_fast(pdf_file, structured_output):
            success_count += 1
        else:
            error_count += 1
        
        file_elapsed = time.time() - file_start
        print(f"⏱️ Total arquivo: {file_elapsed:.1f}s")
        
        # Mostra tamanhos
        if os.path.exists(txt_output):
            size = os.path.getsize(txt_output)
            print(f"📊 Extração: {size} bytes")
        
        if os.path.exists(structured_output):
            size = os.path.getsize(structured_output)
            print(f"📊 Estruturada: {size} bytes")
    
    # Relatório final
    total_elapsed = time.time() - total_start
    print(f"\n{'='*50}")
    print(f"📋 RELATÓRIO FINAL")
    print(f"{'='*50}")
    print(f"📂 Projeto: {current_project}")
    print(f"📄 PDFs: {len(pdf_files)}")
    print(f"✅ Sucessos: {success_count}")
    print(f"❌ Erros: {error_count}")
    print(f"⏱️ Tempo total: {total_elapsed:.1f}s")
    print(f"⚡ Tempo médio: {total_elapsed/len(pdf_files):.1f}s por PDF")
    
    if success_count > 0:
        rate = (success_count/(success_count+error_count))*100
        print(f"📊 Taxa sucesso: {rate:.1f}%")
    
    print(f"📁 Resultados: {project_output_dir}")
    print(f"🎉 FINALIZADO!")
