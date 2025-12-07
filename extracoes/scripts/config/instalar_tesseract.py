# -*- coding: utf-8 -*-
"""
Script para instalar Tesseract OCR no Windows
"""
import os
import sys
import urllib.request
import subprocess
import tempfile

def instalar_tesseract_windows():
    """Instala Tesseract OCR no Windows"""
    print("🔧 INSTALANDO TESSERACT OCR PARA WINDOWS")
    print("="*50)
    
    # URL do Tesseract para Windows (installer)
    tesseract_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    
    # Diretório de instalação típico
    install_dir = r"C:\Program Files\Tesseract-OCR"
    tesseract_exe = os.path.join(install_dir, "tesseract.exe")
    
    if os.path.exists(tesseract_exe):
        print(f"✅ Tesseract já está instalado em: {tesseract_exe}")
        return tesseract_exe
    
    print("📥 Baixando Tesseract OCR installer...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            installer_path = os.path.join(temp_dir, "tesseract-installer.exe")
            
            # Baixar installer
            urllib.request.urlretrieve(tesseract_url, installer_path)
            print("✅ Download concluído!")
            
            # Executar installer silenciosamente
            print("📦 Instalando Tesseract...")
            print("💡 NOTA: O installer pode solicitar permissões de administrador")
            
            result = subprocess.run([
                installer_path, 
                "/S",  # Instalação silenciosa
                "/D=" + install_dir
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Tesseract instalado em: {install_dir}")
                return tesseract_exe
            else:
                print(f"❌ Erro na instalação: {result.stderr}")
                return None
                
    except Exception as e:
        print(f"❌ Erro ao instalar Tesseract: {e}")
        print("💡 Instale manualmente de: https://github.com/UB-Mannheim/tesseract/wiki")
        return None

def configurar_tesseract_path():
    """Configura o PATH do Tesseract"""
    install_dir = r"C:\Program Files\Tesseract-OCR"
    tesseract_exe = os.path.join(install_dir, "tesseract.exe")
    
    if os.path.exists(tesseract_exe):
        # Configurar variável de ambiente para pytesseract
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe
        
        # Adicionar ao PATH da sessão
        current_path = os.environ.get('PATH', '')
        if install_dir not in current_path:
            os.environ['PATH'] = f"{install_dir};{current_path}"
            print(f"✅ Tesseract adicionado ao PATH: {install_dir}")
        
        return tesseract_exe
    
    return None

def testar_tesseract():
    """Testa se o Tesseract está funcionando"""
    print("\n🧪 TESTANDO TESSERACT OCR...")
    
    try:
        # Configura o path primeiro
        tesseract_exe = configurar_tesseract_path()
        
        if not tesseract_exe:
            print("❌ Tesseract não encontrado")
            return False
        
        # Testa pytesseract
        import pytesseract
        from PIL import Image
        
        # Cria uma imagem de teste simples
        import tempfile
        from PIL import Image, ImageDraw, ImageFont
        
        # Criar imagem de teste
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST OCR", fill='black')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            img.save(temp_file.name)
            
            # Testar OCR
            text = pytesseract.image_to_string(temp_file.name)
            os.unlink(temp_file.name)
            
            if "TEST" in text:
                print("✅ Tesseract OCR está funcionando!")
                return True
            else:
                print(f"⚠️ OCR executado mas resultado inesperado: {text.strip()}")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 CONFIGURAÇÃO TESSERACT OCR")
    print("="*40)
    
    # Tentar configurar path primeiro (se já instalado)
    tesseract_exe = configurar_tesseract_path()
    
    if not tesseract_exe:
        # Instalar se não encontrado
        tesseract_exe = instalar_tesseract_windows()
        
        if tesseract_exe:
            configurar_tesseract_path()
    
    # Testar instalação
    if testar_tesseract():
        print("\n🎉 TESSERACT CONFIGURADO COM SUCESSO!")
        print("✅ O OCR agora deve funcionar completamente")
    else:
        print("\n⚠️ TESSERACT PODE PRECISAR DE CONFIGURAÇÃO ADICIONAL")
        print("💡 Tente instalar manualmente ou reiniciar o VS Code")

if __name__ == "__main__":
    main()
