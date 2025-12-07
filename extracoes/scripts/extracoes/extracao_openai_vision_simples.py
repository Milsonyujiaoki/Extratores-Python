# -*- coding: utf-8 -*-
"""
Extração OpenAI Vision SIMPLES e RÁPIDA - Teste básico
"""
import os
import sys
import base64
from pdf2image import convert_from_path
import tempfile
import time

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

def extract_one_pdf_simple(pdf_path, api_key=None):
    """Extrai texto de UM PDF de forma simples"""
    
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI não disponível")
        return False
    
    if api_key is None:
        api_key = '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'
    
    print(f"🤖 TESTE SIMPLES OpenAI Vision")
    print(f"📄 Arquivo: {os.path.basename(pdf_path)}")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Converte apenas a primeira página
        print("📄 Convertendo primeira página...")
        pages = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        
        if not pages:
            print("❌ Nenhuma página convertida")
            return False
            
        print(f"✅ Página convertida: {len(pages)} página")
        
        # Salva temporariamente
        with tempfile.TemporaryDirectory() as temp_dir:
            page_path = os.path.join(temp_dir, "page_1.png")
            pages[0].save(page_path, "PNG")
            
            # Verifica tamanho
            size = os.path.getsize(page_path) / 1024
            print(f"📊 Tamanho da imagem: {size:.1f} KB")
            
            # Codifica base64
            print("🔄 Codificando base64...")
            with open(page_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            print(f"✅ Base64: {len(base64_image)} caracteres")
            
            # Chama API
            print("🌐 Chamando OpenAI API...")
            start_time = time.time()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extraia o texto desta imagem de documento. Seja conciso."
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
                max_tokens=1000,
                temperature=0
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️ Tempo da API: {elapsed:.2f}s")
            
            # Resultado
            text = response.choices[0].message.content
            print(f"✅ Texto extraído: {len(text)} caracteres")
            print(f"📝 Preview: {text[:200]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

if __name__ == "__main__":
    import glob
    
    # Configuração
    current_project = os.environ.get('CURRENT_PROJECT', 'novos_arquivos')
    pdf_base_path = "../../pdfs"
    
    print("🚀 TESTE SIMPLES OPENAI VISION")
    print("="*50)
    
    # Busca PDFs
    pdf_pattern = f"{pdf_base_path}/{current_project}/*.pdf"
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"❌ Nenhum PDF em {pdf_pattern}")
    else:
        print(f"📂 Projeto: {current_project}")
        print(f"📄 PDFs encontrados: {len(pdf_files)}")
        
        # Testa apenas o primeiro PDF
        first_pdf = pdf_files[0]
        print(f"🎯 Testando: {os.path.basename(first_pdf)}")
        
        success = extract_one_pdf_simple(first_pdf)
        
        if success:
            print("🎉 TESTE BEM-SUCEDIDO!")
        else:
            print("❌ TESTE FALHOU")
