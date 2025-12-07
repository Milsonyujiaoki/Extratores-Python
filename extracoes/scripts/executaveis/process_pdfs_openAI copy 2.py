from calendar import c

from http import client
from pathlib import Path
import logging
import sys
import datetime
import configparser
import os
import csv
import asyncio
import json
import aiofiles
import base64
import shutil
from typing import Any, Dict, List, Tuple, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from openai import OpenAI,api_key
import path
from pdf2image import convert_from_path
import tempfile
import glob

logger = logging.getLogger(__name__)



def carregar_configuracoes():
    """
    Carrega as configurações do arquivo config.ini.
    """
    config = configparser.ConfigParser()
    config_file = Path(r"C:\Users\Maoki\Dev_yuji\Projetos\extracoes\scripts\executaveis\config_process_pdfs.ini")
    
    if not config_file.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_file}")
    
    config.read(config_file)
    
    return config

def configurar_logger(config):
    """
    Configura o logger para registrar mensagens em um arquivo com timestamp.
    """
    try:
        log_dir = Path(config.get("Paths", "PATH_LOGS"))
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"Process_pdfs_{timestamp}.log"

        formato = "%(asctime)s - %(levelname)s - %(message)s"

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format=formato,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(formato))
        logger = logging.getLogger("process_pdfs_openAI")
        logger.addHandler(console_handler)
        return logger
    except Exception as e:
        logging.error(f"Erro ao configurar o logger: {e}")
        raise e

def iniciando_configuracoes():
    logger = None
    try:
        # Carrega as configurações
        config = carregar_configuracoes()
        logger = configurar_logger(config)
        logger.info(f"[MAIN.CONFIG] Configurações carregadas: {config}")
        # Log de informações do ambiente
        logger.info(f"[MAIN.AMBIENTE] Executável Python: {sys.executable}")
        logger.info(f"[MAIN.AMBIENTE] Argumentos: {sys.argv}")
        logger.info(f"[MAIN.AMBIENTE] Diretório de trabalho: {os.getcwd()}")
        logger.info(f"[MAIN.AMBIENTE] Versão do Python: {sys.version}")
        logger.info("[MAIN] Iniciando o processamento de PDFs com OpenAI Vision v3.")

        # Verifica se o diretório de entrada existe
        diretorio_entrada = config.get("Paths", "PATH_ENTRADA")
        if not Path(diretorio_entrada).exists():
            logger.error(f"[MAIN] Diretório de entrada não encontrado: {diretorio_entrada}")
            raise FileNotFoundError(f"Diretório de entrada não encontrado: {diretorio_entrada}")

        # Verifica se o diretório de saída existe, se não, cria-o
        diretorio_saida = config.get("Paths", "PATH_SAIDA")
        if not Path(diretorio_saida).exists():
            logger.info(f"[MAIN] Diretório de saída não encontrado, criando: {diretorio_saida}")
            Path(diretorio_saida).mkdir(parents=True, exist_ok=True)
            raise FileNotFoundError(f"Diretório de saída não encontrado: {diretorio_saida}")
        return logger, config

    except Exception as e:
        if logger:
            logger.error(f"[MAIN] Erro ao iniciar o processamento: {e}")
        else:
            logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
            logging.error(f"[MAIN] Erro ao iniciar o processamento: {e}")

