# Importa o módulo time para medir o tempo de execução de cada extrator
import time

# Importa Path para lidar com caminhos de arquivos de forma segura e multiplataforma
from pathlib import Path

# Importa os módulos de extração personalizados, cada um representa uma biblioteca
from extrator import (
    extrator_unstructured,   # Usa a lib unstructured (com OCR, tabelas, etc.)
    extrator_pdfplumber,     # Usa pdfplumber (PDFs com texto digital)
    extrator_pymupdf,        # Usa pymupdf (rápido e simples)
    extrator_tika,           # Usa Apache Tika (OCR leve + metadados)
)

def analisar_saida(caminho_saida: Path):
    """
    Função para calcular o número de linhas e caracteres de um arquivo de saída .txt

    Parâmetros:
    - caminho_saida (Path): caminho do arquivo de saída gerado por um extrator

    Retorna:
    - Tuple[int, int]: número de linhas e número total de caracteres
    """
    try:
        with open(caminho_saida, "r", encoding="utf-8") as f:
            conteudo = f.read()
            num_linhas = conteudo.count("\n")
            tamanho = len(conteudo)
        return num_linhas, tamanho
    except Exception as e:
        return 0, 0  # Em caso de erro, retorna 0 para ambos os valores

def main():
    # Caminho do PDF a ser processado (pode ser ajustado conforme sua organização)
    caminho_pdf = Path(r"Dev_yuji\ACADEMICO\UFABC\2° QUAD\BECM\2 - Andre Comte Spoville\André Comte-Sponville.pdf")

    # Dicionário de extratores: nome (str) → função de extração correspondente
    extratores = {
        "unstructured": extrator_unstructured.extrair_com_unstructured,
        "pdfplumber": extrator_pdfplumber.extrair_com_pdfplumber,
        "pymupdf": extrator_pymupdf.extrair_com_pymupdf,
        "tika": extrator_tika.extrair_com_tika,
    }

    # Dicionário que irá armazenar os resultados de cada extrator
    resultados = {}

    # Loop para executar cada extrator e medir seu desempenho
    for nome, funcao_extracao in extratores.items():
        saida_txt = Path(f"saida_{nome}.txt")  # Nome do arquivo de saída
        print(f"🔍 Iniciando extração com {nome}...")

        try:
            # Medição de tempo de execução
            inicio = time.time()
            funcao_extracao(str(caminho_pdf), str(saida_txt))
            fim = time.time()

            # Análise do conteúdo extraído
            linhas, tamanho = analisar_saida(saida_txt)

            # Armazena os resultados para comparação final
            resultados[nome] = {
                "tempo": round(fim - inicio, 2),
                "linhas": linhas,
                "tamanho": tamanho,
                "arquivo": saida_txt
            }

        except Exception as e:
            # Armazena erro se a extração falhar
            resultados[nome] = {"erro": str(e)}
            print(f"❌ Erro ao extrair com {nome}: {e}")

    # Impressão dos resultados comparativos
    print("\n📊 RESULTADOS:")
    for nome, resultado in resultados.items():
        if "erro" in resultado:
            print(f"- {nome}: ❌ ERRO: {resultado['erro']}")
        else:
            print(f"- {nome}: ✅ {resultado['tempo']}s | {resultado['linhas']} linhas | {resultado['tamanho']} caracteres | -> {resultado['arquivo']}")

# Ponto de entrada principal
if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-