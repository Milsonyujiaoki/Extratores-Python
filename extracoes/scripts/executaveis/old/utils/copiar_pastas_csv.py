import csv
import shutil
from pathlib import Path
import os

# Caminhos dos arquivos
csv_path = Path(r"CAMINHO/para/seu_arquivo.csv")  # ajuste para seu arquivo
path_entrada = Path(r"CAMINHO/para/destino")      # ajuste para seu destino

# Lê o CSV e copia as pastas
with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        caminho2 = row.get('caminho2') or row.get('caminho_csv2') or row.get('caminho')
        if caminho2:
            origem = Path(caminho2)
            destino = path_entrada / origem.name
            if destino.exists():
                shutil.rmtree(destino)
            shutil.copytree(origem, destino)
            print(f"Copiado: {origem} -> {destino}")

print("Processo concluído!")
