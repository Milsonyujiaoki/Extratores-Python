import os
import json
from pathlib import Path

DIRETORIO_RAIZ = r"C:\saida"  # ajuste para o seu caminho real
JSON_SAIDA = r"C:\saida\consolidado_openai_vision.json"

def encontrar_jsons(diretorio_raiz: str):
    for root, _, files in os.walk(diretorio_raiz):
        for file in files:
            if file.endswith('.json'):
                yield Path(root) / file

def extrair_dados_json(path_json: Path):
    try:
        # Verifica se o arquivo está vazio
        if os.path.getsize(path_json) == 0:
            print(f"Arquivo vazio: {path_json}")
            return []
        with open(path_json, encoding="utf-8") as f:
            data = json.load(f)
        cp = path_json.stem
        no_titulo3 = cp.split('_')[-1] if '_' in cp else cp
        linhas = []
        # Suporta tanto dict (com chave 'paginas') quanto lista de páginas diretamente
        if isinstance(data, dict):
            paginas = data.get('paginas', [])
        elif isinstance(data, list):
            paginas = data
        else:
            print(f"JSON não é um dicionário nem lista: {path_json}")
            return []
        for pagina in paginas:
            if not isinstance(pagina, dict):
                continue
            valores = pagina.get("valores_monetarios", {}) if isinstance(pagina.get("valores_monetarios", {}), dict) else {}
            datas = pagina.get("datas", {}) if isinstance(pagina.get("datas", {}), dict) else {}
            nomes = pagina.get("nomes", {}) if isinstance(pagina.get("nomes", {}), dict) else {}
            documentos = pagina.get("documentos", {}) if isinstance(pagina.get("documentos", {}), dict) else {}
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

def consolidar_para_json(diretorio_raiz: str, json_saida: str):
    linhas = []
    for path_json in encontrar_jsons(diretorio_raiz):
        linhas.extend(extrair_dados_json(path_json))
    with open(json_saida, "w", encoding="utf-8") as fout:
        json.dump(linhas, fout, ensure_ascii=False, indent=2)
    print(f"Arquivo consolidado gerado em: {json_saida}")

if __name__ == "__main__":
    consolidar_para_json(DIRETORIO_RAIZ, JSON_SAIDA)
