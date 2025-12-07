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
from pdf2image import convert_from_path
import tempfile
import asyncio
import aiohttp
import concurrent.futures
from functools import partial
import logging
import time
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import json
from datetime import datetime

# Configuração do sistema de logging estruturado
class StructuredLogger:
    def __init__(self, project_name="openai_vision", log_dir="logs"):
        
        self.project_name = project_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configurar formatador estruturado
        log_format = '%(asctime)s | %(levelname)8s | %(name)15s | %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Logger principal
        self.logger = logging.getLogger(f'openai_vision_{project_name}')
        self.logger.setLevel(logging.DEBUG)
        
        # Remover handlers existentes para evitar duplicação
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler para arquivo de log geral
        log_file = self.log_dir / f"{project_name}_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Handler para console com cores
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        self.logger.addHandler(console_handler)
        
        # Loggers especializados por fase
        self.phases = {
            'INIT': logging.getLogger(f'openai_vision_{project_name}.init'),
            'PDF_SCAN': logging.getLogger(f'openai_vision_{project_name}.pdf_scan'),
            'PDF_CONV': logging.getLogger(f'openai_vision_{project_name}.pdf_convert'),
            'API_CALL': logging.getLogger(f'openai_vision_{project_name}.api_call'),
            'TEXT_PROC': logging.getLogger(f'openai_vision_{project_name}.text_process'),
            'FILE_SAVE': logging.getLogger(f'openai_vision_{project_name}.file_save'),
            'STATS': logging.getLogger(f'openai_vision_{project_name}.statistics')
        }
        
        # Configurar todos os loggers de fase (evita duplicidade de handlers)
        for phase_logger in self.phases.values():
            phase_logger.setLevel(logging.DEBUG)
            if not phase_logger.handlers:
                phase_logger.addHandler(file_handler)
                phase_logger.addHandler(console_handler)
        
        self.start_time = time.time()
        self.phase_times = {}
        
        # Log inicial
        self.logger.info("="*80)
        self.logger.info(f"🚀 SISTEMA DE LOGGING INICIADO - {project_name.upper()}")
        self.logger.info(f"📁 Log salvo em: {log_file}")
        self.logger.info("="*80)
    
    def start_phase(self, phase_name, description=""):
        """Inicia uma nova fase de processamento"""
        if phase_name in self.phase_times:
            # Finaliza fase anterior se ainda estiver ativa
            self.end_phase(phase_name)
        
        self.phase_times[phase_name] = time.time()
        phase_logger = self.phases.get(phase_name, self.logger)
        
        message = f"🔄 INICIANDO FASE: {phase_name}"
        if description:
            message += f" - {description}"
        
        phase_logger.info("─" * 60)
        phase_logger.info(message)
        phase_logger.info("─" * 60)
    
    def end_phase(self, phase_name, success=True):
        """Finaliza uma fase de processamento"""
        if phase_name not in self.phase_times:
            return
        
        duration = time.time() - self.phase_times[phase_name]
        del self.phase_times[phase_name]
        
        phase_logger = self.phases.get(phase_name, self.logger)
        status = "✅ CONCLUÍDA" if success else "❌ FALHOU"
        
        phase_logger.info(f"{status} FASE: {phase_name} ({duration:.2f}s)")
        phase_logger.info("─" * 60)
    
    def log_progress(self, phase_name, current, total, item_name="", extra_info=""):
        """Log de progresso durante uma fase"""
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
        """Log específico para chamadas da API"""
        api_logger = self.phases['API_CALL']
        
        if status == "enviando":
            api_logger.info(f"🤖 API Call [{page_num}/{total_pages}] - Enviando página para OpenAI Vision...")
        elif status == "sucesso":
            api_logger.info(f"✅ API Call [{page_num}/{total_pages}] - Resposta recebida: {response_size} caracteres")
        elif status == "erro":
            api_logger.error(f"❌ API Call [{page_num}/{total_pages}] - ERRO: {error}")
    
    def log_file_operation(self, operation, file_path, success=True, size=0, error=None):
        """Log para operações de arquivo"""
        file_logger = self.phases['FILE_SAVE']
        
        if operation == "save" and success:
            file_logger.info(f"💾 Arquivo salvo: {Path(file_path).name} ({size} bytes)")
        elif operation == "save" and not success:
            file_logger.error(f"❌ Erro ao salvar: {Path(file_path).name} - {error}")
        elif operation == "load":
            file_logger.info(f"📂 Carregando: {Path(file_path).name}")
    
    def log_statistics(self, stats_dict):
        """Log de estatísticas finais"""
        stats_logger = self.phases['STATS']
        stats_logger.info("📊 ESTATÍSTICAS FINAIS:")
        
        for key, value in stats_dict.items():
            stats_logger.info(f"   {key}: {value}")
    
    def get_total_runtime(self):
        """Retorna o tempo total de execução"""
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

