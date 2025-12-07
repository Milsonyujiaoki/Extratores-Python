"""
ARQUIVO DE CONFIGURAÇÃO - EXTRAÇÃO DE PDFs
Modifique este arquivo para adaptar o sistema às suas necessidades
"""

# ==================== CONFIGURAÇÃO DE CAMINHOS ====================

# Pasta base onde estão os PDFs organizados por projeto
# Exemplos:
# "../pdfs"           - Para estrutura atual
# "C:/MeusPDFs"       - Caminho absoluto Windows
# "/home/user/pdfs"   - Caminho absoluto Linux
PDF_BASE_PATH = "../pdfs"

# Pasta base onde serão salvos os resultados
# Exemplos:
# "../resultados"     - Para estrutura atual
# "C:/Resultados"     - Caminho absoluto Windows
# "/home/user/results"- Caminho absoluto Linux
RESULTS_BASE_PATH = "../resultados"

# Prefixo para identificar projetos nas pastas
# Exemplos:
# "000."              - Para projetos 000.001, 000.002, etc.
# "projeto_"          - Para projetos projeto_A, projeto_B, etc.
# "doc"               - Para projetos doc1, doc2, etc.
# ""                  - Para qualquer pasta (cuidado: pode pegar pastas indesejadas)
PROJECT_PREFIX = "000."

# ==================== CONFIGURAÇÃO DE EXECUÇÃO ====================

# Scripts de extração disponíveis (na ordem de execução)
# Formato: (nome_do_arquivo, descrição_amigável)
EXTRACTION_SCRIPTS = [
    ("extracao_pyMuPdf.py", "🚀 PyMuPDF - Extração rápida e eficiente"),
    ("extracao_pdfPlumber.py", "📊 PDFPlumber - Estruturas e tabelas"),
    ("extracao_pdfMiner.py", "🔍 PDFMiner - Análise profunda"),
    ("extracao_pyPdf2.py", "📄 PyPDF2 - Biblioteca clássica"),
    ("extracao_pymupdf4llm.py", "🤖 PyMuPDF4LLM - Otimizado para IA"),
    ("extracao_pdfquery.py", "🔎 PDFQuery - Consultas estruturadas"),
    ("extracao_camelot_tabelas.py", "📈 Camelot - Extração e consolidação integrada"),
    ("extracao_tabula.py", "📊 Tabula - Extração de tabelas Java"),
    ("extracao_tika.py", "🔍 Apache Tika - Análise de conteúdo"),
]

# Padrões de arquivos gerados por cada script (para detecção de duplicatas)
SCRIPT_OUTPUT_PATTERNS = {
    'extracao_pyMuPdf.py': ['txt/PyMuPDF_*.txt'],
    'extracao_pdfPlumber.py': ['txt/pdfPlumber_*.txt'],
    'extracao_pdfMiner.py': ['txt/pdfMiner_*.txt'],
    'extracao_pyPdf2.py': ['txt/PyPDF2_*.txt'],
    'extracao_pymupdf4llm.py': ['txt/pymupdf4llm_*.txt', 'md/pymupdf4llm_*.md'],
    'extracao_pdfquery.py': ['txt/pdfquery_*.txt', 'txt/pdfquery_estruturado_*.txt'],
    'extracao_camelot_tabelas.py': ['csv/*_T*.csv', 'relatorios/camelot_consolidado_*.txt', 'relatorios/camelot_consolidado_*.xlsx'],
    'extracao_tabula.py': ['csv/tabula_*.csv'],
    'extracao_tika.py': ['txt/tika_*.txt']
}

# ==================== CONFIGURAÇÃO DO AMBIENTE ====================

# Caminho para o interpretador Python do ambiente virtual
# Modifique conforme sua instalação
PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"

# Estrutura de subpastas nos resultados
RESULT_SUBDIRS = ['txt', 'csv', 'md', 'relatorios']

# ==================== EXEMPLOS DE CONFIGURAÇÃO ====================

# Exemplo 1: Estrutura simples
# PDF_BASE_PATH = "pdfs"
# RESULTS_BASE_PATH = "results"
# PROJECT_PREFIX = "proj"

# Exemplo 2: Estrutura por data
# PDF_BASE_PATH = "../documentos/2024"
# RESULTS_BASE_PATH = "../extrações/2024"
# PROJECT_PREFIX = "2024-"

# Exemplo 3: Estrutura corporativa
# PDF_BASE_PATH = "//servidor/documentos/contratos"
# RESULTS_BASE_PATH = "//servidor/análises/extrações"
# PROJECT_PREFIX = "contrato_"
