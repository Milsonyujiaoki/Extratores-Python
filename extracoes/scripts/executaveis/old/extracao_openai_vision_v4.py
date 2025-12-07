# -*- coding: utf-8 -*-
"""
Extração usando OpenAI Vision API ASSÍNCRONA - Para PDFs complexos ou com formatação especial
Biblioteca: openai, pdf2image, asyncio
Instalação: pip install openai pdf2image pillow
Configuração: Definir OPENAI_API_KEY como variável de ambiente
"""
from curses.ascii import ctrl
import os
import sys
import base64
from pdf2image import convert_from_path
import tempfile
import asyncio
import time
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import glob
import shutil
import csv
import hashlib


# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class StructuredLogger:
    def __init__(self, project_name="openai_vision", log_dir="logs"):
        from pathlib import Path
        import logging
        import time
        from datetime import datetime

        self.project_name = project_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        log_format = '%(asctime)s | %(levelname)8s | %(name)30s | %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Logger principal
        self.logger = logging.getLogger(f'openai_vision_{project_name}')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # impede log duplo no root logger

        # Remove todos os handlers existentes
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)

        # Arquivo de log
        log_file = self.log_dir / f"{project_name}_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        file_handler.setLevel(logging.DEBUG)

        # Console com stream
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        console_handler.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Fases separadas
        self.phases = {}
        phase_names = ['INIT', 'PDF_SCAN', 'PDF_CONV', 'API_CALL', 'TEXT_PROC', 'FILE_SAVE', 'STATS']
        for phase in phase_names:
            phase_logger = logging.getLogger(f'openai_vision_{project_name}.{phase.lower()}')
            phase_logger.setLevel(logging.DEBUG)
            phase_logger.propagate = False  # evita duplicações

            # Verifica handlers duplicados por tipo
            if not any(isinstance(h, logging.FileHandler) for h in phase_logger.handlers):
                phase_logger.addHandler(file_handler)
            if not any(isinstance(h, logging.StreamHandler) for h in phase_logger.handlers):
                phase_logger.addHandler(console_handler)

            self.phases[phase] = phase_logger

        self.start_time = time.time()
        self.phase_times = {}

        self.logger.info("="*80)
        self.logger.info(f"🚀 SISTEMA DE LOGGING INICIADO - {project_name.upper()}")
        self.logger.info(f"📁 Log salvo em: {log_file}")
        self.logger.info("="*80)

    def start_phase(self, phase_name, description=""):
        if phase_name in self.phase_times:
            self.end_phase(phase_name)
        self.phase_times[phase_name] = time.time()

        phase_logger = self.phases.get(phase_name, self.logger)
        phase_logger.info("─" * 60)
        phase_logger.info(f"🔄 INICIANDO FASE: {phase_name} ─ {description}")
        phase_logger.info("─" * 60)

    def end_phase(self, phase_name, success=True):
        if phase_name not in self.phase_times:
            return
        duration = time.time() - self.phase_times[phase_name]
        del self.phase_times[phase_name]

        phase_logger = self.phases.get(phase_name, self.logger)
        status = "✅ CONCLUÍDA" if success else "❌ FALHOU"
        phase_logger.info(f"{status} FASE: {phase_name} ({duration:.2f}s)")
        phase_logger.info("─" * 60)

    def log_progress(self, phase_name, current, total, item_name="", extra_info=""):
        phase_logger = self.phases.get(phase_name, self.logger)
        percentage = (current / total * 100) if total > 0 else 0
        progress_bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
        message = f"📊 [{progress_bar}] {current}/{total} ({percentage:.1f}%)"
        if item_name:
            message += f" - {item_name}"
        if extra_info:
            message += f" | {extra_info}"
        phase_logger.info(message)

    def log_api_call(self, page_num, total_pages, status="enviando", response_size=0, error=None):
        logger = self.phases['API_CALL']
        if status == "enviando":
            logger.info(f"🤖 API Call [{page_num}/{total_pages}] - Enviando imagem para OpenAI Vision...")
        elif status == "sucesso":
            logger.info(f"✅ API Call [{page_num}/{total_pages}] - Resposta recebida: {response_size} caracteres")
        elif status == "erro":
            logger.error(f"❌ API Call [{page_num}/{total_pages}] - ERRO: {error}")

    def log_file_operation(self, operation, file_path, success=True, size=0, error=None):
        logger = self.phases['FILE_SAVE']
        name = Path(file_path).name
        if operation == "save" and success:
            logger.info(f"💾 Arquivo salvo: {name} ({size} bytes)")
        elif operation == "save":
            logger.error(f"❌ Erro ao salvar {name}: {error}")
        elif operation == "load":
            logger.info(f"📂 Carregando arquivo: {name}")

    def log_statistics(self, stats_dict):
        logger = self.phases['STATS']
        logger.info("📊 ESTATÍSTICAS FINAIS:")
        for k, v in stats_dict.items():
            logger.info(f"   {k}: {v}")

    def get_total_runtime(self):
        return time.time() - self.start_time


# Instância global do logger
logger_instance = None

def get_logger(project_name="default"):
    """Obtém a instância do logger estruturado"""
    global logger_instance
    if logger_instance is None:
        logger_instance = StructuredLogger(project_name)
    return logger_instance

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

