# -*- coding: utf-8 -*-
"""
Extração usando OpenAI Vision API ASSÍNCRONA - Para PDFs complexos ou com formatação especial
Biblioteca: openai, pdf2image, asyncio
Instalação: pip install openai pdf2image pillow
Configuração: Definir OPENAI_API_KEY como variável de ambiente
"""
import os
import sys
import base64
from httpx import get
from openai import api_key, OpenAI
from pdf2image import convert_from_path
import logging
import time
from pathlib import Path
import dotenv
import json
from datetime import datetime
import io
import dotenv
import glob
import tempfile
# ==================== CONFIGURAÇÃO DO SISTEMA ====================
# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

dotenv.load_dotenv()


def _configurar_logging_basico() -> None:
    """Configuração básica de logging como fallback."""
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"Extracao_openai_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

# Configuração inicial
_configurar_logging_basico()

def get_env_path(var: str, default: str) -> str:
    """Lê um caminho do .env, normalizando separadores e expandindo user/home."""
    val = dotenv.get_key(dotenv.find_dotenv(), var)
    if not val:
        val = os.environ.get(var, default)
    return os.path.normpath(os.path.expanduser(val))

pdf_base_path = get_env_path('PDF_BASE_PATH', './extracoes/pdfs')
results_base_path = get_env_path('RESULTS_BASE_PATH', './extracoes/resultados')
processados_dir = get_env_path('PROCESSADOS_PATH', './extracoes/pdfs/Processados')
current_project = get_env_path('CURRENT_PROJECT', None)
api_key = get_env_path('OPENAI_API_KEY', None)

def encode_image_to_base64(image_path):
    """Converte imagem para base64 para enviar à API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_structured_openai_vision(pdf_path, output_path, api_key=None, logging=None):
    """
    Extração estruturada usando OpenAI Vision com prompts especializados
    """
    
    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY', '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')
    
    if not api_key:
        return False
    client = OpenAI(api_key=api_key)
    
    try:
        # Fase de análise estruturada
        logging.info(f"Análise estruturada de {os.path.basename(pdf_path)}")
        logging.info(f"🧠 Iniciando extração estruturada...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Cria subpasta para PNGs para evitar conflito com arquivos .ppm
            png_dir = os.path.join(temp_dir, "pngs")
            os.makedirs(png_dir, exist_ok=True)
            pages = convert_from_path(pdf_path, dpi=300)
            logging.info(f"📄 Convertido: {len(pages)} páginas para análise estruturada")

            results = []
            results.append("=== ANÁLISE ESTRUTURADA OPENAI VISION ===\n")
            results.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            results.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            results.append("="*50 + "\n\n")

            # Analisa todo o documento primeiro
            if len(pages) > 0:
                logging.info(f"Análise geral do documento: {os.path.basename(pdf_path)}")

            # Extrai dados estruturados de cada página e consolida para JSON único
            json_consolidado = {
                "arquivo": os.path.basename(pdf_path),
                "data_hora": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                "paginas": []
            }
            for i, page in enumerate(pages, 1):
                logging.info(f"TEXT_PROC | {i + 1}/{len(pages) + 1} | Página {i} | Dados estruturados")
                page_path = os.path.join(png_dir, f"page_{i}.png")
                page.save(page_path, "PNG")
                base64_image = encode_image_to_base64(page_path)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Você é um assistente extrator de informações de boletos, comprovantes de pagamento, etc."},
                        {"role": "system", "content": (
                            "Você é um assistente jurídico especializado na extração de informações "
                            "de documentos diversos como contratos, boletos, notas fiscais e prints. "
                        )},
                        {"role": "user",   "content": "Você irá analisar cada página do documento e extrair informações estruturadas. Arquivos como boletos podem conter informações relevantes como data de vencimento, valor de pagamento, data de processamento, descrição, deduções, multas, juros, data do documento, nosso numero, número do documento, data de emissão, data de processamento, data de vencimento, valor do documento, valor pago, valor da multa, valor dos juros, valor total a pagar, valor do desconto, data do desconto, data de compensação, data de baixa. Em arquivos como comprovantes de pagamento, extratos bancários, etc., extraia informações como data de transação, valor, descrição, saldo, data de credito, data de solicitação, desconto, juros. Sempre responda em JSON com os campos extraídos."},
                        {"role": "assistant", "content": "Claro! Pode me fornecer o texto ou imagem?"},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extraia informações estruturadas desta página:
                                    - Tipo de documento (contrato, nota fiscal, relatório, boleto, print, tabela, tela de software)
                                    - Datas encontradas, detalhes como vencimento, emissão, processamento, pagamento, solicitação, compensação, baixa
                                    - Valores monetários detalhados, incluindo:
                                        - Valor do documento
                                        - Valor pago
                                        - Valor da multa
                                        - Valor dos juros
                                        - Valor total a pagar
                                        - Valor do desconto
                                        - Data do desconto
                                        - Data de compensação
                                        - Data de baixa
                                    - Nomes de pessoas/empresas
                                    - Números de documentos (nosso número, número do documento)
                                    - Tabelas completas 
                                    
                                    Organize as informações de forma clara e estruturada."""
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
                    temperature=0.1
                )
                structured_data = response.choices[0].message.content
                results.append(f"=== DADOS ESTRUTURADOS - PÁGINA {i} ===\n")
                results.append(structured_data)
                results.append(f"\n\n{'='*40}\n\n")

                # Adiciona ao consolidado
                try:
                    parsed_json = json.loads(structured_data)
                except Exception:
                    parsed_json = {"raw": structured_data}
                json_consolidado["paginas"].append({
                    "pagina": i,
                    "dados": parsed_json
                })

            # Salva o consolidado JSON ao final
            json_output_path = os.path.splitext(output_path)[0] + ".json"
            with open(json_output_path, "w", encoding="utf-8") as jf:
                json.dump(json_consolidado, jf, ensure_ascii=False, indent=2)
            if logging:
                file_size_json = os.path.getsize(json_output_path)
                logging.info("save", json_output_path, True, file_size_json)
                logging.info(f"Arquivo JSON consolidado salvo: {json_output_path}")
        """response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """"""Analise este documento e identifique:
                                    1. Tipo de documento (contrato, nota fiscal, relatório, etc.)
                                    2. Principais seções ou partes
                                    3. Informações-chave visíveis
                                    4. Estrutura geral do documento
                                    5. Qualidade da imagem/texto (legível, borrado, escaneado, etc.)
                                    
                                    Seja detalhado na análise.""""""
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
                    max_tokens=1000,
                    temperature=0.2
                )
                
        analysis = response.choices[0].message.content
        results.append("=== ANÁLISE GERAL DO DOCUMENTO ===\n")
        results.append(analysis)
        results.append(f"\n\n{'='*40}\n\n")"""
        
        
        # Salva os resultados em um arquivo de texto
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(results))
        
            file_size = os.path.getsize(output_path)
            logging.info("save", output_path, True, file_size)
            logging.info('FILE_SAVE', True)
        
        logging.info(f"✅ Análise estruturada concluída: {output_path}")
        return True
    except Exception as e:
        logging.error(f"❌ Erro na análise estruturada: {e}")

