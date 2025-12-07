import os
import sys
import csv
import re
import json
import base64
import shutil
import logging
import datetime
import configparser
import tempfile
import glob
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from pdf2image import convert_from_path


logger = logging.getLogger(__name__)


def verificar_pdf_valido(pdf_path: Path) -> Tuple[bool, str]:
    """
    Verifica se um arquivo PDF é válido e pode ser processado.
    Implementa retry em caso de arquivo em uso (WinError 32).
    
    Args:
        pdf_path: Caminho para o arquivo PDF a ser validado
        
    Returns:
        Tuple contendo (is_valid, error_message)
        - is_valid: True se o PDF é válido, False caso contrário
        - error_message: Mensagem descritiva do erro (se houver)
    """
    max_tentativas = 3
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            # Verifica se o arquivo existe e tem tamanho válido
            if not pdf_path.exists():
                return False, "Arquivo não encontrado"
            
            if pdf_path.stat().st_size == 0:
                return False, "Arquivo vazio"
            
            if pdf_path.stat().st_size < 100:  # PDFs muito pequenos são suspeitos
                return False, "Arquivo muito pequeno (possivelmente corrompido)"
            
            # Tenta converter apenas a primeira página para testar se o PDF é válido
            with tempfile.TemporaryDirectory() as temp_dir:
                pages = None
                try:
                    # Log para debug
                    if logger and tentativa > 1:
                        logger.debug(f"[VALIDACAO_PDF] Tentativa {tentativa}/{max_tentativas} para: {pdf_path}")
                    elif logger:
                        logger.debug(f"[VALIDACAO_PDF] Testando conversão de: {pdf_path}")
                        logger.debug(f"[VALIDACAO_PDF] Tamanho do arquivo: {pdf_path.stat().st_size} bytes")
                    
                    # Tenta converter apenas a primeira página
                    pages = convert_from_path(
                        str(pdf_path),  # Converte para string para evitar problemas com WindowsPath
                        dpi=150,  # DPI menor para teste rápido
                        first_page=1, 
                        last_page=1, 
                        output_folder=temp_dir,
                        timeout=30  # Timeout de 30 segundos
                    )
                    
                    if pages:
                        # IMPORTANTE: Fecha explicitamente cada página para liberar handles
                        for page in pages:
                            try:
                                page.close()
                            except Exception:
                                pass
                        # Pequeno delay para garantir que o Windows libere os handles
                        time.sleep(0.2)
                        return True, "PDF válido"
                    else:
                        return False, "PDF sem páginas válidas"
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Se for erro de arquivo em uso e ainda temos tentativas, tenta novamente
                    if 'winerror 32' in error_msg or 'sendo usado por outro processo' in error_msg:
                        if tentativa < max_tentativas:
                            if logger:
                                logger.warning(f"[VALIDACAO_PDF] Arquivo em uso (tentativa {tentativa}), aguardando...")
                            time.sleep(1.0 * tentativa)  # Delay progressivo
                            continue
                        else:
                            return False, f"Arquivo em uso após {max_tentativas} tentativas: {str(e)}"
                    
                    # Outros tipos de erro
                    if any(keyword in error_msg for keyword in [
                        'trailer dictionary', 'xref table', 'page count', 
                        'syntax error', 'not a pdf file', 'corrupted'
                    ]):
                        return False, f"PDF corrompido: {str(e)}"
                    else:
                        return False, f"Erro ao processar PDF: {str(e)}"
                finally:
                    # Garantia adicional de limpeza
                    if pages:
                        for page in pages:
                            try:
                                page.close()
                            except Exception:
                                pass
                    # Delay adicional para liberar handles no Windows
                    time.sleep(0.2)
                    
        except Exception as e:
            error_msg = str(e).lower()
            # Se for erro de arquivo em uso e ainda temos tentativas, tenta novamente
            if 'winerror 32' in error_msg or 'sendo usado por outro processo' in error_msg:
                if tentativa < max_tentativas:
                    if logger:
                        logger.warning(f"[VALIDACAO_PDF] Erro externo (tentativa {tentativa}): {str(e)}")
                    time.sleep(1.0 * tentativa)  # Delay progressivo
                    continue
                else:
                    return False, f"Erro persistente após {max_tentativas} tentativas: {str(e)}"
            else:
                return False, f"Erro na validação: {str(e)}"
    
    # Se chegou aqui, todas as tentativas falharam
    return False, f"Falha na validação após {max_tentativas} tentativas"

def verificar_arquivo_em_uso(file_path: Path) -> bool:
    """
    Verifica se um arquivo está sendo usado por outro processo.
    Retorna True se o arquivo estiver em uso, False caso contrário.
    """
    if not file_path.exists():
        return False
    
    try:
        # Tenta abrir o arquivo em modo exclusivo
        with open(file_path, "r+", encoding="utf-8") as test_file:
            pass
        return False  # Arquivo não está em uso
    except PermissionError:
        return True  # Arquivo está em uso
    except Exception:
        return False  # Outros erros, assumimos que não está em uso

