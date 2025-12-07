import os
import logging
from pathlib import Path
import pdfplumber
import PyPDF2
import configparser
# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Caminhos fixos (editáveis) ===
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
                OUTPUT_PATH = Path(config.get('Paths', 'OUTPUT_PATH_DIRECT'))
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
def extract_text_with_pdfplumber(pdf_path: Path) -> str:
    """Extrai texto usando pdfplumber (melhor para layouts complexos)."""
    logger.info(f"Extraindo texto com pdfplumber: {pdf_path}")
    text_content = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Processando página {page_num}")
                text = page.extract_text()
                if text:
                    text_content.append(f"=== PÁGINA {page_num} ===\n{text}\n")
        
        return "\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Erro ao extrair com pdfplumber: {e}")
        raise
    finally:
        # Força limpeza de memória para PDFs grandes
        import gc
        gc.collect()

def extract_text_with_pypdf2(pdf_path: Path) -> str:
    """Extrai texto usando PyPDF2 (mais rápido para PDFs simples)."""
    logger.info(f"Extraindo texto com PyPDF2: {pdf_path}")
    text_content = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                logger.info(f"Processando página {page_num}")
                text = page.extract_text()
                if text:
                    text_content.append(f"=== PÁGINA {page_num} ===\n{text}\n")
        
        return "\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Erro ao extrair com PyPDF2: {e}")
        raise
    finally:
        # Força limpeza de memória para PDFs grandes
        import gc
        gc.collect()

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
        # Tenta primeiro com pdfplumber (melhor qualidade)
        logger.info("Tentando extração com pdfplumber...")
        text_content = extract_text_with_pdfplumber(PDF_PATH)
        
        if not text_content.strip():
            # Se pdfplumber não funcionar, tenta PyPDF2
            logger.info("pdfplumber não extraiu texto, tentando PyPDF2...")
            text_content = extract_text_with_pypdf2(PDF_PATH)
            
        if text_content.strip():
            save_text(text_content, OUTPUT_PATH)
            logger.info("Extração concluída com sucesso!")
        else:
            logger.warning("Nenhum texto foi extraído do PDF.")
            
    except Exception as e:
        logger.error(f"Erro durante a extração: {e}")
        raise

if __name__ == "__main__":
    main()