CSV_CTRL_PATH = os.environ.get('CSV_CTRL_PATH')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
MAX_CONCURRENT_API_CALLS = int(os.environ.get('MAX_CONCURRENT_API_CALLS', 50))

def hash_file(path: str) -> str:

    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def append_ctrl_csv(projeto, arquivo_pdf, hash_pdf, status, output_path, path=CSV_CTRL_PATH):
    # Carrega todos os registros já existentes no CSV (se houver)
    registros = set()
    if os.path.exists(path):
        with open(path, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Considere como identificador único: projeto, arquivo, hash, status, output_path
                key = (row['projeto'], row['arquivo_pdf'], row['hash_pdf'], row['status'], row['output_path'])
                registros.add(key)
    # Monta a chave deste registro
    reg_key = (projeto, arquivo_pdf, hash_pdf, status, output_path)
    if reg_key in registros:
        # Já existe: não adiciona duplicado!
        return
    # Escreve a nova linha
    existe = os.path.exists(path)
    with open(path, 'a', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['projeto', 'arquivo_pdf', 'hash_pdf', 'data_processamento', 'status', 'output_path'])
        writer.writerow([
            projeto,
            arquivo_pdf,
            hash_pdf,
            datetime.now().isoformat(),
            status,
            output_path,
        ])
def popular_csv_de_processados(processados_path, csv_path=CSV_CTRL_PATH):
    """
    Para cada projeto em /Processados, para cada PDF na raiz,
    procura a pasta de resultados com o mesmo nome base e registra no CSV,
    evitando duplicidade.
    """
    import csv

    # 1. Carrega os registros já existentes no CSV uma única vez
    registros_existentes = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['projeto'], row['arquivo_pdf'], row['hash_pdf'], row['status'], row['output_path'])
                registros_existentes.add(key)

    for projeto in os.listdir(processados_path):
        pasta_projeto = os.path.join(processados_path, projeto)
        if not os.path.isdir(pasta_projeto):
            continue

        # PDFs na raiz do projeto (não em subpastas)
        pdfs = [f for f in os.listdir(pasta_projeto)
                if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(pasta_projeto, f))]
        pasta_resultados = os.path.join(pasta_projeto, "resultados")

        for pdf in pdfs:
            nome_base = os.path.splitext(pdf)[0]
            pasta_arquivo_result = os.path.join(pasta_resultados, nome_base)
            if not os.path.isdir(pasta_arquivo_result):
                print(f"⚠️ Pasta de resultado não encontrada para {pdf} em {projeto}")
                continue

            # Busca o JSON
            jsons = glob.glob(os.path.join(pasta_arquivo_result, 'openai_vision_*.json'))
            if not jsons:
                print(f"⚠️ JSON não encontrado para {pdf} em {projeto}")
                continue

            json_file = jsons[0]
            pdf_path = os.path.join(pasta_projeto, pdf)
            hash_pdf = hash_file(pdf_path)

            reg_key = (projeto, pdf, hash_pdf, "success", json_file)
            if reg_key in registros_existentes:
                print(f"⏩ Já registrado no CSV: {projeto} | {pdf}")
                continue  # Não registra duplicado

            append_ctrl_csv(projeto, pdf, hash_pdf, "success", json_file, path=csv_path)
            registros_existentes.add(reg_key)  # Para não duplicar se rodar novamente na mesma execução
            print(f"Registrado no CSV: {projeto} | {pdf} | {json_file}")


def carrega_ctrl_csv(path=CSV_CTRL_PATH):
    if not os.path.exists(path):
        return {}
    with open(path, newline='', encoding="utf-8") as f:
        return {(row['projeto'], row['arquivo_pdf'], row['hash_pdf']): row for row in csv.DictReader(f)}


def limpar_artefatos_pdf2image(temp_dir, extensoes=(".ppm", ".pbm", ".jpg", ".jpeg"), logger=None):
    total_removidos = 0
    for ext in extensoes:
        for file in glob.glob(os.path.join(temp_dir, f"*{ext}")):
            try:
                os.remove(file)
                total_removidos += 1
                if logger:
                    logger.logger.debug(f"🧹 Removido temporário: {file}")
            except Exception as e:
                if logger:
                    logger.logger.warning(f"Erro ao remover {file}: {e}")
                else:
                    print(f"Erro ao remover {file}: {e}")
    if logger:
        logger.logger.info(f"🧹 Limpeza de artefatos pdf2image: {total_removidos} removidos")

