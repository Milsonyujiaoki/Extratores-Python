# Importa a função principal de particionamento da biblioteca unstructured
# Essa função realiza a extração de textos de PDFs, podendo lidar com OCR e estruturas complexas
from unstructured.partition.pdf import partition_pdf
from pathlib import Path  # Para lidar com caminhos de forma robusta e multiplataforma

def extrair_com_unstructured(caminho_pdf: str, caminho_saida: str):
    """
    Extrai texto de um PDF usando a biblioteca `unstructured`.

    Parâmetros:
    - caminho_pdf (str): Caminho do arquivo PDF a ser processado
    - caminho_saida (str): Caminho onde o texto extraído será salvo

    Essa função usa `partition_pdf()` para dividir o PDF em elementos de texto.
    Cada elemento pode representar parágrafos, títulos, listas, etc.
    """
    pdf_path = Path(caminho_pdf)

    # Verifica se o arquivo existe
    if not pdf_path.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {caminho_pdf}")

    # Extrai os elementos do PDF usando o Unstructured
    elementos = partition_pdf(filename=str(pdf_path))

    # Salva o conteúdo extraído em um .txt
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for i, el in enumerate(elementos):
            if hasattr(el, 'text'):  # Garante que o elemento tem conteúdo textual
                f.write(f"\n--- Elemento {i+1} ---\n{el.text}\n")

    print(f"[unstructured] Texto salvo em: {caminho_saida}")