def listar_pdfs_hibrido(root: Path, max_workers: int = 4) -> list[Path]:
    """ Busca recursiva de arquivos XML usando os.scandir e multithreading.
        Como funciona:
            Só paraleliza o primeiro nível de subdiretórios (diretamente sob root).
            Cada thread faz uma varredura recursiva (com os.scandir) em sua subpasta, mas a recursão interna é sequencial.
            O diretório raiz é varrido sequencialmente para identificar subpastas e arquivos.
        Vantagem:
            Reduz drasticamente o overhead de threads: só há uma thread por subpasta do primeiro nível.
            Cada thread faz uso máximo do disco em sua subárvore, aproveitando o I/O paralelo do storage moderno.
            Mais simples, menos risco de race condition.
        Desvantagem:
            Se o diretório raiz tiver poucos subdiretórios grandes, o paralelismo é limitado ao número de subpastas.
            Se toda a estrutura estiver em um único nível, o ganho é pequeno.    
    """

    logger.info(f"[MAIN.LISTAGEM_HIBRIDA] Iniciando a varredura de PDFs no diretório: {root}")
    logger.info(f"[MAIN.LISTAGEM_HIBRIDA] Usando {max_workers} threads para varredura de subdiretórios.")

    def scan_dir(p: Path):
        arquivos = []
        try:
            for entry in os.scandir(p):
                if entry.is_file() and entry.name.lower().endswith('.pdf'):
                    arquivos.append(Path(entry.path))
                elif entry.is_dir():
                    arquivos.extend(scan_dir(Path(entry.path)))
        except Exception as e:
            logger.warning(f"[MAIN.LISTAGEM_HIBRIDA.SCAN_DIR] Erro ao acessar {p}: {e}")
        return arquivos

    arquivos_pdfs = []
    subdirs = [Path(entry.path) for entry in os.scandir(root) if entry.is_dir()]
    arquivos_pdfs.extend([Path(entry.path) for entry in os.scandir(root) if entry.is_file() and entry.name.lower().endswith('.pdf')])

    subdiretorios_verificados = len(subdirs)
    total_verificados = len(arquivos_pdfs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_dir, subdir): subdir for subdir in subdirs}
        for f in as_completed(futures):
            arquivos_pdfs.extend(f.result())
            total_verificados += len(f.result())

    logger.info(f"[MAIN.LISTAGEM_HIBRIDA] Total de arquivos verificados: {total_verificados}, subdiretórios verificados: {subdiretorios_verificados}")
    return arquivos_pdfs, subdirs

def listar_txts_jsons_hibrido(root: Path, max_workers: int = 4) -> list[Path]:
    """ Busca recursiva de arquivos TXT e JSON usando os.scandir e multithreading.
        Funciona de forma semelhante à função listar_pdfs_hibrido, mas busca arquivos com extensões .txt e .json.
    """
    logger.info(f"[MAIN.LISTAGEM_HIBRIDA] Iniciando a varredura de TXT e JSON no diretório: {root}")
    logger.info(f"[MAIN.LISTAGEM_HIBRIDA] Usando {max_workers} threads para varredura de subdiretórios.")

    def scan_dir(p: Path):
        arquivos = []
        try:
            for entry in os.scandir(p):
                if entry.is_file() and (entry.name.lower().endswith('.txt') or entry.name.lower().endswith('.json')):
                    arquivos.append(Path(entry.path))
                elif entry.is_dir():
                    arquivos.extend(scan_dir(Path(entry.path)))
        except Exception as e:
            logger.warning(f"[MAIN.LISTAGEM_HIBRIDA.SCAN_DIR] Erro ao acessar {p}: {e}")
        return arquivos

    arquivos_txt_json = []
    subdirs = [Path(entry.path) for entry in os.scandir(root) if entry.is_dir()]
    arquivos_txt_json.extend([Path(entry.path) for entry in os.scandir(root) if entry.is_file() and (entry.name.lower().endswith('.txt') or entry.name.lower().endswith('.json'))])

    subdiretorios_verificados = len(subdirs)
    total_verificados = len(arquivos_txt_json)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_dir, subdir): subdir for subdir in subdirs}
        for f in as_completed(futures):
            arquivos_txt_json.extend(f.result())
            total_verificados += len(f.result())

    logger.info(f"[MAIN.LISTAGEM_HIBRIDA] Total de arquivos verificados: {total_verificados}, subdiretórios verificados: {subdiretorios_verificados}")
    return arquivos_txt_json, subdirs

