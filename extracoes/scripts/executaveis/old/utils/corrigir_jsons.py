import os
import json
from pathlib import Path

DIRETORIO_RAIZ = r"C:\saida"  # ajuste para o seu caminho real
PASTA_SAIDA = r"C:\saida\json_corrigidos"  # onde salvar os arquivos corrigidos

os.makedirs(PASTA_SAIDA, exist_ok=True)

def encontrar_jsons(diretorio_raiz: str):
    for root, _, files in os.walk(diretorio_raiz):
        for file in files:
            if file.endswith('.json'):
                yield Path(root) / file

def tentar_carregar_json(path_json: Path):
    try:
        with open(path_json, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def corrigir_json_texto(texto: str) -> str:
    # Troca ponto e vírgula por vírgula
    texto = texto.replace(';', ',')
    # Troca aspas simples por aspas duplas (cuidado: pode gerar problemas se o texto for "sujo")
    texto = texto.replace("'", '"')
    # Remove quebras de linha desnecessárias
    texto = texto.replace('\r', '').replace('\n', '\n')
    # Remove vírgulas duplicadas
    while ',,' in texto:
        texto = texto.replace(',,', ',')
    # Remove vírgula antes de fechar colchete/chave
    texto = texto.replace(',]', ']').replace(',}', '}')
    return texto

def processar_arquivos(diretorio_raiz: str, pasta_saida: str):
    for path_json in encontrar_jsons(diretorio_raiz):
        data = tentar_carregar_json(path_json)
        if data is not None:
            # Já está OK, copia para pasta de saída
            destino = Path(pasta_saida) / path_json.name
            with open(destino, 'w', encoding='utf-8') as fout:
                json.dump(data, fout, ensure_ascii=False, indent=2)
            print(f"Arquivo já válido: {path_json}")
            continue
        # Se não conseguiu carregar, tenta corrigir
        with open(path_json, encoding="utf-8") as f:
            texto = f.read()
        texto_corrigido = corrigir_json_texto(texto)
        try:
            data_corrigida = json.loads(texto_corrigido)
            destino = Path(pasta_saida) / path_json.name
            with open(destino, 'w', encoding='utf-8') as fout:
                json.dump(data_corrigida, fout, ensure_ascii=False, indent=2)
            print(f"Corrigido: {path_json}")
        except Exception as e:
            print(f"Falha ao corrigir {path_json}: {e}")

if __name__ == "__main__":
    processar_arquivos(DIRETORIO_RAIZ, PASTA_SAIDA)