def limpar_temp_antigo(path_temp: str = None, max_idade_horas: int = 2):
    if not path_temp:
        path_temp = os.environ.get('TMP', os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp'))
    agora = time.time()
    for entry in os.scandir(path_temp):
        if entry.is_dir():
            try:
                idade = agora - entry.stat().st_mtime
                if idade > max_idade_horas * 3600:
                    shutil.rmtree(entry.path, ignore_errors=True)
                    print(f"🧹 Limpo temporário antigo: {entry.path}")
            except Exception as e:
                print(f"Erro ao limpar {entry.path}: {e}")

async def worker(queue: asyncio.Queue, client, total_pages: int, logger=None, results: list[tuple[int, str]] = None):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break

        page_num, image_data = item
        try:
            result = await process_page_async(client, image_data, page_num, total_pages, logger)
            if results is not None:
                results.append(result)
        except Exception as e:
            if logger:
                logger.log_api_call(page_num, total_pages, "erro", error=str(e))
        finally:
            queue.task_done()

async def process_all_pages_with_queue(client: Any, page_data: list[tuple[int, str]], MAX_CONCURRENT_API_CALLS: int, logger=None) -> list[tuple[int, str]]:
    queue: asyncio.Queue = asyncio.Queue()
    results: list[tuple[int, str]] = []

    # Preenche a fila com páginas
    for item in page_data:
        await queue.put(item)

    # Adiciona os sinais de parada (poison pills)
    for _ in range(MAX_CONCURRENT_API_CALLS):
        await queue.put(None)

    # Cria os workers
    tasks = [asyncio.create_task(worker(queue, client, len(page_data), logger, results)) for _ in range(MAX_CONCURRENT_API_CALLS)]

    # Aguarda todos os workers finalizarem
    await queue.join()
    await asyncio.gather(*tasks)

    # Ordena os resultados por número da página
    results.sort(key=lambda x: x[0])
    return results

def process_pdf(pdf_file: str, output_dir: str, logger, projeto: str, ctrl: dict) -> dict:
    try:
        filename = os.path.basename(pdf_file)
        hash_pdf = hash_file(pdf_file)
        chave = (projeto, filename, hash_pdf)
        output_json = f"{output_dir}/openai_vision_{filename}.json"

        # Checagem se já processado
        registro = ctrl.get(chave)
        if registro and registro['status'] == 'success' and os.path.exists(output_json):
            logger.logger.info(f"⏩ Pulando {pdf_file} (já processado com sucesso!)")
            return {'filename': filename, 'success': True, 'skipped': True}

        # Marca início de processamento
        append_ctrl_csv(projeto, filename, hash_pdf, "processing", output_json)

        try:
            # ... (chame seu processamento real aqui)
            # exemplo: success = extract_text_openai_vision(...)
            success = extract_text_openai_vision(
                pdf_file,
                output_json.replace('.json', '.txt'),
                output_json.replace('.json', '_txt.txt'),
                output_json,
                logger=logger
            )

            status = "success" if success else "error"
            append_ctrl_csv(projeto, filename, hash_pdf, status, output_json)
            return {
                'filename': filename,
                'success': success,
                'skipped': False
            }
        except Exception as e:
            append_ctrl_csv(projeto, filename, hash_pdf, "error", output_json)
            logger.logger.error(f"❌ Erro ao processar PDF {pdf_file}: {e}")
            return {
                'filename': filename,
                'success': False,
                'error': str(e),
                'skipped': False
            }
    finally:
        pass

def process_project(project_name: str, ctrl: dict) -> tuple[str, bool, int]:
    """Processa um projeto completo (vários PDFs) com controle de duplicidade pelo CSV"""

    try:
        logger.logger.info("="*100)
        logger.logger.info(f"🚀 INICIANDO PROJETO: {project_name}")
        logger.logger.info("="*100)

        project_pdf_path = f"{PDF_BASE_PATH}/{project_name}"
        project_output_dir = f"{RESULTS_BASE_PATH}/{project_name}"
        os.makedirs(project_output_dir, exist_ok=True)

        pdf_files = glob.glob(f"{project_pdf_path}/*.pdf")
        pdf_files = sorted(pdf_files, key=os.path.getctime)  # FIFO

        # Logando a fila:
        logger.logger.info("📑 Fila de PDFs a processar (FIFO):")
        for idx, pdf in enumerate(pdf_files, 1):
            logger.logger.info(f"   [{idx}] {os.path.basename(pdf)} (ctime: {os.path.getctime(pdf)})")

        if not pdf_files:
            logger.logger.warning(f"⚠️ Nenhum PDF encontrado em {project_name}")
            return project_name, False, 0

        logger.logger.info(f"📄 {len(pdf_files)} PDFs encontrados em {project_name}")

        success_count = 0

        for i, pdf_file in enumerate(pdf_files, 1):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            pdf_dir = f"{project_output_dir}/{filename}"
            os.makedirs(pdf_dir, exist_ok=True)

            txt_output = f"{pdf_dir}/openai_vision_{filename}.txt"
            json_output_txt = f"{pdf_dir}/openai_json_{filename}.txt"
            json_output = f"{pdf_dir}/openai_vision_{filename}.json"

            # --- Controle CSV ---
            hash_pdf = hash_file(pdf_file)
            chave = (project_name, f"{filename}.pdf", hash_pdf)
            registro = ctrl.get(chave)
            if registro and registro['status'] == 'success' and os.path.exists(json_output):
                logger.logger.info(f"⏩ Pulando {filename}.pdf (já processado com sucesso!)")
                continue

            append_ctrl_csv(project_name, f"{filename}.pdf", hash_pdf, "processing", json_output)

            logger.logger.info(f"📄 [{i}/{len(pdf_files)}] {filename}")

            try:
                success = extract_text_openai_vision(
                    pdf_file,
                    txt_output,
                    json_output_txt,
                    json_output,
                    logger=logger,
                    MAX_CONCURRENT_API_CALLS=MAX_CONCURRENT_API_CALLS
                )
                status = "success" if success else "error"
                append_ctrl_csv(project_name, f"{filename}.pdf", hash_pdf, status, json_output)
                if success:
                    logger.logger.info(f"✅ Extração concluída: {filename}")
                    success_count += 1
                else:
                    logger.logger.error(f"❌ Erro na extração: {filename}")
            except Exception as e:
                append_ctrl_csv(project_name, f"{filename}.pdf", hash_pdf, "error", json_output)
                logger.logger.error(f"❌ Erro inesperado na extração: {filename}: {e}")

        # Mover para Processados
        destino = f"{PDF_BASE_PATH}/Processados/{project_name}"
        os.makedirs(destino, exist_ok=True)
        try:
            shutil.move(project_pdf_path, destino)
        except Exception as e:
            logger.logger.warning(f"⚠️ Não foi possível mover {project_pdf_path}: {e}")
        try:
            shutil.move(project_output_dir, f"{destino}/resultados")
        except Exception as e:
            logger.logger.warning(f"⚠️ Não foi possível mover resultados para {destino}: {e}")

        logger.logger.info(f"📦 Projeto movido para: {destino}")
        return project_name, True, success_count

    except Exception as e:
        logger.logger.error(f"❌ Erro ao processar projeto {project_name}: {e}")
        return project_name, False, 0


async def requisicao_async(client, extracted_text, logger=None):
    """Faz uma requisição assíncrona para a API OpenAI"""
    try:
        if logger:
            logger.phases['API_CALL'].info("🤖 Enviando texto extraído para OpenAI Vision API...")
        else:
            print("🤖 Enviando texto extraído para OpenAI Vision API...")
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano",
             messages=[
                {"role": "system", "content": "Você é um assistente especializado na consolidação de dados estruturados."},
                {"role": "user", "content": "Consolide os dados estruturados extraídos em um formato JSON pelas paginas, ai em cada pagina tera suas datas(vencimento, pagamento,socilitacao, etc), valores monetarios."},
                {"role": "assistant", "content": "Claro! Vou consolidar os dados estruturados em um formato JSON organizado."},
                {
                    "role": "user",
                    "content": f"{extracted_text}"
                }
            ],
            temperature=0.1
        )
        extracted_json = response.choices[0].message.content

        if logger:
            logger.phases['API_CALL'].info("✅ Resposta recebida da API.")
        else:
            print("✅ Resposta recebida da API.")

        return extracted_json

    except Exception as e:
        error_msg = f"❌ Erro na requisição à API: {e}"
        if logger:
            logger.phases['API_CALL'].error(error_msg)
        else:
            print(error_msg)
        return None

