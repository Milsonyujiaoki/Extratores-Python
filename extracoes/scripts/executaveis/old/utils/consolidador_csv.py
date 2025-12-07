import os
import json
import csv
from pathlib import Path

# Defina o diretório principal a ser varrido
DIRETORIO_RAIZ = r"C:\saida"  # Altere para o seu caminho real
CSV_SAIDA = r"C:\saida\consolidado_openai_vision.csv"

# Campos do Excel (ajuste conforme necessidade)
COLUNAS = [
    "CP_", "No. Titulo3",
    "Vlr Titulo", "Vlr Pago", "Vlr Total a Pagar",
    "Data de Vencimento", "Data de Emissao", "Data de Pagamento", "Data de Processamento",
    "Emitente", "Destinatario", "Nosso Numero", "Numero Documento", "Fatura", "Observacao"
]

def encontrar_jsons(diretorio_raiz: str):
    """Varre todos os subdiretórios procurando arquivos .json."""
    for root, _, files in os.walk(diretorio_raiz):
        for file in files:
            if file.endswith('.json'):
                yield Path(root) / file

def extrair_dados_json(path_json: Path):
    """Extrai os dados estruturados de cada JSON no padrão solicitado."""
    try:
        with open(path_json, encoding="utf-8") as f:
            data = json.load(f)
        # Tenta identificar CP e No. Titulo3 pelo nome do arquivo/pasta
        cp = path_json.stem
        no_titulo3 = cp.split('_')[-1] if '_' in cp else cp
        linhas = []
        for pagina in data.get('paginas', []):
            valores = pagina.get("valores_monetarios", {})
            datas = pagina.get("datas", {})
            nomes = pagina.get("nomes", {})
            documentos = pagina.get("documentos", {})

            linha = {
                "CP_": cp,
                "No. Titulo3": no_titulo3,
                "Vlr Titulo": valores.get("valor_documento"),
                "Vlr Pago": valores.get("valor_pago"),
                "Vlr Total a Pagar": valores.get("valor_total_a_pagar"),
                "Data de Vencimento": datas.get("vencimento"),
                "Data de Emissao": datas.get("emissao"),
                "Data de Pagamento": datas.get("pagamento"),
                "Data de Processamento": datas.get("processamento"),
                "Emitente": nomes.get("emitente") or nomes.get("empresa"),
                "Destinatario": nomes.get("destinatario") or nomes.get("avaliador"),
                "Nosso Numero": documentos.get("nosso_numero"),
                "Numero Documento": documentos.get("numero_documento"),
                "Fatura": documentos.get("fatura"),
                "Observacao": pagina.get("tipo_documento")
            }
            linhas.append(linha)
        return linhas
    except Exception as e:
        print(f"Erro ao processar {path_json}: {e}")
        return []

def consolidar_para_csv(diretorio_raiz: str, csv_saida: str):
    """Varre diretórios, lê JSONs, extrai dados e salva no CSV consolidado."""
    with open(csv_saida, "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=COLUNAS)
        writer.writeheader()
        for path_json in encontrar_jsons(diretorio_raiz):
            linhas = extrair_dados_json(path_json)
            for linha in linhas:
                writer.writerow(linha)
    print(f"Arquivo consolidado gerado em: {csv_saida}")

if __name__ == "__main__":
    consolidar_para_csv(DIRETORIO_RAIZ, CSV_SAIDA)
