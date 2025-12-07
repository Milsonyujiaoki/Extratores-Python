"""
CONFIGURAÇÃO PARA EXECUTÁVEL TOP 3 OTIMIZADO
Configuração específica para o sistema simplificado com os 3 melhores scripts
"""

# ==================== CONFIGURAÇÃO TOP 3 ====================

# Caminhos principais (ajustar conforme sua estrutura)
PDF_BASE_PATH = "../../pdfs"         # Pasta onde estão os PDFs
RESULTS_BASE_PATH = "../../resultados" # Pasta para salvar resultados
PROJECT_PREFIX = "000."               # Prefixo dos projetos a processar

# Configuração do ambiente Python
PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"

# Estrutura de subpastas nos resultados
RESULT_SUBDIRS = ['txt', 'csv', 'md', 'relatorios']

# Scripts TOP 3 otimizados (melhor qualidade para arquivos CP)
EXTRACTION_SCRIPTS_TOP3 = [
    ("../extracoes/extracao_pdfquery.py", "🥇 PDFQuery - MELHOR para arquivos CP (80% sucesso)"),
    ("../extracoes/extracao_pyMuPdf.py", "🥈 PyMuPDF - Rápido e eficiente (60% sucesso CP)"),
    ("../extracoes/extracao_pdfPlumber.py", "🥉 PDFPlumber - Estruturas e tabelas (60% sucesso CP)"),
]

# Scripts OCR para fallback automático
EXTRACTION_SCRIPTS_OCR = [
    ("../extracoes/extracao_tesseract_ocr.py", "🔍 Tesseract OCR - Para PDFs escaneados"),
    ("../extracoes/extracao_openai_vision.py", "🤖 OpenAI Vision - IA avançada para texto complexo"),
    ("../extracoes/extracao_hibrida_ocr.py", "🧠 Pipeline Híbrido - Automático com fallback"),
]

# Configuração completa com OCR
EXTRACTION_SCRIPTS_COMPLETE = EXTRACTION_SCRIPTS_TOP3 + EXTRACTION_SCRIPTS_OCR

# Padrões para detecção de arquivos existentes (evita duplicatas)
SCRIPT_OUTPUT_PATTERNS_TOP3 = {
    '../extracoes/extracao_pdfquery.py': ['pdfquery_*.txt', 'pdfquery_estruturado_*.txt'],
    '../extracoes/extracao_pyMuPdf.py': ['PyMuPDF_*.txt'],
    '../extracoes/extracao_pdfPlumber.py': ['pdfPlumber_*.txt'],
}

# Padrões para scripts OCR
SCRIPT_OUTPUT_PATTERNS_OCR = {
    '../extracoes/extracao_tesseract_ocr.py': ['tesseract_ocr_*.txt', 'tesseract_enhanced_*.txt'],
    '../extracoes/extracao_openai_vision.py': ['openai_vision_*.txt', 'openai_structured_*.txt'],
    '../extracoes/extracao_hibrida_ocr.py': ['extraction_report_*.txt'],
}

# Padrões completos
SCRIPT_OUTPUT_PATTERNS_COMPLETE = {**SCRIPT_OUTPUT_PATTERNS_TOP3, **SCRIPT_OUTPUT_PATTERNS_OCR}

# ==================== CONFIGURAÇÕES ALTERNATIVAS ====================

# Para estrutura de pastas diferentes, modifique abaixo:

# Exemplo 1: Estrutura corporativa
# PDF_BASE_PATH = "//servidor/documentos"
# RESULTS_BASE_PATH = "//servidor/analises"
# PROJECT_PREFIX = "contrato_"

# Exemplo 2: Organização por data
# PDF_BASE_PATH = "../../documentos/2024"
# RESULTS_BASE_PATH = "../../resultados/2024"
# PROJECT_PREFIX = "2024-"

# Exemplo 3: Estrutura acadêmica
# PDF_BASE_PATH = "../../papers"
# RESULTS_BASE_PATH = "../../extrações"
# PROJECT_PREFIX = "paper_"
