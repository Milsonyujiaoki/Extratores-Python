# Importa a biblioteca pdfplumber, ideal para PDFs com estrutura digital (não escaneados)
import pdfplumber

def extrair_com_pdfplumber(caminho_pdf: str, caminho_saida: str):
    """
    Extrai texto de um PDF utilizando `pdfplumber`.

    Parâmetros:
    - caminho_pdf (str): Caminho do PDF de entrada
    - caminho_saida (str): Caminho do arquivo onde o texto será salvo

    Essa biblioteca é ótima para extrair texto já digitalizado, respeitando quebras de linha.
    """
    with pdfplumber.open(caminho_pdf) as pdf, open(caminho_saida, "w", encoding="utf-8") as f:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                f.write(texto + "\n\n")  # Adiciona espaçamento entre páginas

    print(f"[pdfplumber] Texto salvo em: {caminho_saida}")
