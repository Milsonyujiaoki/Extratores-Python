import os
import logging
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
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
                PDF_PATH = Path(config.get('Paths', 'PDF_PATH'))
                # Usa OUTPUT_PATH_OCR se existir, senão usa OUTPUT_PATH
                if config.has_option('Paths', 'OUTPUT_PATH_OCR'):
                    OUTPUT_PATH = Path(config.get('Paths', 'OUTPUT_PATH_OCR'))
                else:
                    OUTPUT_PATH = Path(config.get('Paths', 'OUTPUT_PATH'))
                logger.info(f"Configuração carregada com encoding: {encoding}")
                logger.info(f"Arquivo config encontrado em: {config_file}")
                break
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

def extract_text_with_ocr(pdf_path: Path, dpi: int = 300, lang: str = 'por', max_pages: int | None = None) -> str:
    """Extrai texto usando OCR (para PDFs escaneados ou com imagens)."""
    logger.info(f"Extraindo texto com OCR: {pdf_path}")
    text_content = []
    images = None
    
    # Verifica se o arquivo existe antes de tentar processar
    if not pdf_path.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")
    
    # Converte para string com encoding UTF-8 para evitar problemas
    pdf_path_str = str(pdf_path)
    logger.info(f"Caminho do PDF (string): {pdf_path_str}")
    
    try:
        # Converte PDF para imagens
        logger.info("Convertendo PDF para imagens...")
        # Usa o caminho como string para evitar problemas de encoding
        images = convert_from_path(pdf_path_str, dpi=dpi)
        
        total_pages = len(images)
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
        
        logger.info(f"Total de páginas: {total_pages}, processando: {pages_to_process}")
        
        for page_num in range(pages_to_process):
            logger.info(f"Processando página {page_num + 1}/{pages_to_process} com OCR...")
            try:
                # Aplica OCR na imagem
                current_image = images[page_num]
                text = pytesseract.image_to_string(current_image, lang=lang)
                if text.strip():
                    text_content.append(f"=== PÁGINA {page_num + 1} ===\n{text}\n")
                else:
                    logger.warning(f"Página {page_num + 1} não contém texto extraível")
                    
            except Exception as page_error:
                logger.error(f"Erro ao processar página {page_num + 1}: {page_error}")
                continue
                
        if max_pages and total_pages > max_pages:
            text_content.append(f"\n[NOTA: PDF tem {total_pages} páginas, mas apenas {max_pages} foram processadas via OCR]\n")
                
        return "\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Erro ao extrair com OCR: {e}")
        raise
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
        logger.info("Recursos de imagem liberados da memória")

def save_text(content: str, output_path: Path) -> None:
    """Salva o texto extraído no arquivo."""
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
        raise FileNotFoundError(str(PDF_PATH))

    try:
        text_content = extract_text_with_ocr(PDF_PATH)
        
        if text_content.strip():
            save_text(text_content, OUTPUT_PATH)
            logger.info("Extração OCR concluída com sucesso!")
        else:
            logger.warning("Nenhum texto foi extraído via OCR.")
            
    except Exception as e:
        logger.error(f"Erro durante a extração OCR: {e}")
        raise

if __name__ == "__main__":
    main()
