import os
import re
import json
from pathlib import Path
import pandas as pd
import unicodedata

DIRETORIO_RAIZ = r"C:\saida"
ARQUIVO_SAIDA_XLSX = r"C:\saida\consolidado_openai_vision.xlsx"
ARQUIVO_SAIDA_CSV  = r"C:\saida\consolidado_openai_vision.csv"

COLUNAS_EXCEL = {
    "CP_":          r"^CP_(\d+)",  # Regex do nome do arquivo
    "No. Titulo3":  r"(\d{6,})",   # parte numérica do nome
    "Vlr Título":   ["valor_documento", "valor_do_documento", "valor", "valor documento", "valor do documento", "valor total a pagar", "valor total", "valor pago"],
    "(-) Descontos": ["valor_desconto", "desconto","valor desconto", "desconto aplicado"],
    "(=) Vlr Devido": ["valor_total_a_pagar", "valor_devido", "valor total a pagar", "valor devido"],
    "Data de Vencimento": ["vencimento", "data_vencimento", "vencimento_real","data_de_vencimento", "data vencimento", "data de vencimento"],
    "Vencimento Real": ["vencimento_real"],
    "Data de Pagamento": ["pagamento", "data_pagamento", "data_de_pagamento", "data pagamento", "data de pagamento", "Data de crédito"],
}

def normaliza_nome(nome_arquivo):
    nome = os.path.splitext(os.path.basename(nome_arquivo))[0]
    nome = re.sub(r"^(openai_json_|openai_vision_)", "", nome)
    return nome

def extrai_cp_no_titulo3(nome_arquivo):
    nome = normaliza_nome(nome_arquivo)
    m_cp = re.match(r"CP_(\d+)", nome)
    cp = nome if m_cp else ""  # Só preenche CP_ se houver no nome
    no_titulo3 = nome
    return cp, no_titulo3

def normaliza_texto(txt):
    # Remove acentos e converte para minúsculo
    return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode().lower()

def extrai_valor_de_texto(linhas_texto, chaves):
    chaves = [normaliza_texto(c) for c in chaves]
    for linha in linhas_texto:
        linha_norm = normaliza_texto(linha.strip())
        for chave in chaves:
            # Regex atualizado: pega valor após chave: ou =, com/sem aspas, pega números, frases, valores monetários, etc
            regex = re.compile(
                rf'["\']?{re.escape(chave)}["\']?\s*[:=]\s*["\']?([^"\',\n]+)',
                re.IGNORECASE
            )
            m = regex.search(linha_norm)
            if m:
                return m.group(1).strip()
    return None
def extrai_valor_de_dict(d: dict, chaves):
    # Normaliza todas as chaves do dicionário para minúsculo em uma cópia temporária
    d_norm = {k.lower(): v for k, v in d.items()}
    for chave in chaves:
        if chave.lower() in d_norm:
            return d_norm[chave.lower()]
    return None

def carrega_json_robusto(path_json: Path):
    try:
        with open(path_json, encoding="utf-8") as f:
            texto = f.read()
        texto = re.sub(r',\s*([\]}])', r'\1', texto)
        if texto.count("'") > texto.count('"'):
            texto = texto.replace("'", '"')
        texto = re.sub(r'//.*?\n|/\*.*?\*/', '', texto, flags=re.DOTALL)
        return json.loads(texto)
    except Exception as e:
        print(f"[ERRO JSON] {path_json}: {e}")
        return None

def processa_json(path_json: Path):
    linhas = []
    data = carrega_json_robusto(path_json)
    if data is None:
        print(f"Arquivo pulado: {path_json}")
        return []
    cp, no_titulo3 = extrai_cp_no_titulo3(path_json.name)
    paginas = []
    if isinstance(data, dict):
        paginas = data.get("paginas") or [data]
    elif isinstance(data, list):
        paginas = data
    else:
        return []
    for pagina in paginas:
        linha = {"CP_": cp, "No. Titulo3": no_titulo3}
        valores = pagina.get("valores_monetarios", {}) if isinstance(pagina.get("valores_monetarios", {}), dict) else {}
        datas = pagina.get("datas", {}) if isinstance(pagina.get("datas", {}), dict) else {}
        for col, sin_list in COLUNAS_EXCEL.items():
            if col in ("CP_", "No. Titulo3"):
                continue
            if "Descontos" in col:
                val = extrai_valor_de_dict(valores, sin_list)
            elif "Vlr" in col:
                val = extrai_valor_de_dict(valores, sin_list)
            elif "Data" in col or "Vencimento" in col:
                val = extrai_valor_de_dict(datas, sin_list)
            else:
                val = extrai_valor_de_dict(pagina, sin_list)
            if val is None:
                val = extrai_valor_de_dict(pagina, sin_list)
            linha[col] = val
        linhas.append(linha)
    return linhas


def processa_txt(path_txt: Path):
    with open(path_txt, encoding="utf-8") as f:
        linhas_arquivo = f.readlines()
    cp, no_titulo3 = extrai_cp_no_titulo3(path_txt.name)
    linha = {"CP_": cp, "No. Titulo3": no_titulo3}
    for col, sin_list in COLUNAS_EXCEL.items():
        if col in ("CP_", "No. Titulo3"):
            continue
        # Procura o valor na lista de sinonimos/regex
        val = extrai_valor_de_texto(linhas_arquivo, sin_list)
        linha[col] = val
    return [linha]

def varrer_arquivos(diretorio_raiz):
    for root, _, files in os.walk(diretorio_raiz):
        for file in files:
            if file.endswith('.json') or file.endswith('.txt'):
                yield Path(root) / file

def consolidar_para_excel_e_csv(diretorio_raiz, xlsx_saida, csv_saida):
    todas_linhas = []
    for path_arquivo in varrer_arquivos(diretorio_raiz):
        if path_arquivo.suffix.lower() == '.json':
            todas_linhas.extend(processa_json(path_arquivo))
        elif path_arquivo.suffix.lower() == '.txt':
            todas_linhas.extend(processa_txt(path_arquivo))
    df = pd.DataFrame(todas_linhas)
    df.to_excel(xlsx_saida, index=False)
    df.to_csv(csv_saida, index=False, sep=";")
    print(f"Arquivos salvos: {xlsx_saida}, {csv_saida}")

if __name__ == "__main__":
    consolidar_para_excel_e_csv(DIRETORIO_RAIZ, ARQUIVO_SAIDA_XLSX, ARQUIVO_SAIDA_CSV)
