import csv
from pathlib import Path

# Caminhos dos arquivos CSV
path_csv_1 = Path(r"Caminho/para/path_csv_1.csv")  # ajuste para o seu caminho real
path_csv_2 = Path(r"Caminho/para/path_csv_2.csv")  # ajuste para o seu caminho real
path_csv_saida = Path(r"Caminho/para/resultado_comparacao.csv")  # arquivo de saídas

# Carrega registros do primeiro CSV (nome, caminho)
registros_1 = {}
with open(path_csv_1, newline='', encoding='utf-8') as f1:
    reader1 = csv.DictReader(f1)
    for row in reader1:
        registros_1[row['nome']] = row['caminho']

# Carrega registros do segundo CSV (nome, caminho)
registros_2 = {}
with open(path_csv_2, newline='', encoding='utf-8') as f2:
    reader2 = csv.DictReader(f2)
    for row in reader2:
        registros_2[row['nome']] = row['caminho']

# Compara nomes do primeiro com o segundo CSV e salva resultado
with open(path_csv_saida, 'w', newline='', encoding='utf-8') as fout:
    writer = csv.writer(fout)
    writer.writerow(['nome', 'caminho_csv1', 'caminho_csv2'])
    for nome, caminho1 in registros_1.items():
        caminho2 = registros_2.get(nome, '')
        writer.writerow([nome, caminho1, caminho2])

print(f"Arquivo de comparação gerado: {path_csv_saida}")
