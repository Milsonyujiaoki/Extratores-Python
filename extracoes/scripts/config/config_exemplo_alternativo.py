"""
EXEMPLO DE CONFIGURAÇÃO ALTERNATIVA - EXTRAÇÃO DE PDFs
Este é um exemplo de como configurar o sistema para diferentes estruturas
"""

# ==================== CONFIGURAÇÃO ALTERNATIVA ====================

# Exemplo: Usar estrutura de pasta diferente
PDF_BASE_PATH = "../documentos"        # Pasta com documentos
RESULTS_BASE_PATH = "../analises"      # Pasta para análises
PROJECT_PREFIX = "doc"                 # Prefixo para projetos: doc1, doc2, etc.

# Configuração do Python (manter igual)
PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"

# Subpastas nos resultados (personalizar conforme necessário)
RESULT_SUBDIRS = ['textos', 'tabelas', 'markdown', 'consolidados']

# Scripts de extração (personalizar ordem ou remover alguns)
EXTRACTION_SCRIPTS = [
    ("extracao_pyMuPdf.py", "🚀 PyMuPDF - Rápido"),
    ("extracao_pdfPlumber.py", "📊 PDFPlumber - Tabelas"),
    ("extracao_camelot_tabelas.py", "📈 Camelot - Consolidado"),
    # Comentar ou remover scripts que não quiser usar:
    # ("extracao_pdfMiner.py", "🔍 PDFMiner"),
    # ("extracao_pyPdf2.py", "📄 PyPDF2"),
]

# Padrões de arquivos (adaptar às subpastas personalizadas)
SCRIPT_OUTPUT_PATTERNS = {
    'extracao_pyMuPdf.py': ['textos/PyMuPDF_*.txt'],
    'extracao_pdfPlumber.py': ['textos/pdfPlumber_*.txt'],
    'extracao_pdfMiner.py': ['textos/pdfMiner_*.txt'],
    'extracao_pyPdf2.py': ['textos/PyPDF2_*.txt'],
    'extracao_pymupdf4llm.py': ['textos/pymupdf4llm_*.txt', 'markdown/pymupdf4llm_*.md'],
    'extracao_pdfquery.py': ['textos/pdfquery_*.txt', 'textos/pdfquery_estruturado_*.txt'],
    'extracao_camelot_tabelas.py': ['tabelas/*_T*.csv', 'consolidados/camelot_consolidado_*.txt', 'consolidados/camelot_consolidado_*.xlsx'],
    'extracao_tabula.py': ['tabelas/tabula_*.csv'],
    'extracao_tika.py': ['textos/tika_*.txt']
}
