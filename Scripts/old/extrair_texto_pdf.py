from unstructured.partition.pdf import partition_pdf

def extrair_texto_unstructured(caminho_pdf: str, caminho_saida: str):
    elementos = partition_pdf(filename=caminho_pdf)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        for el in elementos:
            f.write(el.text + "\n")


extrair_texto_unstructured(r"C:\Users\Milson Yuji Aoki\OneDrive - Universidade Federal do ABC\Dev_yuji\ACADEMICO\UFABC\2° QUAD\CTS\28.07\Nisia Trindade As ciencias na formação do brasil.pdf", "As ciencias na formacao do brasil - Nisia Trindade.txt")
