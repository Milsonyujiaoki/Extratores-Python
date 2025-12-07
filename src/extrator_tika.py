# Apache Tika usa Java por baixo dos panos e suporta metadados + OCR básico
from tika import parser

def extrair_com_tika(caminho_pdf: str, caminho_saida: str):
    """
    Extrai texto usando `Apache Tika`, baseado em Java.

    Parâmetros:
    - caminho_pdf (str): Caminho do PDF
    - caminho_saida (str): Caminho do arquivo de texto

    Tika pode lidar com PDFs com OCR simples ou embutido e extrair metadados.
    """
    result = parser.from_file(str(caminho_pdf))
    if isinstance(result, tuple):
        status, parsed = result
    else:
        parsed = result

    # "get" protege contra KeyError caso 'content' não esteja presente
    if not isinstance(parsed, dict):
        raise ValueError("O resultado do parser.from_file não é um dicionário. Verifique se o arquivo foi lido corretamente.")
    texto = parsed.get("content", "") or ""
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(texto.strip())

    print(f"[tika] Texto salvo em: {caminho_saida}")
