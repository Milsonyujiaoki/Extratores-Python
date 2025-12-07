import csv
from pathlib import Path
from typing import Union

def comparar_csvs_faltantes(
    path_csv_fonte: Union[str, Path],
    path_csv_comparacao: Union[str, Path],
    path_csv_saida: Union[str, Path],
    coluna_nome: str = "nome"
) -> int:
    """
    Compara o CSV de fonte com qualquer outro CSV (comparacao) e salva em path_csv_saida
    apenas os registros da fonte que NÃO estão no CSV de comparacao, comparando pela coluna 'nome'.
    Retorna o número de registros salvos.
    """
    path_csv_fonte = Path(path_csv_fonte)
    path_csv_comparacao = Path(path_csv_comparacao)
    path_csv_saida = Path(path_csv_saida)

    # Carrega nomes do CSV de comparação
    nomes_comparacao = set()
    with open(path_csv_comparacao, newline='', encoding="utf-8") as f_comp:
        reader_comp = csv.DictReader(f_comp)
        for row in reader_comp:
            nome = row.get(coluna_nome)
            if nome:
                nomes_comparacao.add(nome)

    # Filtra registros da fonte que não estão no CSV de comparação
    registros_faltantes = []
    with open(path_csv_fonte, newline='', encoding="utf-8") as f_fonte:
        reader_fonte = csv.DictReader(f_fonte)
        for row in reader_fonte:
            nome = row.get(coluna_nome)
            if nome and nome not in nomes_comparacao:
                registros_faltantes.append(row)

    # Salva resultado em CSV saída
    if registros_faltantes:
        with open(path_csv_saida, "w", newline='', encoding="utf-8") as f_saida:
            writer = csv.DictWriter(f_saida, fieldnames=reader_fonte.fieldnames)
            writer.writeheader()
            for row in registros_faltantes:
                writer.writerow(row)
    else:
        # Cria arquivo vazio com cabeçalho
        with open(path_csv_saida, "w", newline='', encoding="utf-8") as f_saida:
            writer = csv.DictWriter(f_saida, fieldnames=reader_fonte.fieldnames)
            writer.writeheader()
    return len(registros_faltantes)

if __name__ == "__main__":
    # Exemplo de uso
    fonte = r"C:\fonte\csv_fonte.csv"
    comparacao = r"C:\Marimex - Doc's completos\Processados\csv_processados.csv"  # pode ser qualquer csv
    saida = r"C:\saida\csv_saida.csv"
    total = comparar_csvs_faltantes(fonte, comparacao, saida)
    print(f"Registros faltantes salvos em {saida}: {total}")
