# -*- coding: utf-8 -*-
"""
Script para instalar e configurar Poppler no Windows
Necessário para conversão PDF para imagem no OCR
"""
import os
import sys
import urllib.request
import zipfile
import tempfile
import shutil

def instalar_poppler_windows():
    """Instala Poppler no Windows automaticamente"""
    print("🔧 INSTALANDO POPPLER PARA WINDOWS")
    print("="*50)
    
    # URL do Poppler para Windows (versão mais recente)
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
    
    # Diretório de instalação
    install_dir = os.path.expanduser("~/poppler")
    bin_dir = os.path.join(install_dir, "poppler-23.11.0", "Library", "bin")
    
    if os.path.exists(bin_dir):
        print(f"✅ Poppler já está instalado em: {bin_dir}")
        return bin_dir
    
    print("📥 Baixando Poppler...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "poppler.zip")
            
            # Baixar arquivo
            urllib.request.urlretrieve(poppler_url, zip_path)
            print("✅ Download concluído!")
            
            # Extrair arquivo
            print("📦 Extraindo arquivos...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)
            
            print(f"✅ Poppler instalado em: {install_dir}")
            print(f"📂 Executáveis em: {bin_dir}")
            
            return bin_dir
            
    except Exception as e:
        print(f"❌ Erro ao instalar Poppler: {e}")
        return None

def adicionar_ao_path(bin_dir):
    """Adiciona o diretório do Poppler ao PATH do sistema"""
    if bin_dir and os.path.exists(bin_dir):
        # Adicionar ao PATH atual da sessão
        current_path = os.environ.get('PATH', '')
        if bin_dir not in current_path:
            os.environ['PATH'] = f"{bin_dir};{current_path}"
            print(f"✅ Poppler adicionado ao PATH da sessão atual")
        
        # Instruções para adicionar permanentemente
        print("\n💡 INSTRUÇÕES PARA PATH PERMANENTE:")
        print("1. Abra o Painel de Controle > Sistema > Configurações Avançadas")
        print("2. Clique em 'Variáveis de Ambiente'")
        print("3. Na seção 'Variáveis do Sistema', encontre 'Path' e clique em 'Editar'")
        print(f"4. Adicione o caminho: {bin_dir}")
        print("5. Clique em 'OK' para salvar")
        
        return True
    return False

def testar_poppler():
    """Testa se o Poppler está funcionando"""
    print("\n🧪 TESTANDO POPPLER...")
    
    try:
        # Tenta importar pdf2image
        from pdf2image import convert_from_path
        print("✅ pdf2image importado com sucesso!")
        
        # Verifica se pdftoppm está disponível
        result = os.system("pdftoppm -h > nul 2>&1")
        if result == 0:
            print("✅ pdftoppm está funcionando!")
            return True
        else:
            print("⚠️ pdftoppm não encontrado no PATH")
            return False
            
    except ImportError as e:
        print(f"❌ Erro ao importar pdf2image: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 CONFIGURAÇÃO DE OCR - INSTALAÇÃO DO POPPLER")
    print("="*60)
    
    # Instalar Poppler
    bin_dir = instalar_poppler_windows()
    
    if bin_dir:
        # Adicionar ao PATH
        adicionar_ao_path(bin_dir)
        
        # Testar instalação
        if testar_poppler():
            print("\n🎉 POPPLER INSTALADO E CONFIGURADO COM SUCESSO!")
            print("✅ O OCR Tesseract agora deve funcionar")
        else:
            print("\n⚠️ POPPLER INSTALADO MAS PODE PRECISAR DE CONFIGURAÇÃO ADICIONAL")
            print("💡 Reinicie o terminal ou VS Code e tente novamente")
    else:
        print("\n❌ FALHA NA INSTALAÇÃO DO POPPLER")
        print("💡 Instale manualmente: https://github.com/oschwartz10612/poppler-windows")

if __name__ == "__main__":
    main()