def get_project_dirs(pdf_base_path: str, current_project: str, logging) -> list:
    if not os.path.isdir(pdf_base_path):
        logging.error(f"❌ PDF_BASE_PATH não é um diretório válido: {pdf_base_path}")
        return []
    logging.info(f"🔎 Iterando na pasta de PDFs: {pdf_base_path}")
    if current_project:
        project_path = os.path.join(pdf_base_path, current_project)
        if os.path.exists(project_path):
            return [os.path.abspath(project_path)]
        logging.error(f"❌ Pasta do projeto {current_project} não encontrada")
        return []
    # Batch mode: retorna todos os caminhos absolutos das subpastas exceto Processados
    dirs = []
    for item in os.listdir(pdf_base_path):
        item_path = os.path.join(pdf_base_path, item)
        if os.path.isdir(item_path) and item.lower() != 'processados':
            dirs.append(os.path.abspath(item_path))
    return sorted(dirs)
def get_pending_projects():
        pending = []
        try:
            for item in os.listdir(pdf_base_path):
                item_path = os.path.join(pdf_base_path, item)
                if os.path.isdir(item_path) and item.lower() != 'processados':
                    # Verifica se a pasta contém PDFs
                    pdf_files_in_dir = glob.glob(f"{item_path}/*.pdf")
                    if pdf_files_in_dir:
                        pending.append(item)
        except OSError as e:
            logging.info['PDF_SCAN'].error(f"❌ Erro ao escanear pastas: {e}")
            
        return sorted(pending)
        
        
        