def gerar_csv_arquivos_pdfs(arquivos_pdfs: List[Path], subdirs: List[Path],path_csv: Path):
    """ Salva todos os arquivos PDF encontrados em um arquivo CSV (um por linha) """
    try:
        if not arquivos_pdfs:
            logger.warning("[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Nenhum arquivo PDF encontrado.")
            return

        # Carrega registros existentes do CSV, se houver, para evitar duplicatas
        registros_existentes = set()
        if path_csv.exists():
            try:
                with open(path_csv, newline='', encoding="utf-8") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        nome = row.get("nome")
                        caminho_arquivo = row.get("caminho_arquivo")
                        caminho_subdir = row.get("caminho_subdir")
                        if nome and caminho_arquivo and caminho_subdir:
                            registros_existentes.add((nome, caminho_arquivo, caminho_subdir))
            except Exception as e:
                logger.warning(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Erro ao ler CSV existente: {e}")

        # Mapeia subdirs para busca rápida
        subdir_map = {subdir.name: str(subdir) for subdir in subdirs}

        # Evita duplicidade usando um set de tuplas (nome, caminho_arquivo, caminho_subdir)
        registros_novos = set()
        for pdf in arquivos_pdfs:
            nome = pdf.name
            caminho_arquivo = str(pdf)
            caminho_subdir = subdir_map.get(pdf.parent.name, str(pdf.parent))
            registros_novos.add((nome, caminho_arquivo, caminho_subdir))

        # Junta os registros existentes e novos, removendo duplicatas
        registros_unicos = registros_existentes.union(registros_novos)

        with open(path_csv, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["nome", "caminho_arquivo", "caminho_subdir"])
            for nome, caminho_arquivo, caminho_subdir in sorted(registros_unicos):
                writer.writerow([nome, caminho_arquivo, caminho_subdir])
    except Exception as e:
        logger.error(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Erro ao salvar CSV: {e}")
        raise e
    logger.info(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Total de arquivos PDF registrados (sem duplicidade): {len(registros_unicos)}")

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
    try:
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
        logger.info(f"[MAIN.COMPARAR_CSVS_FALTANTES] Registros faltantes salvos em {path_csv_saida}: {len(registros_faltantes)}")
    except Exception as e:
        logger.error(f"[MAIN.COMPARAR_CSVS_FALTANTES] Erro ao comparar CSVs: {e}")
        raise e

def gerar_csv_manter_diretorios(path_entrada: Path, path_csv_entrada: Path):
    try:
        arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_entrada, max_workers=4)
        # Evita duplicidade pelo nome do subdiretório
        subdirs_unicos = set()
        counter = 0
        with open(path_csv_entrada, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["nome", "caminho"])
            for subdir in subdirs:
                nome = subdir.name
                caminho = str(subdir)
                if nome not in subdirs_unicos:
                    writer.writerow([nome, caminho])
                    subdirs_unicos.add(nome)
                    counter += 1
        logger.info(f"[MAIN] Total de subdiretórios registrados (sem duplicidade): {counter}")
        
    
    except Exception as e:
        logger.error(f"[MAIN.GERAR_CSV_MANUTENCAO_DIRETORIOS] Erro ao gerar CSV para manter diretórios: {e}")
        raise e

def mover_pastas_csv(path_csv: Path, path_entrada: Path):
    """
    Lê um CSV e copia as pastas especificadas para o diretório de entrada.
    """
    try:
        if not path_csv.exists():
            logger.error(f"[MAIN.MOVER_PASTAS_CSV] Arquivo CSV não encontrado: {path_csv}")
            return

        if not path_entrada.exists():
            logger.error(f"[MAIN.MOVER_PASTAS_CSV] Diretório de entrada não encontrado: {path_entrada}")
            return

        # Lê o CSV e copia as pastas
        with open(path_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            contador = 0
            for row in reader:
                caminho2 = row.get('caminho2') or row.get('caminho_csv2') or row.get('caminho')
                if caminho2:
                    origem = Path(caminho2)
                    destino = path_entrada / origem.name
                    if destino.exists():
                        shutil.rmtree(destino)
                    shutil.copytree(origem, destino)
                    contador += 1
                    #logger.info(f"[MAIN.MOVER_PASTAS_CSV] Copiado: {origem} -> {destino}")
        logger.info(f"[MAIN.MOVER_PASTAS_CSV] Total de pastas copiadas: {contador}")
        logger.info("[MAIN.MOVER_PASTAS_CSV] Processo concluído!")
    except Exception as e:
        logger.error(f"[MAIN.MOVER_PASTAS_CSV] Erro ao mover pastas: {e}")
        raise e

def remover_pastas_csv(path_csv: Path, path_entrada: Path):
    """
    Remove todas as pastas do diretório de entrada cujo nome NÃO está na coluna 'nome' do CSV.
    """
    try:
        if not path_csv.exists():
            logger.error(f"[MAIN.REMOVER_PASTAS_CSV] Arquivo CSV não encontrado: {path_csv}")
            return

        if not path_entrada.exists():
            logger.error(f"[MAIN.REMOVER_PASTAS_CSV] Diretório de entrada não encontrado: {path_entrada}")
            return

        # Lê o CSV e obtém os nomes permitidos
        with open(path_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            nomes_permitidos = set(row.get('nome') for row in reader if row.get('nome'))

        contador = 0
        # Percorre todas as pastas do diretório de entrada
        for item in path_entrada.iterdir():
            if item.is_dir() and item.name not in nomes_permitidos:
                shutil.rmtree(item)
                contador += 1
                #logger.info(f"[MAIN.REMOVER_PASTAS_CSV] Removido: {item}")
        logger.info(f"[MAIN.REMOVER_PASTAS_CSV] Total de pastas removidas: {contador}")
        logger.info("[MAIN.REMOVER_PASTAS_CSV] Processo concluído!")
    except Exception as e:
        logger.error(f"[MAIN.REMOVER_PASTAS_CSV] Erro ao remover pastas: {e}")
        raise e

def encode_image_to_base64(image_path):
    """Converte imagem para base64 para enviar à API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def limpar_artefatos_pdf2image(temp_dir, extensoes=(".ppm", ".pbm", ".jpg", ".jpeg"), logger=None):
    total_removidos = 0
    for ext in extensoes:
        for file in glob.glob(os.path.join(temp_dir, f"*{ext}")):
            try:
                os.remove(file)
                total_removidos += 1
                if logger:
                    logger.debug(f"🧹 Removido temporário: {file}")
            except Exception as e:
                if logger:
                    logger.warning(f"Erro ao remover {file}: {e}")
                else:
                    print(f"Erro ao remover {file}: {e}")
    if logger:
        logger.info(f"🧹 Limpeza de artefatos pdf2image: {total_removidos} removidos")

def gerar_txt_json_openAI(path_csv_entrada_arquivos: Path, api_key: str):
    try:
        # 1. Carrega todos os nomes de PDF do CSV e verifica duplicidade
        with open(path_csv_entrada_arquivos, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            nomes_pdf = [row.get("nome") for row in reader if row.get("nome")]
        nomes_duplicados = set([x for x in nomes_pdf if nomes_pdf.count(x) > 1])
        if nomes_duplicados:
            logger.error(f"[MAIN] Existem PDFs com nomes duplicados (não será processado): {nomes_duplicados}")
            return

        # 2. Processa normalmente, sobrescrevendo TXT/JSON
        with open(path_csv_entrada_arquivos, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                nome = row.get("nome")
                caminho_arquivo = row.get("caminho_arquivo")
                caminho_subdir = row.get("caminho_subdir")
                txt_output = f"{caminho_subdir}/{nome}.txt"
                json_output = f"{caminho_subdir}/{nome}.json"
                try:
                    client = OpenAI(api_key=api_key)
                    logger.info(f"[MAIN] API_KEY: {api_key}")
                    logger.info(f"[MAIN] API_KEY: {client.api_key}")
                    logger.info(f"[MAIN] Processando PDF: {nome} em {caminho_arquivo}")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pages = convert_from_path(caminho_arquivo, dpi=300, output_folder=temp_dir)

                        results = []
                        results_consolidador_json = []

                        results.append("=== ANÁLISE ESTRUTURADA OPENAI  ===\n")
                        results.append(f"Arquivo: {os.path.basename(caminho_arquivo)}\n")
                        results.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                        results.append("="*50 + "\n\n")

                        # Extrai dados estruturados de cada página
                        for i, page in enumerate(pages, 1):
                            if logger:
                                logger.log_progress('TEXT_PROC', i + 1, len(pages) + 1, f"Página {i}", "Dados estruturados")

                            page_path = os.path.join(temp_dir, f"page_{i}.png")
                            page.save(page_path, "PNG")
                            base64_image = encode_image_to_base64(page_path)

                            response = client.chat.completions.create(
                                model="gpt-4.1-nano",
                                messages=[
                                        {"role": "system", "content": "Você é um assistente extrator de informações de boletos, comprovantes de pagamento, etc."},
                                        {"role": "system", "content": (
                                            "Você é um assistente jurídico especializado na extração de informações "
                                            "de documentos diversos como contratos, boletos, notas fiscais e prints. "
                                        )},
                                        {"role": "user",   "content": "Você irá analisar cada página do documento e extrair informações estruturadas. Arquivos como boletos podem conter informações relevantes como data de vencimento, valor de pagamento, data de processamento, descrição, deduções, multas, juros, data do documento, nosso numero, número do documento, data de emissão, data de processamento, data de vencimento, valor do documento, valor pago, valor da multa, valor dos juros, valor total a pagar, valor do desconto, data do desconto, data de compensação, data de baixa. Em arquivos como comprovantes de pagamento, extratos bancários, etc., extraia informações como data de transação, valor, descrição, saldo, data de credito, data de solicitação, desconto, juros."},
                                        {"role": "assistant", "content": "Claro! Pode me fornecer o texto ou imagem?"},
                                        {
                                            "role": "user",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": """Extraia informações estruturadas desta página:
                                                    Organize as informações de forma clara e estruturada
                                                    - Tipo de documento (contrato, nota fiscal, relatório, boleto, print, tabela, tela de software)
                                                    - Valores monetários detalhados, incluindo:
                                                        - Valor do documento
                                                        - Valor pago
                                                        - Valor da multa
                                                        - Valor dos juros
                                                        - Valor total a pagar
                                                        - Valor do desconto
                                                    - Datas encontradas(detalhes como vencimento, emissão, processamento, pagamento, solicitação, compensação, baixa):
                                                        - Data do desconto
                                                        - Data de compensação
                                                        - Data de baixa
                                                        - Data de vencimento
                                                        - Data de emissão
                                                        - Data de processamento
                                                        - Data de solicitação
                                                        - Data de crédito
                                                        - Data de Pagamento
                                                    - Nomes de pessoas/empresas
                                                    - Números de documentos (nosso número, número do documento)
                                                    - Tabelas completas 
                                                    
                                                    """
                                                },
                                                {
                                                    "type": "image_url",
                                                    "image_url": {
                                                        "url": f"data:image/png;base64,{base64_image}"
                                                    }
                                                }
                                            ]
                                        }
                                    ],
                                temperature=0.2
                            )

                            structured_data = response.choices[0].message.content
                            results.append(f"=== DADOS ESTRUTURADOS - PÁGINA {i} ===\n")
                            results.append(structured_data)
                            results.append(f"\n\n{'='*40}\n\n")

                        if results:
                            #limpar_artefatos_pdf2image(temp_dir)
                            response = client.chat.completions.create(
                                model="gpt-4.1-nano-2025-04-14",
                                messages=[
                                    {"role": "system", "content": "Você é um assistente especializado na consolidação de dados estruturados."},
                                    {"role": "user", "content": "Consolide os dados estruturados extraídos em um formato JSON pelas paginas, ai em cada pagina tera suas datas(vencimento, pagamento,socilitacao, etc), valores monetarios."},
                                    {"role": "assistant", "content": "Claro! Vou consolidar os dados estruturados em um formato JSON organizado."},
                                    {"role": "user", "content": f"{results}"}
                                ],
                                temperature=0.2)

                            consolidated_data = response.choices[0].message.content
                            results_consolidador_json.append(consolidated_data)
                        else:
                            logger.warning(f"[MAIN] Nenhum dado estruturado encontrado na página {i} do PDF {nome}")

                        # Sempre sobrescreve TXT/JSON
                        with open(txt_output, "w", encoding="utf-8") as f:
                            f.write("".join(results))

                        with open(json_output, "w", encoding="utf-8") as f:
                            f.write("".join(results_consolidador_json))

                except Exception as e:
                    logger.error(f"[MAIN] Erro ao processar arquivo {nome}: {e}")
                    continue
        logger.info("[MAIN.OPENAI_PROCESSAMENTO] Processo concluido!")
    except Exception as e:
        logger.error(f"[MAIN.OPENAI_PROCESSAMENTO] Erro ao processar o arquivo CSV: {e}")
        raise e

def main():
    global logger, config
    logger, config = iniciando_configuracoes()
    
    path_entrada = Path(config['Paths']['PATH_ENTRADA'])
    path_saida = Path(config['Paths']['PATH_SAIDA'])
    path_fonte = Path(config['Paths']['PATH_FONTE'])
    path_processados = Path(config['Paths']['PATH_PROCESSADOS'])
    path_csv_entrada = Path(config['Paths']['PATH_CSV_ENTRADA'])
    path_csv_saida = Path(config['Paths']['PATH_CSV_SAIDA'])
    path_csv_fonte = Path(config['Paths']['PATH_CSV_FONTE'])
    path_csv_processados = Path(config['Paths']['PATH_CSV_PROCESSADOS'])
    path_csv_entrada_manter = Path(config['Paths']['PATH_CSV_ENTRADA_MANTER'])
    path_csv_saida_manter = Path(config['Paths']['PATH_CSV_SAIDA_MANTER'])
    path_csv_processados_manter = Path(config['Paths']['PATH_CSV_PROCESSADOS_MANTER'])
    path_csv_entrada_arquivos = Path(config['Paths']['PATH_CSV_ENTRADA_ARQUIVOS'])
    path_csv_saida_arquivos = Path(config['Paths']['PATH_CSV_SAIDA_ARQUIVOS'])
    path_csv_fonte_arquivos = Path(config['Paths']['PATH_CSV_FONTE_ARQUIVOS'])
    api_key = config['OpenAI']['API_KEY']
    path_temp_dir = Path(config['Paths']['PATH_TEMP_DIR'])
    
    """ gerar_csv_manter_diretorios(path_entrada, path_csv_entrada)
    comparar_csvs_faltantes(path_csv_entrada, path_csv_saida, path_csv_entrada_manter)
    gerar_csv_manter_diretorios(path_saida, path_csv_saida)
    comparar_csvs_faltantes(path_csv_fonte, path_csv_saida, path_csv_saida_manter) """
    
    arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_saida, max_workers=4)
    gerar_csv_arquivos_pdfs(arquivos_pdfs, subdirs, path_csv_saida_arquivos)
    
    arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_entrada, max_workers=4)
    gerar_csv_arquivos_pdfs(arquivos_pdfs, subdirs, path_csv_entrada_arquivos)
    
    gerar_txt_json_openAI(path_csv_entrada_arquivos, api_key)
    
    
if __name__ == "__main__":
    main()
    
    #preciso criar um script para comparar csv_processados com csv_fonte 
    
    # Salva todos os subdiretórios em um arquivo CSV (um por linha)
    # Se o arquivo não existir, será criado. Se existir, será sobrescrito (modo 'w').
    

    """ # Carrega registros do primeiro CSV (nome, caminho)
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
    with open(path_csv_3, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        writer.writerow(['nome', 'caminho_csv1', 'caminho_csv2'])
        for nome, caminho1 in registros_1.items():
            caminho2 = registros_2.get(nome, '')
            writer.writerow([nome, caminho1, caminho2])

    print(f"Arquivo de comparação gerado: {path_csv_3}") """

    

#sem alterar nada no codigo original de process_pdfs_openAI me ajude criando um scri
    
    """ Vou separar o Projeto em:
    1. Configuração e inicialização
    2. Encontrar todos arquivos PDF no diretório de entrada
    3. Transformar os PDFs em imagens com pdf2image e transformar em base 64 para enviar para a OpenAI Vision API
    4. Enviar as imagens para o OpenAI Vision API
    5. Receber as respostas da API e Consolidar e estruturação dos dados
    6. Salvar os resultados no diretório de saída
    7. Exibir relatório de sucesso ou falha
    
    Detalhando TODO:
    1. Configuração e inicialização
        A.importar bibliotecas necessárias
        B.criar função para carregar configurações do arquivo config.ini
        C.configurar logger para registrar mensagens em um arquivo com timestamp e console
        D.verificar se o diretório de entrada existe
        E.verificar se o diretório de saída existe, se não, cria-o
        F.exibir informações do ambiente (executável Python, argumentos, diretório de trabalho, versão do Python)
    2. Encontrar todos arquivos PDF no diretório de entrada
        A.listar todos os arquivos PDF no diretório de entrada
            -> Usar funcao listar com os.scandir() + multiprocessing para processar arquivos em paralelo
        B.verificar se existem arquivos PDF, se não, registrar mensagem de aviso
    3. Transformar os PDFs em imagens com pdf2image
        A. usar convert_from_path para converter cada PDF em uma lista de imagens
        B. salvar as imagens temporariamente em um diretório temporário
        4. enviar as imagens para o OpenAI Vision API
            A. criar função para enviar imagens para a API
            B. usar biblioteca asyncio para enviar as imagens em paralelo
            C. lidar com limites de taxa da API com semaphore e erros de rede
            D. implementar lógica de retry para chamadas falhas
            5. Receber as respostas da API e consolidar e estruturar os dados
                A. ao confirmar o recebimento de uma resposta da API, apagar a imagem temporária correspondente e adicionar a resposta à lista de resultados
                B. criar um subdiretórios com nome de cada pasta encontrada no diretório de entrada
                C. estruturar os dados recebidos da API em um arquivo TXT com nome correspondente ao nome do arquivo PDF original, se o pdf tiver mais de uma página, criar um arquivo TXT contendo todas as páginas do pdf
                D. salvar os arquivos TXT no subdiretório correspondente
                6. Realizar mais uma chamada a API para cada arquivo TXT criado
                    A. enviar o arquivo TXT para a API para retornar um JSON estruturado
                    B. verificar se a resposta da API é válida
                    C. salvar a resposta em um JSON no subdiretório correspondente

            
    """