def encode_image_to_base64(image_path):
    """Converte imagem para base64 para enviar à API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def process_page_async(client, page_image_data, page_num, total_pages, prompt_text, logger=None):
    """Processa uma página de forma assíncrona"""
    try:
        if logger:
            logger.log_api_call(page_num, total_pages, "enviando")
        else:
            print(f"   🤖 [{page_num}/{total_pages}] Enviando para OpenAI Vision API...")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
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
            max_tokens=4000,
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

async def extract_text_openai_vision_async(pdf_path, txt_path, api_key=None, max_concurrent=3, logger=None):
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
            logger.phases['INIT'].info(f"⚡ Máximo de requisições simultâneas: {max_concurrent}")
        
        client = AsyncOpenAI(api_key=api_key)
        
        if not logger:
            print(f"🤖 Iniciando extração OpenAI Vision ASSÍNCRONA para {os.path.basename(pdf_path)}...")
            print(f"🔑 API Key configurada: {api_key[:20]}...")
            print(f"⚡ Máximo de requisições simultâneas: {max_concurrent}")
        
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
            
            # Fase de preparação das páginas
            if logger:
                logger.end_phase('PDF_CONV', True)
                logger.start_phase('TEXT_PROC', "Preparando páginas para processamento")
            
            page_data = []
            prompt_text = """Extraia todo o texto visível nesta imagem de documento PDF. 
                            Mantenha a formatação original o máximo possível, incluindo quebras de linha, 
                            espaçamentos e estrutura do documento. Se houver tabelas, preserve a estrutura tabular.
                            Retorne apenas o texto extraído, sem comentários adicionais."""
            
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
            
            # Cria semáforo para limitar requisições simultâneas
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(page_num, image_data):
                async with semaphore:
                    return await process_page_async(client, image_data, page_num, len(pages), prompt_text, logger)
            
            # Processa todas as páginas em paralelo
            tasks = [process_with_semaphore(page_num, image_data) for page_num, image_data in page_data]
            results = await asyncio.gather(*tasks)
            
            # Fase de salvamento
            if logger:
                logger.end_phase('API_CALL', True)
                logger.start_phase('FILE_SAVE', "Organizando e salvando resultados")
            
            # Organiza resultados
            extracted_text = []
            extracted_text.append("=== EXTRAÇÃO OPENAI VISION API (ASSÍNCRONA) ===\n")
            extracted_text.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            extracted_text.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            extracted_text.append(f"Páginas processadas: {len(pages)}\n")
            extracted_text.append(f"Processamento: PARALELO ({max_concurrent} requisições simultâneas)\n")
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
        
        # Salva resultado
        if logger:
            logger.phases['FILE_SAVE'].info(f"💾 Salvando resultado em: {txt_path}")
        else:
            print(f"💾 Salvando resultado em: {txt_path}")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(extracted_text))
        
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
                print(f"❌ Erro: Arquivo não foi criado")
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

def extract_text_openai_vision(pdf_path, txt_path, api_key=None, logger=None):
    """Wrapper síncrono para a função assíncrona"""
    return asyncio.run(extract_text_openai_vision_async(pdf_path, txt_path, api_key, max_concurrent=3, logger=logger))

def extract_structured_openai_vision(pdf_path, output_path, api_key=None, logger=None):
    """
    Extração estruturada usando OpenAI Vision com prompts especializados
    """
    if not OPENAI_AVAILABLE:
        return False
    
    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY', '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')
    
    if not api_key:
        return False
    
    try:
        # Fase de análise estruturada
        if logger:
            logger.start_phase('TEXT_PROC', f"Análise estruturada de {os.path.basename(pdf_path)}")
        
        # Usando cliente síncrono para extração estruturada (menos páginas, mais detalhada)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        if logger:
            logger.phases['TEXT_PROC'].info(f"🧠 Iniciando extração estruturada...")
        else:
            print(f"🧠 Extração estruturada OpenAI Vision para {os.path.basename(pdf_path)}...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pages = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir)
            
            if logger:
                logger.phases['TEXT_PROC'].info(f"📄 Convertido: {len(pages)} páginas para análise estruturada")
            
            results = []
            results_analise = []
            results.append("=== ANÁLISE ESTRUTURADA OPENAI VISION ===\n")
            results.append(f"Arquivo: {os.path.basename(pdf_path)}\n")
            results.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            results.append("="*50 + "\n\n")
            
            # Analisa todo o documento primeiro
            if len(pages) > 0:
                if logger:
                    logger.log_progress('TEXT_PROC', 1, len(pages) + 1, "Análise geral do documento", "Primeira página")
                
                # Extrai dados estruturados de cada página
            for i, page in enumerate(pages, 1):
                page_path = os.path.join(temp_dir, f"page_{i}.png")
                page.save(page_path, "PNG")
                base64_image = encode_image_to_base64(page_path)
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Analise este documento e identifique:
                                    1. Tipo de documento (boleto, nota fiscal, comprovante pagamento, etc.)
                                    2. Principais seções ou partes
                                    3. Informações-chave visíveis
                                    4. Estrutura geral do documento
                                    5. Possíveis tabelas ou listas
                                    6. Qualquer informação relevante que possa ser extraída
                                    7. Valores monetários, datas, nomes, números de documentos, etc.

                                    Seja detalhado na análise."""
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
                
                analysis = response.choices[0].message.content
                results_analise.append("=== ANÁLISE GERAL DO DOCUMENTO ===\n")
                results_analise.append(analysis)
                results_analise.append(f"\n\n{'='*40}\n\n")
                
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "system", "content": "Você é um assistente especializado na analise, entendimento, extração de informações e estruturação de documentos."},

                        {"role": "user", "content": "Você irá analisar o documento e estruturar as informações de maneira clara e organizada."},
                        {"role": "user", "content": f"{results_analise}"}
                    ],
                    temperature=0.2
                )
            analysis_result = response.choices[0].message.content
            results.append(f"=== ANÁLISE GERAL DO DOCUMENTO - PÁGINA {i} ===\n")
            results.append(analysis_result)
            results.append(f"\n\n{'='*40}\n\n")
                

            # Extrai dados estruturados de cada página
            for i, page in enumerate(pages, 1):
                if logger:
                    logger.log_progress('TEXT_PROC', i + 1, len(pages) + 1, f"Página {i}", "Dados estruturados")
                
                page_path = os.path.join(temp_dir, f"page_{i}.png")
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
                        {"role": "user",   "content": "Você irá analisar cada página do documento e extrair informações estruturadas. Arquivos como boletos podem conter informações relevantes como data de vencimento, valor de pagamento, data de processamento, descrição, deduções, multas, juros, data do documento, nosso numero, número do documento, data de emissão, data de processamento, data de vencimento, valor do documento, valor pago, valor da multa, valor dos juros, valor total a pagar, valor do desconto, data do desconto, data de compensação, data de baixa. Em arquivos como comprovantes de pagamento, extratos bancários, etc., extraia informações como data de transação, valor, descrição, saldo, data de credito, data de solicitação, desconto, juros."},
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
                    temperature=0.2
                )
                
                structured_data = response.choices[0].message.content
                results.append(f"=== DADOS ESTRUTURADOS - PÁGINA {i} ===\n")
                results.append(structured_data)
                results.append(f"\n\n{'='*40}\n\n")
        
        # Salva resultado estruturado
        if logger:
            logger.end_phase('TEXT_PROC', True)
            logger.start_phase('FILE_SAVE', "Salvando análise estruturada")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(results))
        
        if logger:
            file_size = os.path.getsize(output_path)
            logger.log_file_operation("save", output_path, True, file_size)
            logger.end_phase('FILE_SAVE', True)
        else:
            print(f"✅ OpenAI Vision Estruturado: Resultado salvo em {output_path}")
        
        return True
        
    except Exception as e:
        if logger:
            logger.phases['TEXT_PROC'].error(f"❌ Erro na extração estruturada OpenAI: {e}")
            # Finaliza fases ativas
            for phase in logger.phase_times.keys():
                logger.end_phase(phase, False)
        else:
            print(f"❌ Erro na extração estruturada OpenAI: {e}")
        return False