def process_project(project_name: str, pdf_base_path: str, results_base_path: str, processados_dir: str, logging) -> dict:
    import glob, shutil
    project_pdf_path = os.path.join(pdf_base_path, project_name)
    logging.info(f"caminho do projeto: {project_pdf_path}")
    pdf_files = glob.glob(f"{project_pdf_path}/*.pdf")
    if not pdf_files:
        logging.warning(f"⚠️ Nenhum PDF encontrado em {project_name}, pulando...")
        return None
    logging.info(f"📄 PDFs encontrados em {project_name}: {len(pdf_files)}")
    for i, pdf_file in enumerate(pdf_files, 1):
        file_size = os.path.getsize(pdf_file) / 1024
        logging.info(f"   {i:2d}. {os.path.basename(pdf_file)} ({file_size:.1f} KB)")
    project_output_dir = os.path.join(results_base_path, project_name)
    os.makedirs(project_output_dir, exist_ok=True)
    logging.info(f"📁 Diretório de resultados: {project_output_dir}")
    project_success_count = 0
    project_error_count = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        filename = os.path.splitext(os.path.basename(pdf_file))[0]
        logging.info("─" * 80)
        logging.info(f"📄 PROCESSANDO PDF [{i}/{len(pdf_files)}]: {filename}")
        logging.info(f"📂 Arquivo: {pdf_file}")
        logging.info("─" * 80)
        pdf_dir = os.path.join(project_output_dir, filename)
        os.makedirs(pdf_dir, exist_ok=True)
        logging.info(f"📁 Pasta de saída: {pdf_dir}")
        structured_output = os.path.join(pdf_dir, f"openai_structured_{filename}.txt")
        logging.info(f"🧠 ANÁLISE ESTRUTURADA OpenAI Vision...")
        logging.info(f"💾 Saída: {structured_output}")
        # Função de extração estruturada deve ser definida no topo do arquivo
        if extract_structured_openai_vision(pdf_file, structured_output, logging=logging):
            logging.info(f"✅ Análise estruturada concluída")
            project_success_count += 1
        else:
            logging.error(f"❌ Falha na análise estruturada")
            project_error_count += 1
    # Move projeto para pasta Processados
    logging.info("📦 MOVENDO PROJETO PARA PROCESSADOS...")
    try:
        processados_project_dir = os.path.join(processados_dir, project_name)
        if os.path.exists(processados_project_dir):
            shutil.rmtree(processados_project_dir)
        shutil.move(project_pdf_path, processados_project_dir)
        logging.info(f"✅ PDFs movidos para: {processados_project_dir}")
        processados_results_dir = os.path.join(processados_project_dir, "resultados")
        # Remove subpasta de resultados de destino se já existir para evitar duplicação
        if os.path.exists(processados_results_dir):
            shutil.rmtree(processados_results_dir)
        shutil.move(project_output_dir, processados_results_dir)
        logging.info(f"✅ Resultados movidos para: {processados_results_dir}")
        # Verifica se o JSON consolidado foi movido junto
        for root, _, files in os.walk(processados_results_dir):
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    if not os.path.exists(json_path):
                        logging.warning(f"⚠️ Arquivo JSON não encontrado em {json_path} após mover resultados!")
    except Exception as e:
        logging.error(f"❌ Erro ao mover projeto {project_name}: {e}")
        logging.info(f"⚠️ Projeto processado mas não foi movido")
    return {
        'project': project_name,
        'success': project_success_count,
        'error': project_error_count,
        'pdfs': len(pdf_files)
    }

def main():

    # Inicializa logger padrão
    logger = logging.getLogger("openai_vision")
    logger.info("🔄 Iniciando extração estruturada OpenAI Vision")

    # Lê caminhos do .env
    pdf_base_path = get_env_path('PDF_BASE_PATH', './extracoes/pdfs')
    results_base_path = get_env_path('RESULTS_BASE_PATH', './extracoes/pdfs/Processados')
    processados_dir = get_env_path('PROCESSADOS_PATH', os.path.join(pdf_base_path, 'Processados'))
    current_project = get_env_path('CURRENT_PROJECT', None)

    logger.info(f"📂 Pasta PDFs: {pdf_base_path}")
    logger.info(f"💾 Pasta resultados: {results_base_path}")
    logger.info(f"📦 Pasta Processados: {processados_dir}")

    if not os.path.exists(pdf_base_path):
        logger.error(f"❌ Pasta base de PDFs não encontrada: {pdf_base_path}")
        return
    os.makedirs(results_base_path, exist_ok=True)
    os.makedirs(processados_dir, exist_ok=True)


    # Descobre apenas projetos com PDFs pendentes
    pending_projects = get_pending_projects()
    if not pending_projects:
        logger.info(f"✅ TODAS AS PASTAS JÁ FORAM PROCESSADAS!")
        logger.info(f"📁 Não há novos projetos para processar em {pdf_base_path}")
        return

    logger.info(f"📂 PASTAS DE PROJETOS ENCONTRADAS: {len(pending_projects)}")
    for i, project_dir in enumerate(pending_projects, 1):
        pdf_count = len([f for f in os.listdir(os.path.join(pdf_base_path, project_dir)) if f.endswith('.pdf')])
        logger.info(f"   {i:2d}. {project_dir} ({pdf_count} PDFs)")

    global_start_time = time.time()
    stats = []
    for project_name in pending_projects:
        logger.info("="*100)
        logger.info(f"🚀 PROCESSANDO PROJETO: {project_name}")
        logger.info("="*100)
        result = process_project(project_name, pdf_base_path, results_base_path, processados_dir, logger)
        if result:
            stats.append(result)

    # Relatório final
    global_elapsed = time.time() - global_start_time
    total_success = sum(s['success'] for s in stats)
    total_error = sum(s['error'] for s in stats)
    total_projects = len(stats)
    logger.info("📊 RELATÓRIO FINAL:")
    logger.info(f"Projetos processados: {total_projects}")
    logger.info(f"Total de extrações bem-sucedidas: {total_success}")
    logger.info(f"Total de extrações com erro: {total_error}")
    logger.info(f"Tempo total de execução: {global_elapsed:.2f}s")
    logger.info(f"Concluído em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    main()