def encode_image_to_base64(image_path):
    """Converte imagem para base64 para enviar à API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def process_page_async(client, page_image_data, page_num, total_pages, logger=None):
    """Processa uma página de forma assíncrona"""
    try:
        if logger:
            logger.log_api_call(page_num, total_pages, "enviando")
        else:
            print(f"   🤖 [{page_num}/{total_pages}] Enviando para OpenAI Vision API...")
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Você é um assistente extrator de informações de boletos, comprovantes de pagamento, etc."},
                {"role": "system", "content": (
                            "Você é um assistente jurídico especializado na extração de informações "
                            "de documentos diversos como contratos, boletos, notas fiscais e prints. ")},
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
                                "url": f"data:image/png;base64,{page_image_data}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1
        )
        
        page_text = response.choices[0].message.content
        response_size = len(page_text) if page_text else 0
        
        if logger:
            logger.log_api_call(page_num, total_pages, "sucesso", response_size)
        else:
            print(f"   ✅ [{page_num}/{total_pages}] Resposta recebida: {response_size} caracteres")
        
        return page_num, page_text
        
    except Exception as e:
        if logger:
            logger.log_api_call(page_num, total_pages, "erro", error=str(e))
        else:
            print(f"   ❌ [{page_num}/{total_pages}] Erro: {e}")
        return page_num, f"[ERRO NA API OPENAI: {e}]"

def extract_text_openai_vision(pdf_path, txt_path, json_output_txt, json_output, api_key='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', MAX_CONCURRENT_API_CALLS=5, logger=None):
    """Wrapper síncrono para a função assíncrona"""
    return asyncio.run(extract_text_openai_vision_async(pdf_path, txt_path, json_output_txt, json_output, api_key=api_key, MAX_CONCURRENT_API_CALLS=MAX_CONCURRENT_API_CALLS, logger=logger))

async def extract_text_openai_vision_async(pdf_path, txt_path, json_output_txt, json_output, api_key="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", MAX_CONCURRENT_API_CALLS=5, logger=None):
    """
    Extrai texto usando OpenAI Vision API de forma ASSÍNCRONA
    """
    if not OPENAI_AVAILABLE:
        error_msg = "❌ Biblioteca OpenAI não está instalada. Execute: pip install openai"
        if logger:
            logger.phases['INIT'].error(error_msg)
        else:
            print(error_msg)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
        return False
    
    # Configuração da API
    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY', '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')
    
    if not api_key:
        error_msg = "❌ OPENAI_API_KEY não configurada. Defina a variável de ambiente."
        if logger:
            logger.phases['INIT'].error(error_msg)
        else:
            print(error_msg)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(error_msg + "\n")
            f.write("Configure: set OPENAI_API_KEY=sua_chave_aqui\n")
        return False
    
    try:
        # Fase de inicialização
        if logger:
            logger.start_phase('INIT', f"Configurando extração para {os.path.basename(pdf_path)}")
            logger.phases['INIT'].info(f"🔑 API Key configurada: {api_key[:20]}...")
            logger.phases['INIT'].info(f"⚡ Máximo de requisições simultâneas: {MAX_CONCURRENT_API_CALLS}")
        
        client = AsyncOpenAI(api_key=api_key)
        
        if not logger:
            print(f"🤖 Iniciando extração OpenAI Vision ASSÍNCRONA para {os.path.basename(pdf_path)}...")
            print(f"🔑 API Key configurada: {api_key[:20]}...")
            print(f"⚡ Máximo de requisições simultâneas: {MAX_CONCURRENT_API_CALLS}")
        
        # Fase de conversão PDF
        if logger:
            logger.end_phase('INIT', True)
            logger.start_phase('PDF_CONV', "Convertendo PDF para imagens")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            if not logger:
                print("📄 Convertendo PDF para imagens...")
            
            try:
                pages = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir)
                if logger:
                    logger.phases['PDF_CONV'].info(f"✅ PDF convertido: {len(pages)} páginas detectadas")
                else:
                    print(f"✅ PDF convertido: {len(pages)} páginas detectadas")
            except Exception as e:
                if logger:
                    logger.phases['PDF_CONV'].error(f"❌ Erro na conversão PDF: {e}")
                    logger.end_phase('PDF_CONV', False)
                else:
                    print(f"❌ Erro na conversão PDF: {e}")
                raise
            finally:
                # Limpa artefatos temporários do pdf2image
                limpar_artefatos_pdf2image(temp_dir)
            
            # Fase de preparação das páginas
            if logger:
                logger.end_phase('PDF_CONV', True)
                logger.start_phase('TEXT_PROC', "Preparando páginas para processamento")
            
            page_data = []
            
            if not logger:
                print(f"🔄 Preparando {len(pages)} páginas para processamento paralelo...")
            
            for i, page in enumerate(pages, 1):
                page_path = os.path.join(temp_dir, f"page_{i}.png")
                page.save(page_path, "PNG")
                
                # Verifica tamanho da imagem
                img_size = os.path.getsize(page_path) / 1024  # KB
                
                if logger:
                    logger.log_progress('TEXT_PROC', i, len(pages), f"Página {i}", f"{img_size:.1f} KB")
                else:
                    print(f"   📊 Página {i}: {img_size:.1f} KB")
                
                # Codifica para base64
                base64_image = encode_image_to_base64(page_path)
                page_data.append((i, base64_image))
            
            # Fase de processamento API
            if logger:
                logger.end_phase('TEXT_PROC', True)
                logger.start_phase('API_CALL', f"Processamento paralelo de {len(pages)} páginas")
            else:
                print(f"🚀 Iniciando processamento PARALELO de {len(pages)} páginas...")
            
            
            # Usando fila para processamento assíncrono
            if logger:
                logger.phases['API_CALL'].info(f"🔄 Processando {len(page_data)} páginas com {MAX_CONCURRENT_API_CALLS} requisições simultâneas...")
            else:
                print(f"🔄 Processando {len(page_data)} páginas com {MAX_CONCURRENT_API_CALLS} requisições simultâneas...")
            results = await process_all_pages_with_queue(client, page_data, MAX_CONCURRENT_API_CALLS, logger)
            
            # Fase de salvamento
            if logger:
                logger.end_phase('API_CALL', True)
                logger.start_phase('FILE_SAVE', "Organizando e salvando resultados")
            
            # Organiza resultados
            extracted_text = []
            extracted_json = []
            extracted_text.append("=== EXTRAÇÃO OPENAI VISION API (ASSÍNCRONA) ===\n")
            extracted_text.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            extracted_text.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            extracted_text.append(f"Páginas processadas: {len(pages)}\n")
            extracted_text.append(f"Processamento: PARALELO ({MAX_CONCURRENT_API_CALLS} requisições simultâneas)\n")
            extracted_text.append("="*50 + "\n\n")
            
            # Ordena resultados por número da página
            results.sort(key=lambda x: x[0])
            
            for page_num, page_text in results:
                if page_text and page_text.strip() and not page_text.startswith("[ERRO"):
                    extracted_text.append(f"=== PÁGINA {page_num} ===\n")
                    extracted_text.append(page_text.strip())
                    extracted_text.append(f"\n\n{'='*30}\n\n")
                    if logger:
                        logger.phases['FILE_SAVE'].info(f"📝 Página {page_num}: Texto extraído com sucesso")
                    else:
                        print(f"   📝 Página {page_num}: Texto extraído com sucesso")
                else:
                    extracted_text.append(f"=== PÁGINA {page_num} ===\n")
                    extracted_text.append(page_text if page_text else "[PÁGINA EM BRANCO OU SEM TEXTO DETECTADO]")
                    extracted_text.append(f"\n\n{'='*30}\n\n")
                    if logger:
                        logger.phases['FILE_SAVE'].warning(f"⚠️ Página {page_num}: {page_text if page_text and page_text.startswith('[ERRO') else 'Sem texto detectado'}")
                    else:
                        print(f"   ⚠️ Página {page_num}: {page_text if page_text and page_text.startswith('[ERRO') else 'Sem texto detectado'}")
                        
        # Consolida resultados em JSON
        if logger:
            logger.phases['FILE_SAVE'].info("🔄 Consolidando resultados em JSON...")
            logger.phases['FILE_SAVE'].info(f"💾 Salvando resultado em: {json_output_txt}")
            logger.phases['FILE_SAVE'].info(f"💾 Salvando resultado em: {json_output}")
        else:
            print(f" Salvando resultados em {json_output_txt}")
            print(f" Salvando resultados em {json_output}")
        
        """async def requisicao_async_with_semaphore(client, extracted_text, logger=None):
            async with semaphore:
                return await requisicao_async(client, "".join(extracted_text), logger)


        tasks = [requisicao_async_with_semaphore(client, "".join(extracted_text), logger) for _ in range(len(pages))]
        results = await asyncio.gather(*tasks)"""
        results = await requisicao_async(client, "".join(extracted_text), logger)
        extracted_json.append(results)

        # Salva resultado
        if logger:
            logger.phases['FILE_SAVE'].info(f"💾 Salvando resultado em: {txt_path}")
        else:
            print(f"💾 Salvando resultado em: {txt_path}")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(extracted_text))
            
        with open(json_output_txt, "w", encoding="utf-8") as f:
            f.write("".join(extracted_json))
        
        with open(json_output, "w", encoding="utf-8") as f:
            f.write("".join(extracted_json))
        
        # Verifica arquivo salvo
        if os.path.exists(txt_path):
            file_size = os.path.getsize(txt_path)
            if logger:
                logger.log_file_operation("save", txt_path, True, file_size)
                logger.end_phase('FILE_SAVE', True)
            else:
                print(f"✅ OpenAI Vision ASSÍNCRONA: Arquivo salvo ({file_size} bytes)")
        else:
            if logger:
                logger.log_file_operation("save", txt_path, False, error="Arquivo não foi criado")
                logger.end_phase('FILE_SAVE', False)
            else:
                print("❌ Erro: Arquivo não foi criado")
            return False
        
        return True
        
    except Exception as e:
        if logger:
            logger.phases['API_CALL'].error(f"❌ Erro na OpenAI Vision API ASSÍNCRONA: {e}")
            # Finaliza todas as fases ativas
            for phase in logger.phase_times.keys():
                logger.end_phase(phase, False)
        else:
            print(f"❌ Erro na OpenAI Vision API ASSÍNCRONA: {e}")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"ERRO NA OPENAI VISION API ASSÍNCRONA: {e}\n")
            f.write("Verifique se a chave da API está configurada corretamente.\n")
        return False



# Sistema multiprojeto com logs detalhados
if __name__ == "__main__":
    import glob
    import time
    import shutil
    
    # Configuração inicial
    
    PDF_BASE_PATH = os.environ.get('PDF_BASE_PATH')
    RESULTS_BASE_PATH = os.environ.get('RESULTS_BASE_PATH', '../resultados')
    PROCESSADOS_PATH = os.environ.get('PROCESSADOS_PATH', os.path.join(PDF_BASE_PATH, 'Processados'))
    CURRENT_PROJECT = os.environ.get('CURRENT_PROJECT')

    # Configuração de paralelismo
    OPENAI_MAX_RPM = int(os.environ.get('OPENAI_MAX_RPM', 4700))
    MODEL_NAME = os.environ.get('MODEL_NAME', 'gpt-4.1-nano')
    MAX_CPU = int(os.environ.get('MAX_CPU', os.cpu_count() or 4))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', min(8, MAX_CPU * 2)))
    MAX_PARALLEL_PROJECTS = int(os.environ.get('MAX_PARALLEL_PROJECTS', 5))

    # Temporários
    TEMP_GLOBAL = os.environ.get('TEMP_GLOBAL')
    TEMP_USER = os.environ.get('TEMP_USER')
    TEMP_PROJECT = os.environ.get('TEMP_PROJECT')

    limpar_temp_antigo(TEMP_PROJECT)
    ctrl = carrega_ctrl_csv(CSV_CTRL_PATH)
    popular_csv_de_processados(PROCESSADOS_PATH, CSV_CTRL_PATH)
    
    print(f"PDF_BASE_PATH (environ): {repr(os.environ.get('PDF_BASE_PATH'))}")
    print(f"PDF_BASE_PATH: {repr(PDF_BASE_PATH)}")
    print(f"exists: {os.path.exists(PDF_BASE_PATH)}")
    print(f"isdir: {os.path.isdir(PDF_BASE_PATH)}")
    print(f"Access OK: {os.access(PDF_BASE_PATH, os.R_OK)}")

    # Inicializa sistema de logging
    if CURRENT_PROJECT:
        logger = get_logger(CURRENT_PROJECT)
    else:
        logger = get_logger("batch_processing")
        
    # Configurações baseadas no modelo GPT-4.1 Nano (padrão atual para visão)
        MODEL_NAME = "gpt-4.1-nano"
        # Definido com base nos limites reais do modelo
        OPENAI_RPM = os.environ.get('OPENAI_MAX_RPM', 4000)  # Requisições por minuto para o modelo GPT-4.1 Nano

        """ESTIMATED_API_CALL_DURATION = 3  # segundos por página (pode ajustar)
        MAX_CPU = os.cpu_count() or 4
        MAX_WORKERS = min(8, MAX_CPU * 2)

        rpm_per_second = OPENAI_RPM / 60  # = 83.33
        MAX_CONCURRENT_API_CALLS = int(rpm_per_second * ESTIMATED_API_CALL_DURATION)
        MAX_CONCURRENT_API_CALLS = min(MAX_CONCURRENT_API_CALLS, 100)  # limite superior razoável

        # Paralelismo entre projetos com base no uso médio por projeto
        MAX_PARALLEL_PROJECTS = max(1, OPENAI_RPM // MAX_CONCURRENT_API_CALLS_API_CALLS)"""


        logger.logger.info(f"🔧 Modelo configurado: {MODEL_NAME}")
        logger.logger.info(f"🔧 OPENAI_RPM = {OPENAI_RPM}")
        logger.logger.info(f"🔧 MAX_CONCURRENT_API_CALLS por PDF = {MAX_CONCURRENT_API_CALLS}")
        logger.logger.info(f"🔧 max_workers entre projetos = {MAX_PARALLEL_PROJECTS}")
    
    logger.start_phase('INIT', "Configuração inicial do sistema")
    logger.phases['INIT'].info(f"📂 Pasta PDFs: {PDF_BASE_PATH}")
    logger.phases['INIT'].info(f"💾 Pasta resultados: {RESULTS_BASE_PATH}")
    
    """# Verifica se a pasta base de PDFs existe
    if not os.path.exists(PDF_BASE_PATH):
        # Tenta encontrar caminhos alternativos
        alternative_paths = [
            "../../pdfs",
            "../../../pdfs", 
            "../pdfs",
            "pdfs"
        ]
        
        logger.phases['INIT'].info("🔍 Tentando localizar pasta base de PDFs...")
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                PDF_BASE_PATH = alt_path
                logger.phases['INIT'].info(f"✅ Encontrada em: {alt_path}")
                break
        else:
            logger.phases['INIT'].error("❌ Nenhuma pasta de PDFs encontrada")
            logger.phases['INIT'].info("📁 Caminhos testados:")
            for path in alternative_paths:
                logger.phases['INIT'].info(f"   - {path}")
            logger.end_phase('INIT', False)
            exit(1)"""
    
    logger.end_phase('INIT', True)
    logger.start_phase('PDF_SCAN', "Escaneando pastas de PDFs")
    
    # Se CURRENT_PROJECT está definido, processa apenas essa pasta
    if CURRENT_PROJECT:
        project_dirs = [CURRENT_PROJECT] if os.path.exists(f"{PDF_BASE_PATH}/{CURRENT_PROJECT}") else []
        if not project_dirs:
            logger.phases['PDF_SCAN'].error(f"❌ Pasta do projeto {CURRENT_PROJECT} não encontrada")
            logger.end_phase('PDF_SCAN', False)
            exit(1)
        logger.phases['PDF_SCAN'].info(f"🎯 MODO PROJETO ESPECÍFICO: Processando apenas {CURRENT_PROJECT}")
    else:
        # MODO BATCH: Processa TODAS as pastas de projetos (exceto Processados) até finalizar
        logger.phases['PDF_SCAN'].info("🚀 MODO BATCH COMPLETO: Processando todas as pastas até finalizar")
        
        # Função para descobrir pastas pendentes
        def get_pending_projects():
            pending = []
            try:
                for item in os.listdir(PDF_BASE_PATH):
                    item_path = os.path.join(PDF_BASE_PATH, item)
                    if os.path.isdir(item_path) and item.lower() != 'processados':
                        # Verifica se a pasta contém PDFs
                        pdf_files_in_dir = glob.glob(f"{item_path}/*.pdf")
                        if pdf_files_in_dir:
                            pending.append(item)
            except OSError as e:
                logger.phases['PDF_SCAN'].error(f"❌ Erro ao escanear pastas: {e}")
            return sorted(pending)
        
        # Descobre todas as pastas pendentes
        project_dirs = get_pending_projects()
        
        if not project_dirs:
            logger.phases['PDF_SCAN'].info("✅ TODAS AS PASTAS JÁ FORAM PROCESSADAS!")
            logger.phases['PDF_SCAN'].info(f"📁 Não há novos projetos para processar em {PDF_BASE_PATH}")
            logger.end_phase('PDF_SCAN', True)
            
            # Mostra estatísticas da pasta Processados
            processados_path = f"{PDF_BASE_PATH}/Processados"
            if os.path.exists(processados_path):
                processed_folders = [f for f in os.listdir(processados_path) 
                                   if os.path.isdir(os.path.join(processados_path, f))]
                logger.phases['PDF_SCAN'].info(f"📊 Total de projetos já processados: {len(processed_folders)}")
                for folder in sorted(processed_folders)[:10]:  # Mostra até 10
                    logger.phases['PDF_SCAN'].info(f"   ✅ {folder}")
                if len(processed_folders) > 10:
                    logger.phases['PDF_SCAN'].info(f"   ... e mais {len(processed_folders) - 10} projetos")
            exit(0)
    
    logger.phases['PDF_SCAN'].info(f"📂 PASTAS DE PROJETOS ENCONTRADAS: {len(project_dirs)}")
    for i, project_dir in enumerate(project_dirs, 1):
        pdf_count = len(glob.glob(f"{PDF_BASE_PATH}/{project_dir}/*.pdf"))
        logger.phases['PDF_SCAN'].info(f"   {i:2d}. {project_dir} ({pdf_count} PDFs)")
    
    logger.end_phase('PDF_SCAN', True)
    
    # Estatísticas globais
    global_start_time = time.time()
    global_success_count = 0
    global_error_count = 0
    projects_processed = 0
    projects_moved = 0
    
    # Cria pasta de processados se não existir
    processados_dir = f"{PDF_BASE_PATH}/Processados"
    os.makedirs(processados_dir, exist_ok=True)
    
    logger.start_phase('PARALLEL_EXEC', f"Processando {len(project_dirs)} projetos em paralelo com {MAX_WORKERS} workers {MAX_CPU} CPUs disponíveis")

    logger.logger.info(f"🚀 Executando {len(project_dirs)} projetos em paralelo com {MAX_WORKERS} workers")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_PROJECTS) as executor:
        futures = {executor.submit(process_project, proj, ctrl): proj for proj in project_dirs}
        for future in as_completed(futures):
            project = futures[future]
            try:
                project_name, success, num_files = future.result()
                results.append((project_name, success, num_files))
                logger.logger.info(f"✅ Projeto '{project_name}' finalizado com sucesso com {num_files} arquivos")
            except Exception as e:
                logger.logger.error(f"❌ Erro ao processar projeto '{project}': {e}")
            

    
    # Relatório final global
    logger.start_phase('STATS', "Compilando estatísticas finais globais")
    
    """global_elapsed = time.time() - global_start_time
    
    # Prepara estatísticas detalhadas
    stats = {
        'Projetos processados': projects_processed,
        'Projetos movidos': projects_moved,
        'Total de extrações bem-sucedidas': global_success_count,
        'Total de extrações com erro': global_error_count,
        'Tempo total de execução': f"{global_elapsed:.2f}s",
        'Tempo médio por projeto': f"{global_elapsed/projects_processed:.2f}s" if projects_processed > 0 else "N/A",
        'Concluído em': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    # Log das estatísticas
    logger.log_statistics(stats)
    
    if global_success_count > 0:
        success_rate = (global_success_count / (global_success_count + global_error_count)) * 100
        stats['Taxa de sucesso global'] = f"{success_rate:.1f}%"""
    
    
    
    total_success = sum(r[2] for r in results if r[1])
    total_errors = len(project_dirs) - sum(1 for r in results if r[1])
    total_runtime = time.time() - global_start_time

    stats = {
        'Projetos processados': len(project_dirs),
        'Projetos com sucesso': len([r for r in results if r[1]]),
        'Projetos com erro': total_errors,
        'Arquivos extraídos com sucesso': total_success,
        'Tempo total de execução': f"{total_runtime:.2f}s",
        'Concluído em': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    logger.log_statistics(stats)

    
    logger.end_phase('STATS', True)
    
    # Log final com detalhamento de projetos pendentes
    total_runtime = logger.get_total_runtime()
    logger.logger.info("="*100)
    logger.logger.info("🎉 PROCESSAMENTO GLOBAL FINALIZADO!")
    logger.logger.info(f"📊 Projetos processados nesta execução: {projects_processed}")
    logger.logger.info(f"📦 Projetos movidos para Processados: {projects_moved}")
    logger.logger.info(f"📁 Pasta Processados: {processados_dir}")
    logger.logger.info(f"⏱️ Tempo total de execução: {total_runtime:.2f}s")
    logger.logger.info(f"📊 Taxa de sucesso final: {stats.get('Taxa de sucesso global', 'N/A')}")
    
    # Verifica se ainda há pastas pendentes para processar
    try:
        remaining_projects = []
        for item in os.listdir(PDF_BASE_PATH):
            item_path = os.path.join(PDF_BASE_PATH, item)
            if os.path.isdir(item_path) and item.lower() != 'processados':
                pdf_files_in_dir = glob.glob(f"{item_path}/*.pdf")
                if pdf_files_in_dir:
                    remaining_projects.append(item)
        
        if remaining_projects:
            logger.logger.info("="*100)
            logger.logger.info(f"⚠️ AINDA HÁ {len(remaining_projects)} PROJETO(S) PENDENTE(S):")
            for project in sorted(remaining_projects)[:5]:
                pdf_count = len(glob.glob(f"{PDF_BASE_PATH}/{project}/*.pdf"))
                logger.logger.info(f"   📁 {project} ({pdf_count} PDFs)")
            if len(remaining_projects) > 5:
                logger.logger.info(f"   ... e mais {len(remaining_projects) - 5} projetos")
            logger.logger.info("💡 Execute novamente para continuar o processamento!")
        else:
            logger.logger.info("="*100)
            logger.logger.info("✅ TODOS OS PROJETOS FORAM PROCESSADOS!")
            logger.logger.info("🎯 Não há mais pastas pendentes para processar.")
            
            # Mostra estatísticas finais da pasta Processados
            if os.path.exists(processados_dir):
                all_processed = [f for f in os.listdir(processados_dir) if os.path.isdir(os.path.join(processados_dir, f))]
                logger.logger.info(f"📊 Total geral de projetos processados: {len(all_processed)}")
                
    except Exception as e:
        logger.logger.warning(f"⚠️ Erro ao verificar projetos pendentes: {e}")
    
    logger.logger.info("="*100)
