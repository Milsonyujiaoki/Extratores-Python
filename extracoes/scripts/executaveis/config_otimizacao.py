# -*- coding: utf-8 -*-
"""
Configurações de otimização para o processamento OpenAI Vision
Ajuste estes parâmetros conforme necessário para seu ambiente
"""

# ================================
# CONFIGURAÇÕES DE PARALELIZAÇÃO
# ================================

# Número de threads para processamento paralelo de PDFs
# RECOMENDADO: 3-4 threads para balancear velocidade vs estabilidade
# CUIDADO: Muitas threads podem causar rate limiting na API OpenAI
MAX_WORKERS_PROCESSAMENTO = 3

# Número de threads para listagem de arquivos
MAX_WORKERS_LISTAGEM = 4

# ================================
# CONFIGURAÇÕES DE QUALIDADE/VELOCIDADE
# ================================

# DPI para conversão PDF->Imagem
# 150: Mais rápido, qualidade boa para a maioria dos documentos
# 200: Balanceado entre qualidade e velocidade (RECOMENDADO)
# 300: Alta qualidade, mais lento
PDF_DPI = 200

# ================================
# CONFIGURAÇÕES DE LOGGING
# ================================

# Frequência de logs de progresso durante processamento em massa
# Log a cada X arquivos processados
LOG_PROGRESS_EVERY = 50

# Log detalhado apenas para os primeiros X arquivos (evita spam)
LOG_DETAILED_FIRST = 5

# Log de erros apenas a cada X erros (evita poluição do log)
LOG_ERRORS_EVERY = 20

# ================================
# CONFIGURAÇÕES DE RETRY/TIMEOUT
# ================================

# Máximo de tentativas para validação de PDF
MAX_TENTATIVAS_VALIDACAO_PDF = 3

# Delay entre tentativas (segundos)
DELAY_ENTRE_TENTATIVAS = 0.5

# Timeout para operações de arquivo (segundos)
FILE_OPERATION_TIMEOUT = 30

# ================================
# CONFIGURAÇÕES DE LIMPEZA
# ================================

# Modo seguro para limpeza de arquivos temporários
# True: Verifica se arquivo está em uso antes de remover
# False: Remove diretamente (mais rápido, mas pode dar erro)
SAFE_MODE_CLEANUP = True

# Extensões de arquivos temporários a serem limpos
TEMP_FILE_EXTENSIONS = (".ppm", ".pbm", ".jpg", ".jpeg", ".png", ".tmp")

# ================================
# CONFIGURAÇÕES DE MEMÓRIA
# ================================

# Limpar recursos de imagem após cada página
CLEANUP_IMAGES_AFTER_PAGE = True

# Forçar garbage collection a cada X arquivos processados
FORCE_GC_EVERY = 100

# ================================
# ESTIMATIVAS DE TEMPO
# ================================

def calcular_tempo_estimado(arquivos_restantes: int, max_workers: int = MAX_WORKERS_PROCESSAMENTO) -> dict:
    """
    Calcula tempo estimado baseado nas otimizações implementadas
    
    Args:
        arquivos_restantes: Número de arquivos ainda não processados
        max_workers: Número de threads paralelas
    
    Returns:
        dict com estimativas de tempo em diferentes cenários
    """
    # Tempos médios observados (segundos por arquivo)
    TEMPO_ORIGINAL_SEQUENCIAL = 37.0  # Tempo médio antes das otimizações
    TEMPO_OTIMIZADO_PARALELO = 12.0   # Tempo médio com otimizações (3 threads)
    TEMPO_CONSERVADOR = 15.0          # Estimativa conservadora
    
    # Calcula tempos em diferentes cenários
    tempo_original_horas = (arquivos_restantes * TEMPO_ORIGINAL_SEQUENCIAL) / 3600
    tempo_otimizado_horas = (arquivos_restantes * TEMPO_OTIMIZADO_PARALELO / max_workers) / 3600
    tempo_conservador_horas = (arquivos_restantes * TEMPO_CONSERVADOR / max_workers) / 3600
    
    return {
        "arquivos_restantes": arquivos_restantes,
        "max_workers": max_workers,
        "tempo_original_horas": round(tempo_original_horas, 1),
        "tempo_otimizado_horas": round(tempo_otimizado_horas, 1), 
        "tempo_conservador_horas": round(tempo_conservador_horas, 1),
        "aceleracao_esperada": round(TEMPO_ORIGINAL_SEQUENCIAL / (TEMPO_OTIMIZADO_PARALELO / max_workers), 1),
        "economia_tempo_horas": round(tempo_original_horas - tempo_otimizado_horas, 1)
    }

# ================================
# CONFIGURAÇÕES AVANÇADAS
# ================================

# Configurações para ambientes com restrições de recursos
CONFIGURACAO_AMBIENTE = {
    "desenvolvimento": {
        "MAX_WORKERS": 2,
        "PDF_DPI": 150,
        "LOG_PROGRESS_EVERY": 10,
        "SAFE_MODE_CLEANUP": True
    },
    "producao_rapida": {
        "MAX_WORKERS": 4,
        "PDF_DPI": 200,
        "LOG_PROGRESS_EVERY": 100,
        "SAFE_MODE_CLEANUP": False
    },
    "producao_estavel": {
        "MAX_WORKERS": 3,
        "PDF_DPI": 200,
        "LOG_PROGRESS_EVERY": 50,
        "SAFE_MODE_CLEANUP": True
    },
    "qualidade_maxima": {
        "MAX_WORKERS": 2,
        "PDF_DPI": 300,
        "LOG_PROGRESS_EVERY": 25,
        "SAFE_MODE_CLEANUP": True
    }
}

def aplicar_configuracao_ambiente(ambiente: str = "producao_estavel") -> None:
    """
    Aplica configurações pré-definidas para diferentes ambientes
    
    Args:
        ambiente: Tipo de ambiente ('desenvolvimento', 'producao_rapida', 
                 'producao_estavel', 'qualidade_maxima')
    """
    global MAX_WORKERS_PROCESSAMENTO, PDF_DPI, LOG_PROGRESS_EVERY, SAFE_MODE_CLEANUP
    
    if ambiente in CONFIGURACAO_AMBIENTE:
        config = CONFIGURACAO_AMBIENTE[ambiente]
        MAX_WORKERS_PROCESSAMENTO = config["MAX_WORKERS"]
        PDF_DPI = config["PDF_DPI"]
        LOG_PROGRESS_EVERY = config["LOG_PROGRESS_EVERY"]
        SAFE_MODE_CLEANUP = config["SAFE_MODE_CLEANUP"]
        print(f"✅ Configuração '{ambiente}' aplicada com sucesso!")
    else:
        print(f"❌ Configuração '{ambiente}' não encontrada. Mantendo configurações padrão.")

if __name__ == "__main__":
    # Exemplo de uso
    print("📊 Exemplo de cálculo de tempo estimado:")
    estimativa = calcular_tempo_estimado(6424, 3)  # 6424 arquivos com 3 threads
    
    print(f"Arquivos restantes: {estimativa['arquivos_restantes']}")
    print(f"Threads: {estimativa['max_workers']}")
    print(f"Tempo original (sequencial): {estimativa['tempo_original_horas']}h")
    print(f"Tempo otimizado (paralelo): {estimativa['tempo_otimizado_horas']}h") 
    print(f"Tempo conservador: {estimativa['tempo_conservador_horas']}h")
    print(f"Aceleração esperada: {estimativa['aceleracao_esperada']}x")
    print(f"Economia de tempo: {estimativa['economia_tempo_horas']}h")