def carregar_configuracoes() -> configparser.ConfigParser:
    """
    Carrega as configurações do arquivo config.ini.
    
    Returns:
        ConfigParser: Objeto com as configurações carregadas
        
    Raises:
        FileNotFoundError: Se o arquivo de configuração não for encontrado
        configparser.Error: Se houver erro na leitura do arquivo de configuração
    """
    config = configparser.ConfigParser()
    config_file = Path(r"C:\Users\Maoki\Dev_yuji\Projetos\extracoes\scripts\executaveis\config_process_pdfs.ini")
    
    if not config_file.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_file}")
    
    try:
        config.read(config_file, encoding='utf-8')
    except configparser.Error as e:
        raise configparser.Error(f"Erro ao ler arquivo de configuração: {e}")
    
    return config

def configurar_logger(config: configparser.ConfigParser) -> logging.Logger:
    """
    Configura o logger para registrar mensagens em um arquivo com timestamp.
    
    Args:
        config: Objeto ConfigParser com as configurações do sistema
        
    Returns:
        Logger: Objeto logger configurado
        
    Raises:
        Exception: Se houver erro na configuração do logger
    """
    try:
        log_dir = Path(config.get("Paths", "PATH_LOGS"))
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"Process_pdfs_{timestamp}.log"

        formato = "%(asctime)s - %(levelname)s - %(message)s"

        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,  # Mudou para DEBUG para capturar mais informações
            format=formato,
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True  # Força reconfiguração se já existe
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console em nível INFO
        console_handler.setFormatter(logging.Formatter(formato))
        logger = logging.getLogger("process_pdfs_openAI")
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)  # Logger principal em DEBUG
        return logger
    except Exception as e:
        logging.error(f"Erro ao configurar o logger: {e}")
        raise e

def iniciando_configuracoes() -> Tuple[logging.Logger, configparser.ConfigParser]:
    """
    Inicializa as configurações do sistema e o logger.
    
    Returns:
        Tuple contendo (logger, config)
        - logger: Logger configurado para o sistema
        - config: Configurações carregadas do arquivo INI
        
    Raises:
        Exception: Se houver erro na inicialização das configurações
    """
    logger = None
    try:
        # Carrega as configurações
        config = carregar_configuracoes()
        logger = configurar_logger(config)
        logger.info(f"[MAIN.CONFIG] Configurações carregadas com sucesso")
        
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
        
        return logger, config

    except Exception as e:
        if logger:
            logger.error(f"[MAIN] Erro ao iniciar o processamento: {e}")
        else:
            logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
            logging.error(f"[MAIN] Erro ao iniciar o processamento: {e}")
        raise e

def listar_pdfs_hibrido(root: Path, max_workers: int = 4) -> Tuple[List[Path], List[Path]]:
    """
    Busca recursiva de arquivos PDF usando os.scandir e multithreading.
    
    Args:
        root: Diretório raiz para busca
        max_workers: Número máximo de threads para paralelização
        
    Returns:
        Tuple contendo (arquivos_pdfs, subdirs)
        - arquivos_pdfs: Lista de caminhos para arquivos PDF encontrados
        - subdirs: Lista de subdiretórios encontrados
        
    Como funciona:
        - Paraleliza o primeiro nível de subdiretórios
        - Cada thread faz varredura recursiva em sua subárvore
        - O diretório raiz é varrido sequencialmente
        
    Vantagens:
        - Reduz overhead de threads
        - Aproveitamento máximo do I/O paralelo
        - Simples implementação, menos race conditions
        
    Desvantagens:
        - Se poucos subdiretórios grandes, paralelismo limitado
        - Se estrutura em um único nível, ganho pequeno
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

def listar_txts_jsons_hibrido(root: Path, max_workers: int = 4) -> Tuple[List[Path], List[Path]]:
    """
    Busca recursiva de arquivos TXT e JSON usando os.scandir e multithreading.
    
    Args:
        root: Diretório raiz para busca
        max_workers: Número máximo de threads para paralelização
        
    Returns:
        Tuple contendo (arquivos_txt_json, subdirs)
        - arquivos_txt_json: Lista de caminhos para arquivos TXT e JSON encontrados
        - subdirs: Lista de subdiretórios encontrados
    
    Note:
        Funciona de forma semelhante à função listar_pdfs_hibrido, 
        mas busca arquivos com extensões .txt e .json.
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

