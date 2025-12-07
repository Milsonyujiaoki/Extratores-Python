from ast import Global
from calendar import c
import logging
from pathlib import Path

import sys
import datetime
import configparser
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from pdf2image import convert_from_path

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

def listar_xmls_hibrido(root: Path, max_workers: int = 4) -> list[Path]:
    
    
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
        logger.info(f"[MAIN.LISTAGEM_HIBRIDA.SCAN_DIR] Arquivos encontrados em {p}: {len(arquivos)}")
        return arquivos

    arquivos_pdfs = []
    subdirs = [Path(entry.path) for entry in os.scandir(root) if entry.is_dir()]
    arquivos_pdfs.extend([Path(entry.path) for entry in os.scandir(root) if entry.is_file() and entry.name.lower().endswith('.xml')])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_dir, subdir): subdir for subdir in subdirs}
        for f in as_completed(futures):
            arquivos_pdfs.extend(f.result())
    
    return arquivos_pdfs



def main():
    global logger, config
    logger, config = iniciando_configuracoes()
    """ Vou separar o Projeto em:
    1. Configuração e inicialização
    2. Encontrar todos arquivos PDF no diretório de entrada
    3. Transformar os PDFs em imagens com pdf2image
convert_from_path
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


if __name__ == "__main__":
    main()