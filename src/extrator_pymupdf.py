import fitz  # PyMuPDF

def extrair_com_pymupdf(caminho_pdf: str, caminho_saida: str):
    """
    Extrai texto de um PDF usando a biblioteca PyMuPDF (fitz).

    Parâmetros:
    - caminho_pdf (str): Caminho do arquivo PDF de entrada.
    - caminho_saida (str): Caminho do arquivo de texto de saída.
    """
    try:
        with fitz.open(caminho_pdf) as doc:
            with open(caminho_saida, "w", encoding="utf-8") as f:
                for pagina in doc:
                    texto = pagina.get_text("text")  # type: ignore
                    f.write(texto + "\n\n")
        print(f"[pymupdf] Texto salvo em: {caminho_saida}")
    except Exception as e:
        print(f"[Erro] Falha ao processar o PDF: {e}")