def gerar_csv_arquivos_pdfs(arquivos_pdfs: List[Path], subdirs: List[Path], path_csv: Path) -> None:
    """
    Salva todos os arquivos PDF encontrados em um arquivo CSV.
    
    Args:
        arquivos_pdfs: Lista de caminhos para arquivos PDF
        subdirs: Lista de subdiretórios encontrados
        path_csv: Caminho onde salvar o arquivo CSV
        
    Raises:
        PermissionError: Se o arquivo CSV estiver em uso ou sem permissão de escrita
        Exception: Outros erros durante o processamento
        
    Note:
        - Filtra arquivos com "print - contabilização.pdf" no nome
        - Evita duplicatas comparando registros existentes
        - Implementa sistema de retry com backup em caso de erro de permissão
        - Fallback para diretório temporário se necessário
    """
    try:
        if not arquivos_pdfs:
            logger.warning("[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Nenhum arquivo PDF encontrado.")
            return

        # Verifica se o arquivo CSV está sendo usado por outro processo
        if verificar_arquivo_em_uso(path_csv):
            logger.error(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] ❌ ARQUIVO EM USO: {path_csv}")
            logger.error("[MAIN.GERAR_CSV_ARQUIVOS_PDFS] ❌ Feche o arquivo no Excel, LibreOffice ou outro programa antes de continuar.")
            logger.error("[MAIN.GERAR_CSV_ARQUIVOS_PDFS] ❌ Após fechar o arquivo, execute o script novamente.")
            raise PermissionError(f"Arquivo está sendo usado por outro processo: {path_csv}")

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

        # Se não há subdirs, usa o diretório raiz como caminho_subdir
        if not subdirs:
            caminho_subdir_padrao = str(Path(arquivos_pdfs[0]).parent) if arquivos_pdfs else ""
            registros_novos = set()
            for pdf in arquivos_pdfs:
                nome = pdf.name
                if "print - contabilização.pdf" in nome.lower():
                    logger.info(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Pulando arquivo com 'Print' no nome: {nome}")
                    continue
                caminho_arquivo = str(pdf)
                caminho_subdir = caminho_subdir_padrao
                registros_novos.add((nome, caminho_arquivo, caminho_subdir))
        else:
            # Mapeia subdirs para busca rápida
            subdir_map = {subdir.name: str(subdir) for subdir in subdirs}
            registros_novos = set()
            for pdf in arquivos_pdfs:
                nome = pdf.name
                if "print - contabilização.pdf" in nome.lower():
                    logger.info(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Pulando arquivo com 'Print' no nome: {nome}")
                    continue
                caminho_arquivo = str(pdf)
                caminho_subdir = subdir_map.get(pdf.parent.name, str(pdf.parent))
                registros_novos.add((nome, caminho_arquivo, caminho_subdir))

        # Junta os registros existentes e novos, removendo duplicatas
        registros_unicos = registros_existentes.union(registros_novos)

        # Garante que o diretório do arquivo CSV existe
        csv_dir = Path(path_csv).parent
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        # Tenta escrever o CSV com tratamento robusto de erros
        csv_escrito = False
        tentativas = 0
        max_tentativas = 3
        
        while not csv_escrito and tentativas < max_tentativas:
            try:
                tentativas += 1
                logger.info(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Tentativa {tentativas} de escrever CSV: {path_csv}")
                
                # Se o arquivo existe e não é a primeira tentativa, tenta fazer backup
                if path_csv.exists() and tentativas > 1:
                    backup_path = path_csv.with_suffix(f'.backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                    try:
                        shutil.copy2(path_csv, backup_path)
                        logger.info(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Backup criado: {backup_path}")
                    except Exception as backup_error:
                        logger.warning(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Não foi possível criar backup: {backup_error}")
                
                with open(path_csv, "w", newline='', encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["nome", "caminho_arquivo", "caminho_subdir"])
                    for nome, caminho_arquivo, caminho_subdir in sorted(registros_unicos):
                        writer.writerow([nome, caminho_arquivo, caminho_subdir])
                csv_escrito = True
                logger.info(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] CSV escrito com sucesso na tentativa {tentativas}")
                
            except PermissionError as perm_error:
                if tentativas < max_tentativas:
                    logger.warning(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Erro de permissão na tentativa {tentativas}: {perm_error}")
                    time.sleep(2)  # Aguarda 2 segundos antes da próxima tentativa
                else:
                    # Se falhou todas as tentativas, usa diretório temporário
                    logger.error(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Falha após {max_tentativas} tentativas. Usando diretório temporário.")
                    temp_csv_path = Path.home() / "Documents" / f"csv_entrada_arquivos_temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    try:
                        with open(temp_csv_path, "w", newline='', encoding="utf-8") as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(["nome", "caminho_arquivo", "caminho_subdir"])
                            for nome, caminho_arquivo, caminho_subdir in sorted(registros_unicos):
                                writer.writerow([nome, caminho_arquivo, caminho_subdir])
                        csv_escrito = True
                        logger.warning(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] CSV salvo em local temporário: {temp_csv_path}")
                        logger.warning(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Mova o arquivo para o local correto: {path_csv}")
                    except Exception as temp_error:
                        logger.error(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Falha ao escrever em diretório temporário: {temp_error}")
                        raise perm_error
            except Exception as other_error:
                logger.error(f"[MAIN.GERAR_CSV_ARQUIVOS_PDFS] Erro inesperado na tentativa {tentativas}: {other_error}")
                if tentativas >= max_tentativas:
                    raise other_error
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

def gerar_txt_openAI(path_csv_entrada_arquivos: Path, api_key: str, diretorio_saida: Path = None):
    """
    Processa arquivos PDF listados no CSV, convertendo-os para TXT usando OpenAI Vision API.
    Inclui validação de PDFs e tratamento robusto de erros.
    
    Args:
        path_csv_entrada_arquivos: Caminho para o CSV com lista de PDFs
        api_key: Chave da API do OpenAI
        diretorio_saida: Diretório onde salvar os arquivos TXT (padrão: C:\saida\Resultados)
    """
    arquivos_processados = 0
    arquivos_pulados = 0
    arquivos_erro = 0
    
    # Define o diretório de saída - usa o padrão se não especificado
    if diretorio_saida is None:
        diretorio_saida = Path("C:/saida/Resultados")
    
    # Garante que o diretório de saída existe
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    logger.info(f"[MAIN.GERAR_TXT_JSON_OPENAI] 📁 Todos os arquivos TXT serão salvos em: {diretorio_saida}")
    
    try:
        # Primeira passagem para contar total de arquivos
        with open(path_csv_entrada_arquivos, "r", newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            total_arquivos = sum(1 for _ in reader)
            
        # Segunda passagem para processar arquivos
        with open(path_csv_entrada_arquivos, "r", newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            
            for idx, row in enumerate(reader, 1):
                nome_ = row.get("nome")
                nome = os.path.splitext(nome_)[0]  # Remove a extensão do nome
                
                # Pula arquivos com "print - contabilização.pdf" no nome (case-insensitive)
                if "print - contabilização.pdf" in nome.lower():
                    logger.info(f"[MAIN.GERAR_TXT_JSON_OPENAI] [{idx}/{total_arquivos}] Pulando arquivo com 'Print' no nome: {nome_}")
                    arquivos_pulados += 1
                    continue
                
                caminho_arquivo = row.get("caminho_arquivo")
                caminho_subdir = row.get("caminho_subdir")
                
                # MUDANÇA: Salva todos os TXTs no diretório único de saída
                # Usa o nome do arquivo PDF como nome do TXT (sem duplicação de pastas)
                txt_output = diretorio_saida / f"{nome}.txt"
                
                logger.info(f"[MAIN.GERAR_TXT_JSON_OPENAI] [{idx}/{total_arquivos}] Processando: {nome}")
                logger.debug(f"[MAIN.GERAR_TXT_JSON_OPENAI] Caminho PDF: {caminho_arquivo}")
                logger.debug(f"[MAIN.GERAR_TXT_JSON_OPENAI] Caminho TXT: {txt_output}")
                
                # VALIDAÇÃO DE PDF ANTES DO PROCESSAMENTO
                pdf_path = Path(caminho_arquivo)
                is_valid, error_message = verificar_pdf_valido(pdf_path)
                
                if not is_valid:
                    logger.warning(f"[MAIN.GERAR_TXT_JSON_OPENAI] ❌ PDF INVÁLIDO: {nome}")
                    logger.warning(f"[MAIN.GERAR_TXT_JSON_OPENAI] ❌ Caminho: {pdf_path}")
                    logger.warning(f"[MAIN.GERAR_TXT_JSON_OPENAI] ❌ Motivo: {error_message}")
                    
                    # Garante que o diretório de saída existe (já foi criado anteriormente, mas por segurança)
                    # txt_output.parent.mkdir(parents=True, exist_ok=True)  # Removido pois já criamos o diretório
                    
                    # Cria um arquivo TXT com informações do erro
                    try:
                        error_txt_content = f"""=== ERRO NO PROCESSAMENTO ===
Arquivo: {nome_}
Data/Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Motivo: PDF corrompido ou inválido
Detalhes: {error_message}
Caminho PDF: {pdf_path}
Status: ARQUIVO PULADO - NÃO PROCESSADO
==========================================
"""
                        with open(txt_output, "w", encoding="utf-8") as f:
                            f.write(error_txt_content)
                        logger.info(f"[MAIN.GERAR_TXT_JSON_OPENAI] ✅ Arquivo de erro criado: {txt_output}")
                    except Exception as txt_error:
                        logger.error(f"[MAIN.GERAR_TXT_JSON_OPENAI] Erro ao criar arquivo de erro: {txt_error}")
                    
                    arquivos_erro += 1
                    continue
                
                # Se chegou aqui, o PDF é válido - processa normalmente
                try:
                    client = OpenAI(api_key=api_key)
                    logger.info(f"[MAIN] Processando PDF válido: {nome} em {caminho_arquivo}")
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        try:
                            pages = convert_from_path(str(caminho_arquivo), dpi=300, output_folder=temp_dir)
                        except Exception as convert_error:
                            logger.error(f"[MAIN.GERAR_TXT_JSON_OPENAI] Erro na conversão PDF->Imagem: {convert_error}")
                            arquivos_erro += 1
                            continue
                        
                        results = []
                        results.append("=== ANÁLISE ESTRUTURADA OPENAI  ===\n")
                        results.append(f"Arquivo: {os.path.basename(caminho_arquivo)}\n")
                        results.append(f"Data/Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                        results.append("="*50 + "\n\n")
                        
                        for i, page in enumerate(pages, 1):
                            page_path = os.path.join(temp_dir, f"page_{i}.png")
                            try:
                                page.save(page_path, "PNG")
                                time.sleep(0.1)
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
                                                Tipo de documento (contrato, nota fiscal, relatorio, boleto, print, tabela, tela de software)
                                                Valores monetários detalhados, incluindo:
                                                    Valor do documento
                                                    Valor pago
                                                    Valor da multa
                                                    Valor dos juros
                                                    Valor total a pagar
                                                    Valor do desconto
                                                Datas encontradas(detalhes como vencimento, emissão, processamento, pagamento, solicitação, compensação, baixa):
                                                    Data do desconto
                                                    Data de compensação
                                                    Data de baixa
                                                    Data de vencimento
                                                    Data de emissão
                                                    Data de processamento
                                                    Data de solicitação
                                                    Data de crédito
                                                    Data de Pagamento
                                                Nomes de pessoas/empresas
                                                Números de documentos (nosso número, número do documento)
                                                Tabelas completas
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
                            
                            except Exception as e:
                                logger.error(f"[MAIN.GERAR_TXT_JSON_OPENAI] Erro na página {i} do PDF {nome}: {e}")
                            finally:
                                # Tenta fechar o handle da imagem (Pillow)
                                try:
                                    page.close()
                                except Exception:
                                    pass
                                # Remove explicitamente o arquivo temporário da página
                                try:
                                    if os.path.exists(page_path):
                                        os.remove(page_path)
                                except Exception as e:
                                    logger.warning(f"Erro ao remover arquivo temporário {page_path}: {e}")
                        
                        # Garante que o diretório de saída existe (já foi criado anteriormente, mas por segurança)
                        # txt_output.parent.mkdir(parents=True, exist_ok=True)  # Removido pois já criamos o diretório
                        
                        # Salva o resultado
                        with open(txt_output, "w", encoding="utf-8") as f:
                            f.write("".join(results))
                        
                        arquivos_processados += 1
                        logger.info(f"[MAIN.GERAR_TXT_JSON_OPENAI] ✅ [{idx}/{total_arquivos}] Processado com sucesso: {nome}")
                        
                    try:
                        limpar_artefatos_pdf2image(temp_dir, logger=logger)
                    except Exception as e:
                        logger.warning(f"Erro na limpeza de artefatos: {e}")
                        
                except Exception as e:
                    logger.error(f"[MAIN.GERAR_TXT_JSON_OPENAI] ❌ [{idx}/{total_arquivos}] Erro ao processar o arquivo {nome}: {e}")
                    arquivos_erro += 1
                    continue
        
        # Relatório final
        logger.info("="*60)
        logger.info(f"[MAIN.OPENAI_PROCESSAMENTO] 📊 RELATÓRIO FINAL:")
        logger.info(f"[MAIN.OPENAI_PROCESSAMENTO] ✅ Arquivos processados: {arquivos_processados}")
        logger.info(f"[MAIN.OPENAI_PROCESSAMENTO] ⚠️  Arquivos pulados: {arquivos_pulados}")
        logger.info(f"[MAIN.OPENAI_PROCESSAMENTO] ❌ Arquivos com erro: {arquivos_erro}")
        logger.info(f"[MAIN.OPENAI_PROCESSAMENTO] 📁 Total de arquivos: {total_arquivos}")
        logger.info("="*60)
        logger.info("[MAIN.OPENAI_PROCESSAMENTO] Processo concluído!")
        
    except Exception as e:
        logger.error(f"[MAIN.OPENAI_PROCESSAMENTO] Erro crítico ao processar o arquivo CSV: {e}")
        raise e

def gerar_csv_txts_openai_vision(arquivos_txt: List[Path], path_csv: Path):
    """
    Gera um arquivo CSV com todos os arquivos TXT que possuem 'openai_vision' no nome.
    Cada linha contém: nome do arquivo, caminho completo.
    """
    try:
        if not arquivos_txt:
            logger.warning("[MAIN.GERAR_CSV_TXTS_OPENAI_VISION] Nenhum arquivo TXT com 'openai_vision' encontrado.")
            return
        csv_dir = Path(path_csv).parent
        csv_dir.mkdir(parents=True, exist_ok=True)
        with open(path_csv, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["nome", "caminho"])
            for txt in sorted(arquivos_txt):
                writer.writerow([txt.name, str(txt)])
        logger.info(f"[MAIN.GERAR_CSV_TXTS_OPENAI_VISION] CSV gerado com {len(arquivos_txt)} arquivos: {path_csv}")
    except Exception as e:
        logger.error(f"[MAIN.GERAR_CSV_TXTS_OPENAI_VISION] Erro ao salvar CSV: {e}")
        raise e

def comparar_csvs_com_regex_e_gerar_faltantes(
    path_csv_entrada_arquivos: Union[str, Path],
    path_csv_saida_txt: Union[str, Path],
    path_csv_faltantes: Union[str, Path]
) -> int:
    """
    Compara CSV de entrada (PDFs) com CSV de saída (TXTs processados) usando regex
    para identificar PDFs que ainda não foram processados.
    
    - csv_entrada_arquivos: extrai chave removendo extensão .pdf do nome
    - csv_saida_txt: extrai números após 'openai_vision_' do nome
    
    Retorna o número de registros faltantes salvos.
    """
    import re
    
    try:
        path_csv_entrada_arquivos = Path(path_csv_entrada_arquivos)
        path_csv_saida_txt = Path(path_csv_saida_txt)
        path_csv_faltantes = Path(path_csv_faltantes)

        # Carrega chaves dos TXTs já processados 
        # MUDANÇA: Agora verifica RECURSIVAMENTE todos os arquivos TXT (incluindo subpastas)
        chaves_processados = set()
        diretorio_saida_resultados = Path("C:/saida/Resultados")
        diretorio_saida_base = Path("C:/saida")
        
        # BUSCA 1: Diretório centralizado C:/saida/Resultados
        if diretorio_saida_resultados.exists():
            logger.info(f"[MAIN.COMPARAR_REGEX] Verificando arquivos TXT em: {diretorio_saida_resultados}")
            
            for txt_file in diretorio_saida_resultados.glob("*.txt"):
                nome_txt = txt_file.stem  # Nome sem extensão
                match = re.search(r'(\d+)', nome_txt)
                if match:
                    chave = match.group(1)
                    chaves_processados.add(chave)
                    
            logger.info(f"[MAIN.COMPARAR_REGEX] Encontrados {len(chaves_processados)} arquivos TXT no diretório centralizado")
        
        # BUSCA 2: RECURSIVA em todas as subpastas de C:/saida (ex: C:/saida/000.002/resultados/)
        if diretorio_saida_base.exists():
            logger.info(f"[MAIN.COMPARAR_REGEX] Busca recursiva em subpastas de: {diretorio_saida_base}")
            arquivos_encontrados_subpastas = 0
            
            # Busca recursiva usando **/*.txt (todos os TXT em qualquer subpasta)
            for txt_file in diretorio_saida_base.glob("**/*.txt"):
                # Pula arquivos já contados no diretório centralizado
                if diretorio_saida_resultados.exists() and txt_file.is_relative_to(diretorio_saida_resultados):
                    continue
                    
                nome_txt = txt_file.stem  # Nome sem extensão
                match = re.search(r'(\d+)', nome_txt)
                if match:
                    chave = match.group(1)
                    if chave not in chaves_processados:
                        chaves_processados.add(chave)
                        arquivos_encontrados_subpastas += 1
                        
            logger.info(f"[MAIN.COMPARAR_REGEX] Encontrados {arquivos_encontrados_subpastas} arquivos TXT adicionais nas subpastas")
            logger.info(f"[MAIN.COMPARAR_REGEX] Total de arquivos TXT processados: {len(chaves_processados)}")
        
        # FALLBACK: Se não encontrou arquivos nas pastas, tenta carregar do CSV (método antigo)
        if not chaves_processados and path_csv_saida_txt.exists():
            logger.info(f"[MAIN.COMPARAR_REGEX] Fallback: Carregando do CSV de saída...")
            with open(path_csv_saida_txt, newline='', encoding="utf-8") as f_txt:
                reader_txt = csv.DictReader(f_txt)
                for row in reader_txt:
                    nome_txt = row.get("nome", "")
                    # Remove extensão .txt antes de extrair números
                    nome_sem_ext = nome_txt.replace('.txt', '').replace('.TXT', '')
                    # Extrai números do nome
                    match = re.search(r'(\d+)', nome_sem_ext)
                    if match:
                        chave = match.group(1)
                        chaves_processados.add(chave)
                        
        logger.info(f"[MAIN.COMPARAR_REGEX] Encontradas {len(chaves_processados)} chaves processadas")

        # Carrega PDFs da entrada e identifica os não processados
        registros_faltantes = []
        if path_csv_entrada_arquivos.exists():
            with open(path_csv_entrada_arquivos, newline='', encoding="utf-8") as f_entrada:
                reader_entrada = csv.DictReader(f_entrada)
                for row in reader_entrada:
                    nome_pdf = row.get("nome", "")
                    # Remove extensão .pdf e extrai números
                    nome_sem_ext = nome_pdf.replace('.pdf', '').replace('.PDF', '')
                    
                    # Extrai números do nome do PDF
                    match = re.search(r'(\d+)', nome_sem_ext)
                    if match:
                        chave_pdf = match.group(1)
                        # Se a chave do PDF não está nos processados, adiciona aos faltantes
                        if chave_pdf not in chaves_processados:
                            registros_faltantes.append(row)

        # Garante que o diretório do CSV faltantes existe
        csv_dir = Path(path_csv_faltantes).parent
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        # Salva resultado em CSV faltantes
        if registros_faltantes:
            with open(path_csv_faltantes, "w", newline='', encoding="utf-8") as f_faltantes:
                fieldnames = reader_entrada.fieldnames
                writer = csv.DictWriter(f_faltantes, fieldnames=fieldnames)
                writer.writeheader()
                for row in registros_faltantes:
                    writer.writerow(row)
        else:
            # Cria arquivo vazio com cabeçalho padrão
            with open(path_csv_faltantes, "w", newline='', encoding="utf-8") as f_faltantes:
                writer = csv.writer(f_faltantes)
                writer.writerow(["nome", "caminho_arquivo", "caminho_subdir"])
                
        logger.info(f"[MAIN.COMPARAR_REGEX] Arquivos faltantes identificados: {len(registros_faltantes)}")
        logger.info(f"[MAIN.COMPARAR_REGEX] CSV faltantes salvo em: {path_csv_faltantes}")
        return len(registros_faltantes)
        
    except Exception as e:
        logger.error(f"[MAIN.COMPARAR_REGEX] Erro ao comparar CSVs com regex: {e}")
        raise e
def listar_txts_openai_vision(root: Path, max_workers: int = 4) -> Tuple[List[Path], List[Path]]:
    """
    Busca recursiva de arquivos TXT que possuem 'openai_vision' no nome, usando os.scandir e multithreading.
    Retorna uma lista de arquivos encontrados e uma lista de subdiretórios.
    """
    logger.info(f"[MAIN.LISTAGEM_OPENAI_VISION] Iniciando a varredura de TXT com 'openai_vision' no diretório: {root}")
    logger.info(f"[MAIN.LISTAGEM_OPENAI_VISION] Usando {max_workers} threads para varredura de subdiretórios.")

    def scan_dir(p: Path):
        arquivos = []
        try:
            for entry in os.scandir(p):
                if entry.is_file() and entry.name.lower().endswith('.txt') and 'openai_vision' in entry.name.lower():
                    arquivos.append(Path(entry.path))
                elif entry.is_dir():
                    arquivos.extend(scan_dir(Path(entry.path)))
        except Exception as e:
            logger.warning(f"[MAIN.LISTAGEM_OPENAI_VISION.SCAN_DIR] Erro ao acessar {p}: {e}")
        return arquivos

    arquivos_txt_openai_vision = []
    subdirs = [Path(entry.path) for entry in os.scandir(root) if entry.is_dir()]
    arquivos_txt_openai_vision.extend([
        Path(entry.path)
        for entry in os.scandir(root)
        if entry.is_file() and entry.name.lower().endswith('.txt') and 'openai_vision' in entry.name.lower()
    ])

    subdiretorios_verificados = len(subdirs)
    total_verificados = len(arquivos_txt_openai_vision)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_dir, subdir): subdir for subdir in subdirs}
        for f in as_completed(futures):
            arquivos_txt_openai_vision.extend(f.result())
            total_verificados += len(f.result())

    logger.info(f"[MAIN.LISTAGEM_OPENAI_VISION] Total de arquivos TXT encontrados: {total_verificados}, subdiretórios verificados: {subdiretorios_verificados}")
    return arquivos_txt_openai_vision, subdirs


def main():
    global logger, config
    logger, config = iniciando_configuracoes()
    
    path_entrada = Path(config['Paths']['PATH_ENTRADA'])
    path_csv_entrada = Path(config['Paths']['PATH_CSV_ENTRADA'])
    path_csv_entrada_arquivos = Path(config['Paths']['PATH_CSV_ENTRADA_ARQUIVOS'])
    path_csv_entrada_manter = Path(config['Paths']['PATH_CSV_ENTRADA_MANTER'])
    path_csv_entrada_txt = Path(config['Paths']['PATH_CSV_ENTRADA_TXT'])
    
    path_saida = Path(config['Paths']['PATH_SAIDA'])
    path_csv_saida = Path(config['Paths']['PATH_CSV_SAIDA'])
    path_csv_saida_manter = Path(config['Paths']['PATH_CSV_SAIDA_MANTER'])
    path_csv_saida_arquivos = Path(config['Paths']['PATH_CSV_SAIDA_ARQUIVOS'])
    path_csv_saida_txt = Path(config['Paths']['PATH_CSV_SAIDA_TXT'])
    
    
    path_processados = Path("C:\\Users\\Maoki\\Downloads\\Nouryon_-_Automatização\\Notas_Fiscais")
    path_csv_processados_arquivos = Path(config['Paths']['PATH_CSV_PROCESSADOS_ARQUIVOS'])
    path_csv_processados_manter = Path(config['Paths']['PATH_CSV_PROCESSADOS_MANTER'])
    path_csv_processados = Path(config['Paths']['PATH_CSV_PROCESSADOS'])
    
    path_csv_fonte = Path(config['Paths']['PATH_CSV_FONTE'])
    path_fonte = Path(config['Paths']['PATH_FONTE'])
    path_csv_fonte_arquivos = Path(config['Paths']['PATH_CSV_FONTE_ARQUIVOS'])
    
    api_key = config['OpenAI']['API_KEY']
    path_temp_dir = Path(config['Paths']['PATH_TEMP_DIR'])
    
    """ gerar_csv_manter_diretorios(path_entrada, path_csv_entrada)
    comparar_csvs_faltantes(path_csv_entrada, path_csv_saida, path_csv_entrada_manter)
    gerar_csv_manter_diretorios(path_saida, path_csv_saida)
    comparar_csvs_faltantes(path_csv_fonte, path_csv_saida, path_csv_saida_manter) """
    
    # arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_saida, max_workers=4)
    # gerar_csv_arquivos_pdfs(arquivos_pdfs, subdirs, path_csv_saida_arquivos)
    # arquivos_txt, _ = listar_txts_openai_vision(path_saida, max_workers=4)
    # gerar_csv_txts_openai_vision(arquivos_txt, path_csv_saida_txt)
    
    
    
    #arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_processados, max_workers=4)
    #gerar_csv_arquivos_pdfs(arquivos_pdfs, subdirs, path_csv_processados_arquivos) 
    #gerar_txt_openAI(path_csv_processados_arquivos, api_key)
    
    
    
    # TODO: PRECISO GERAR O CSV COM TODOS PDFS DA ENTRADA QUE NAO FORAM PROCESSADOS E GERAR TXTS DA ENTRADA QUE NAO FORAM PROCESSADOS 
    """ preciso gerar o csv com todos arquivos da pasta entrada comparando com csv_saida_txt 
        para fazer a comparação preciso de um regex comum entre os dois csv
            - [csv_saida_txt] gerar chave com campo nome e extrair numeros após openai_vision_
            - [csv_entrada_arquivos] gerar uma chave com campo nome e remover extensão
        depois de gerar o csv com os arquivos da entrada que faltam txt
        processar esses arquivos que faltam txt
        gerar csv_entrada_txt 
    """
    
    # 1. Gerar CSV dos arquivos PDF da entrada
    # arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_entrada, max_workers=4)
    # gerar_csv_arquivos_pdfs(arquivos_pdfs, subdirs, path_csv_entrada_arquivos)
    
    # 2. Comparar entrada com saída para identificar arquivos não processados
    path_csv_entrada_faltantes = Path(str(path_csv_entrada_arquivos).replace('.csv', '_faltantes.csv'))
    
    arquivos_faltantes = comparar_csvs_com_regex_e_gerar_faltantes(path_csv_entrada_arquivos, path_csv_saida_txt, path_csv_entrada_faltantes)
    
    if arquivos_faltantes > 0:
        logger.info(f"[MAIN] Processando {arquivos_faltantes} arquivos que faltam TXT...")
        # 3. Processar arquivos que faltam TXT
        gerar_txt_openAI(path_csv_entrada_faltantes, api_key)
        
        # 4. Gerar CSV com todos os TXTs da entrada após processamento
        arquivos_txt, _ = listar_txts_openai_vision(path_entrada, max_workers=4)
        gerar_csv_txts_openai_vision(arquivos_txt, path_csv_entrada_txt)
        
        logger.info(f"[MAIN] Processamento concluído! CSV de entrada com TXTs gerado: {path_csv_entrada_txt}")
    else:
        logger.info("[MAIN] Todos os arquivos da entrada já foram processados.")
    
    
    # arquivos_pdfs, subdirs = listar_pdfs_hibrido(path_entrada, max_workers=4)
    # gerar_csv_arquivos_pdfs(arquivos_pdfs, subdirs, path_csv_entrada_arquivos)
    #gerar_txt_openAI(path_csv_entrada_arquivos, api_key) 
    
    
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