# Sistema multiprojeto com logs detalhados
if __name__ == "__main__":
    import glob
    import time
    import shutil
    
    # Configuração inicial
    current_project = os.environ.get('CURRENT_PROJECT', None)
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../resultados')
    
    # Inicializa sistema de logging
    if current_project:
        logger = get_logger(current_project)
    else:
        logger = get_logger("batch_processing")
    
    logger.start_phase('INIT', "Configuração inicial do sistema")
    logger.phases['INIT'].info(f"📂 Pasta PDFs: {pdf_base_path}")
    logger.phases['INIT'].info(f"💾 Pasta resultados: {results_base_path}")
    
    # Verifica se a pasta base de PDFs existe
    if not os.path.exists(pdf_base_path):
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
                pdf_base_path = alt_path
                logger.phases['INIT'].info(f"✅ Encontrada em: {alt_path}")
                break
        else:
            logger.phases['INIT'].error("❌ Nenhuma pasta de PDFs encontrada")
            logger.phases['INIT'].info("📁 Caminhos testados:")
            for path in alternative_paths:
                logger.phases['INIT'].info(f"   - {path}")
            logger.end_phase('INIT', False)
            exit(1)
    
    logger.end_phase('INIT', True)
    logger.start_phase('PDF_SCAN', "Escaneando pastas de PDFs")
    
    # Se CURRENT_PROJECT está definido, processa apenas essa pasta
    if current_project:
        project_dirs = [current_project] if os.path.exists(f"{pdf_base_path}/{current_project}") else []
        if not project_dirs:
            logger.phases['PDF_SCAN'].error(f"❌ Pasta do projeto {current_project} não encontrada")
            logger.end_phase('PDF_SCAN', False)
            exit(1)
        logger.phases['PDF_SCAN'].info(f"🎯 MODO PROJETO ESPECÍFICO: Processando apenas {current_project}")
    else:
        # MODO BATCH: Processa TODAS as pastas de projetos (exceto Processados) até finalizar
        logger.phases['PDF_SCAN'].info(f"🚀 MODO BATCH COMPLETO: Processando todas as pastas até finalizar")
        
        # Função para descobrir pastas pendentes
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
                logger.phases['PDF_SCAN'].error(f"❌ Erro ao escanear pastas: {e}")
            return sorted(pending)
        
        # Descobre todas as pastas pendentes
        project_dirs = get_pending_projects()
        
        if not project_dirs:
            logger.phases['PDF_SCAN'].info(f"✅ TODAS AS PASTAS JÁ FORAM PROCESSADAS!")
            logger.phases['PDF_SCAN'].info(f"📁 Não há novos projetos para processar em {pdf_base_path}")
            logger.end_phase('PDF_SCAN', True)
            
            # Mostra estatísticas da pasta Processados
            processados_path = f"{pdf_base_path}/Processados"
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
        pdf_count = len(glob.glob(f"{pdf_base_path}/{project_dir}/*.pdf"))
        logger.phases['PDF_SCAN'].info(f"   {i:2d}. {project_dir} ({pdf_count} PDFs)")
    
    logger.end_phase('PDF_SCAN', True)
    
    # Estatísticas globais
    global_start_time = time.time()
    global_success_count = 0
    global_error_count = 0
    projects_processed = 0
    projects_moved = 0
    
    # Cria pasta de processados se não existir
    processados_dir = f"{pdf_base_path}/Processados"
    os.makedirs(processados_dir, exist_ok=True)
    
    # Processa cada projeto
    for project_index, project_name in enumerate(project_dirs, 1):
        logger.logger.info("="*100)
        logger.logger.info(f"🚀 PROCESSANDO PROJETO [{project_index}/{len(project_dirs)}]: {project_name}")
        logger.logger.info("="*100)
        
        project_pdf_path = f"{pdf_base_path}/{project_name}"
        pdf_files = glob.glob(f"{project_pdf_path}/*.pdf")
        
        if not pdf_files:
            logger.logger.warning(f"⚠️ Nenhum PDF encontrado em {project_name}, pulando...")
            continue
        
        logger.logger.info(f"📄 PDFs encontrados em {project_name}: {len(pdf_files)}")
        for i, pdf_file in enumerate(pdf_files, 1):
            file_size = os.path.getsize(pdf_file) / 1024  # KB
            logger.logger.info(f"   {i:2d}. {os.path.basename(pdf_file)} ({file_size:.1f} KB)")
        
        # Cria diretório de resultados para o projeto
        project_output_dir = f"{results_base_path}/{project_name}"
        os.makedirs(project_output_dir, exist_ok=True)
        logger.logger.info(f"📁 Diretório de resultados: {project_output_dir}")
        
        # Estatísticas do projeto
        project_start_time = time.time()
        project_success_count = 0
        project_error_count = 0
        file_stats = []
        
        # Processa cada PDF do projeto
        for i, pdf_file in enumerate(pdf_files, 1):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            
            logger.logger.info("─" * 80)
            logger.logger.info(f"📄 PROCESSANDO PDF [{i}/{len(pdf_files)}]: {filename}")
            logger.logger.info(f"📂 Arquivo: {pdf_file}")
            logger.logger.info("─" * 80)
            
            pdf_dir = f"{project_output_dir}/{filename}"
            os.makedirs(pdf_dir, exist_ok=True)
            logger.logger.info(f"📁 Pasta de saída: {pdf_dir}")
            
            file_start_time = time.time()
            file_success = 0
            file_errors = 0
            
            """# Extração básica OpenAI Vision
            txt_output = f"{pdf_dir}/openai_vision_{filename}.txt"
            logger.logger.info(f"🤖 [1/2] EXTRAÇÃO BÁSICA OpenAI Vision...")
            logger.logger.info(f"💾 Saída: {txt_output}")
            
            if extract_text_openai_vision(pdf_file, txt_output, logger=logger):
                logger.logger.info(f"✅ Extração básica concluída")
                project_success_count += 1
                global_success_count += 1
                file_success += 1
            else:
                logger.logger.error(f"❌ Falha na extração básica")
                project_error_count += 1
                global_error_count += 1
                file_errors += 1
            """

            # Extração estruturada OpenAI Vision
            structured_output = f"{pdf_dir}/openai_structured_{filename}.txt"
            logger.logger.info(f"🧠 [2/2] ANÁLISE ESTRUTURADA OpenAI Vision...")
            logger.logger.info(f"💾 Saída: {structured_output}")
            
            if extract_structured_openai_vision(pdf_file, structured_output, logger=logger):
                logger.logger.info(f"✅ Análise estruturada concluída")
                project_success_count += 1
                global_success_count += 1
                file_success += 1
            else:
                logger.logger.error(f"❌ Falha na análise estruturada")
                project_error_count += 1
                global_error_count += 1
                file_errors += 1
            
            file_elapsed = time.time() - file_start_time
            logger.logger.info(f"⏱️ Tempo para {filename}: {file_elapsed:.2f}s")
            
            # Coleta estatísticas do arquivo
            file_stat = {
                'filename': filename,
                'time': file_elapsed,
                'success': file_success,
                'errors': file_errors,
                'basic_size': 0,
                'structured_size': 0
            }
            
            """# Verifica tamanhos dos arquivos gerados
            if os.path.exists(txt_output):
                size = os.path.getsize(txt_output)
                file_stat['basic_size'] = size
                logger.logger.info(f"📊 Extração básica: {size} bytes")"""
            
            if os.path.exists(structured_output):
                size = os.path.getsize(structured_output)
                file_stat['structured_size'] = size
                logger.logger.info(f"📊 Análise estruturada: {size} bytes")
            
            file_stats.append(file_stat)
        
        # Relatório do projeto
        project_elapsed = time.time() - project_start_time
        logger.logger.info("="*80)
        logger.logger.info(f"📋 RELATÓRIO DO PROJETO: {project_name}")
        logger.logger.info("="*80)
        logger.logger.info(f"📄 PDFs processados: {len(pdf_files)}")
        logger.logger.info(f"✅ Extrações bem-sucedidas: {project_success_count}")
        logger.logger.info(f"❌ Extrações com erro: {project_error_count}")
        logger.logger.info(f"⏱️ Tempo total do projeto: {project_elapsed:.2f}s")
        if len(pdf_files) > 0:
            logger.logger.info(f"⚡ Tempo médio por PDF: {project_elapsed/len(pdf_files):.2f}s")
        
        # Move projeto para pasta Processados
        logger.logger.info("📦 MOVENDO PROJETO PARA PROCESSADOS...")
        try:
            # Destino principal do projeto
            processados_project_dir = f"{processados_dir}/{project_name}"
            
            # Remove se já existir
            if os.path.exists(processados_project_dir):
                shutil.rmtree(processados_project_dir)
            
            # Move pasta de PDFs para Processados
            shutil.move(project_pdf_path, processados_project_dir)
            logger.logger.info(f"✅ PDFs movidos para: {processados_project_dir}")
            
            # Move pasta de resultados DENTRO da pasta do projeto
            processados_results_dir = f"{processados_project_dir}/resultados"
            shutil.move(project_output_dir, processados_results_dir)
            logger.logger.info(f"✅ Resultados movidos para: {processados_results_dir}")
            
            projects_moved += 1
            logger.logger.info(f"🎯 Projeto {project_name} processado e organizado com sucesso!")
            logger.logger.info(f"📁 Estrutura final: {processados_project_dir}/")
            logger.logger.info(f"   ├── PDFs originais")
            logger.logger.info(f"   └── resultados/ (extrações)")
            
        except Exception as e:
            logger.logger.error(f"❌ Erro ao mover projeto {project_name}: {e}")
            logger.logger.info(f"⚠️ Projeto processado mas não foi movido")
        
        projects_processed += 1
        logger.logger.info(f"📊 Progresso geral: {projects_processed}/{len(project_dirs)} projetos processados")
    
    # Relatório final global
    logger.start_phase('STATS', "Compilando estatísticas finais globais")
    
    global_elapsed = time.time() - global_start_time
    
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
    
    if global_success_count > 0:
        success_rate = (global_success_count / (global_success_count + global_error_count)) * 100
        stats['Taxa de sucesso global'] = f"{success_rate:.1f}%"
    
    # Log das estatísticas
    logger.log_statistics(stats)
    
    logger.end_phase('STATS', True)
    
    # Log final com detalhamento de projetos pendentes
    total_runtime = logger.get_total_runtime()
    logger.logger.info("="*100)
    logger.logger.info(f"🎉 PROCESSAMENTO GLOBAL FINALIZADO!")
    logger.logger.info(f"📊 Projetos processados nesta execução: {projects_processed}")
    logger.logger.info(f"📦 Projetos movidos para Processados: {projects_moved}")
    logger.logger.info(f"📁 Pasta Processados: {processados_dir}")
    logger.logger.info(f"⏱️ Tempo total de execução: {total_runtime:.2f}s")
    logger.logger.info(f"📊 Taxa de sucesso final: {stats.get('Taxa de sucesso global', 'N/A')}")
    
    # Verifica se ainda há pastas pendentes para processar
    try:
        remaining_projects = []
        for item in os.listdir(pdf_base_path):
            item_path = os.path.join(pdf_base_path, item)
            if os.path.isdir(item_path) and item.lower() != 'processados':
                pdf_files_in_dir = glob.glob(f"{item_path}/*.pdf")
                if pdf_files_in_dir:
                    remaining_projects.append(item)
        
        if remaining_projects:
            logger.logger.info("="*100)
            logger.logger.info(f"⚠️ AINDA HÁ {len(remaining_projects)} PROJETO(S) PENDENTE(S):")
            for project in sorted(remaining_projects)[:5]:
                pdf_count = len(glob.glob(f"{pdf_base_path}/{project}/*.pdf"))
                logger.logger.info(f"   📁 {project} ({pdf_count} PDFs)")
            if len(remaining_projects) > 5:
                logger.logger.info(f"   ... e mais {len(remaining_projects) - 5} projetos")
            logger.logger.info(f"💡 Execute novamente para continuar o processamento!")
        else:
            logger.logger.info("="*100)
            logger.logger.info("✅ TODOS OS PROJETOS FORAM PROCESSADOS!")
            logger.logger.info("🎯 Não há mais pastas pendentes para processar.")
            
            # Mostra estatísticas finais da pasta Processados
            if os.path.exists(processados_dir):
                all_processed = [f for f in os.listdir(processados_dir) 
                               if os.path.isdir(os.path.join(processados_dir, f))]
                logger.logger.info(f"📊 Total geral de projetos processados: {len(all_processed)}")
                
    except Exception as e:
        logger.logger.warning(f"⚠️ Erro ao verificar projetos pendentes: {e}")
    
    logger.logger.info("="*100)
