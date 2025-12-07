import os
import re
from pathlib import Path
import pandas as pd

DIRETORIO_RAIZ = r"C:\saida"   # Ajuste conforme o seu diretório
ARQUIVO_SAIDA_XLSX = r"C:\saida\consolidado_openai_txt.xlsx"
ARQUIVO_SAIDA_CSV  = r"C:\saida\consolidado_openai_txt.csv"

MAPEAMENTO = {
    "CP_":          r"\bCP_?(\d{6,})\b",
    "No. Titulo3":  r"\b(\d{6,})\b",
    "Vlr Título":   [r"valor.?documento", r"valor.?t[ií]tulo", r"valor[ :]*(r?\$ ?)?[\d\.,]+", r"valor total a pagar", r"valor pago"],
    "(-) Descontos": [r"valor.?desconto", r"desconto"],
    "(=) Vlr Devido": [r"valor.?devido", r"valor total a pagar"],
    "Data de Vencimento": [r"vencimento", r"data.?vencimento"],
    "Vencimento Real": [r"vencimento.?real"],
    "Data de Pagamento": [r"pagamento", r"data.?pagamento", r"data de crédito"],
}
RE_VALOR = re.compile(r"R?\$ ?[\d\.,]+")
RE_DATA = re.compile(r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b")

RE_PAGINA = re.compile(r"p[áa]gina[ \t]*(\d+)", re.I)
RE_TIPO_DOC = re.compile(r"tipo.?de.?documento[^\w:]*[:\-–]?\s*([^\n]+)", re.I)

def normaliza_nome(nome_arquivo):
    nome = os.path.splitext(os.path.basename(nome_arquivo))[0]
    nome = re.sub(r"^(openai_json_|openai_vision_)", "", nome, flags=re.I)
    return nome

def extrai_cp_no_titulo3(nome_arquivo):
    nome = normaliza_nome(nome_arquivo)
    m_cp = re.match(r"cp_(\d{6,})", nome, re.I)
    cp = nome if m_cp else ""
    m_titulo = re.search(r"(\d{6,})", nome)
    no_titulo3 = m_titulo.group(1) if m_titulo else ""
    return cp, no_titulo3

def extrai_valor_regex(linha, patterns):
    linha = linha.lower()
    for p in patterns:
        regex = re.compile(p, re.I)
        if regex.search(linha):
            val_monet = RE_VALOR.findall(linha)
            if val_monet:
                return val_monet[0]
            val_data = RE_DATA.findall(linha)
            if val_data:
                return val_data[0]
    return None

def extrai_tipo_doc(linhas_bloco):
    for linha in linhas_bloco:
        m = RE_TIPO_DOC.search(linha)
        if m:
            return m.group(1).strip()
    return None

def processa_txt(path_txt: Path):
    cp, no_titulo3 = extrai_cp_no_titulo3(path_txt.name)
    with open(path_txt, encoding="utf-8") as f:
        linhas = [l.strip() for l in f if l.strip()]
    # Busca blocos por página
    blocos = []
    bloco_atual = []
    pagina_atual = 1
    for linha in linhas:
        m_pag = RE_PAGINA.search(linha)
        if m_pag:
            if bloco_atual:
                blocos.append((pagina_atual, bloco_atual))
                bloco_atual = []
            pagina_atual = int(m_pag.group(1))
        bloco_atual.append(linha)
    if bloco_atual:
        blocos.append((pagina_atual, bloco_atual))
    if not blocos:
        blocos = [(1, linhas)]  # Tudo em 1 página caso não detecte marcador

    linhas_saida = []
    for pag_num, bloco in blocos:
        texto_bloco = " ".join(bloco).lower()
        dados = {"CP_": cp, "No. Titulo3": no_titulo3, "Página": pag_num, "Tipo Documento": extrai_tipo_doc(bloco)}
        for col, patterns in MAPEAMENTO.items():
            if col in ("CP_", "No. Titulo3"):
                continue
            val = None
            # Busca linha a linha dentro do bloco da página
            for linha in bloco:
                val = extrai_valor_regex(linha, patterns if isinstance(patterns, list) else [patterns])
                if val:
                    break
            if not val:
                val = extrai_valor_regex(texto_bloco, patterns if isinstance(patterns, list) else [patterns])
            dados[col] = val
        linhas_saida.append(dados)
    return linhas_saida

def varrer_txts(diretorio_raiz):
    for root, _, files in os.walk(diretorio_raiz):
        for file in files:
            if file.lower().endswith('.txt'):
                yield Path(root) / file

def consolidar_para_excel_e_csv(diretorio_raiz, xlsx_saida, csv_saida):
    todas_linhas = []
    for path_txt in varrer_txts(diretorio_raiz):
        todas_linhas.extend(processa_txt(path_txt))
    df = pd.DataFrame(todas_linhas)
    df.to_excel(xlsx_saida, index=False)
    df.to_csv(csv_saida, index=False, sep=";")
    print(f"Arquivos salvos: {xlsx_saida}, {csv_saida}")

if __name__ == "__main__":
    consolidar_para_excel_e_csv(DIRETORIO_RAIZ, ARQUIVO_SAIDA_XLSX, ARQUIVO_SAIDA_CSV)
