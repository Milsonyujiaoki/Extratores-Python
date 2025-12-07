import os
import logging
from pathlib import Path
import pdfplumber
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
import configparser

# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === Caminhos fixos (editáveis) ===
config = configparser.ConfigParser()
# Procura o config.ini no mesmo diretório do script
script_dir = Path(__file__).parent
config_file = script_dir / 'config.ini'

# Verifica se o arquivo de configuração existe
if config_file.exists():
    # Tenta diferentes encodings
    for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
        try:
            config.read(config_file, encoding=encoding)
            if config.has_section('Paths'):
                try:
                    PDF_PATH = Path(config.get('Paths', 'PDF_PATH'))
                    OUTPUT_PATH = Path(config.get('Paths', 'OUTPUT_PATH_HYBRID'))
                    logger.info(f"Configuração carregada com encoding: {encoding}")
                    logger.info(f"Arquivo config encontrado em: {config_file}")
                    break
                except configparser.NoOptionError as option_error:
                    logger.error(f"Chave faltando no config.ini: {option_error}")
                    raise option_error
        except Exception as e:
            logger.debug(f"Falha com encoding {encoding}: {e}")
            continue
    else:
        logger.error("Não foi possível carregar o config.ini com nenhum encoding")
        raise configparser.Error("Falha ao carregar configuração")
        
    if not config.has_section('Paths'):
        logger.error("Seção 'Paths' não encontrada no config.ini")
        raise configparser.NoSectionError('Paths')
else:
    logger.error(f"Arquivo config.ini não encontrado em: {config_file}")
    raise FileNotFoundError(f"config.ini não encontrado em {config_file}")

# Configurar o caminho do Tesseract (ajuste conforme sua instalação)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_direct(pdf_path: Path) -> str:
    """Extrai texto diretamente do PDF."""
    logger.info("Tentando extração direta...")
    text_content = []
    
    try:
        # Tenta primeiro com pdfplumber
        logger.info("Tentando pdfplumber...")
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(f"=== PÁGINA {page_num} ===\n{text}\n")
                except Exception as page_error:
                    logger.warning(f"Erro ao processar página {page_num} com pdfplumber: {page_error}")
                    continue
                    
        if text_content:
            logger.info(f"pdfplumber extraiu texto de {len(text_content)} páginas")
            return "\n".join(text_content)
        
        # Se pdfplumber falhou, tenta PyPDF2
        logger.info("pdfplumber não extraiu texto, tentando PyPDF2...")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(f"=== PÁGINA {page_num} ===\n{text}\n")
                except Exception as page_error:
                    logger.warning(f"Erro ao processar página {page_num} com PyPDF2: {page_error}")
                    continue
                    
        if text_content:
            logger.info(f"PyPDF2 extraiu texto de {len(text_content)} páginas")
                    
        return "\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Erro na extração direta: {e}")
        return ""
    finally:
        # Força limpeza de memória
        import gc
        gc.collect()

def extract_text_ocr(pdf_path: Path, max_pages: int = 1000) -> str:
    """Extrai texto usando OCR (limitado a algumas páginas por performance)."""
    logger.info("Iniciando extração com OCR...")
    text_content = []
    images = None
    
    try:
        images = convert_from_path(pdf_path, dpi=300)
        pages_to_process = min(len(images), max_pages)
        
        logger.info(f"Processando {pages_to_process} páginas com OCR...")
        
        for page_num in range(pages_to_process):
            logger.info(f"OCR - Página {page_num + 1}")
            try:
                text = pytesseract.image_to_string(images[page_num], lang='por')
                if text.strip():
                    text_content.append(f"=== PÁGINA {page_num + 1} ===\n{text}\n")
            except Exception as page_error:
                logger.error(f"Erro ao processar página {page_num + 1} com OCR: {page_error}")
                continue
                
        if len(images) > max_pages:
            text_content.append(f"\n[NOTA: PDF tem {len(images)} páginas, mas apenas {max_pages} foram processadas via OCR]\n")
                
        return "\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Erro na extração OCR: {e}")
        return ""
    finally:
        # Limpa todas as imagens da memória
        if images:
            for img in images:
                if img:
                    try:
                        img.close()
                    except:
                        pass
        
        # Força limpeza de memória
        import gc
        gc.collect()
        logger.info("Recursos de imagem OCR liberados da memória")

def save_text(content: str, output_path: Path) -> None:
    """Salva o texto extraído."""
    logger.info(f"Salvando texto em: {output_path}")
    
    # Limpa caracteres problemáticos que podem causar problemas de encoding
    cleaned_content = content.replace('\x00', '')  # Remove null bytes
    cleaned_content = cleaned_content.replace('\ufeff', '')  # Remove BOM
    
    # Normaliza quebras de linha
    cleaned_content = cleaned_content.replace('\r\n', '\n').replace('\r', '\n')
    
    try:
        # Salva com encoding UTF-8 sem BOM
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(cleaned_content)
        logger.info(f"Arquivo salvo com {len(cleaned_content)} caracteres")
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo: {e}")
        raise

def main():
    if not PDF_PATH.exists():
        logger.error(f"PDF não encontrado: {PDF_PATH}")
        return

    # Estratégia híbrida: tenta extração direta primeiro
    text_content = extract_text_direct(PDF_PATH)
    
    if not text_content.strip():
        logger.info("Extração direta falhou, tentando OCR...")
        text_content = extract_text_ocr(PDF_PATH)
    
    if text_content.strip():
        save_text(text_content, OUTPUT_PATH)
        logger.info("✅ Extração concluída com sucesso!")
        print(f"Texto extraído salvo em: {OUTPUT_PATH}")
    else:
        logger.error("❌ Não foi possível extrair texto do PDF.")

if __name__ == "__main__":
    main()
