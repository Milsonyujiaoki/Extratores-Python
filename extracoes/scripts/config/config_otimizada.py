"""
CONFIGURAÇÃO OTIMIZADA - BASEADA NA ANÁLISE DE QUALIDADE
Esta configuração prioriza os scripts com melhor performance,
especialmente para arquivos CP (que são mais desafiadores)
"""

# ==================== CONFIGURAÇÃO OTIMIZADA ====================

# Caminhos (manter configuração atual)
PDF_BASE_PATH = "../pdfs"
RESULTS_BASE_PATH = "../resultados" 
PROJECT_PREFIX = "000."

# Configuração do Python
PYTHON_EXECUTABLE = r"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe"

# Estrutura de resultados
RESULT_SUBDIRS = ['txt', 'csv', 'md', 'relatorios']

# ==================== SCRIPTS OTIMIZADOS POR QUALIDADE ====================

# Configuração PREMIUM - Apenas os melhores scripts (recomendado para produção)
EXTRACTION_SCRIPTS_PREMIUM = [
    ("extracao_pdfquery.py", "🥇 PDFQuery - MELHOR para arquivos CP (80% sucesso)"),
    ("extracao_pyMuPdf.py", "🥈 PyMuPDF - Rápido e confiável (60% sucesso CP)"),
    ("extracao_pdfMiner.py", "🥉 PDFMiner - Análise robusta (60% sucesso CP)"),
    ("extracao_camelot_tabelas.py", "📈 Camelot - Extração de tabelas consolidada"),
]

# Configuração COMPLETA - Todos os scripts com prioridade por qualidade
EXTRACTION_SCRIPTS_COMPLETE = [
    # Tier 1: Melhores para arquivos CP
    ("extracao_pdfquery.py", "🥇 PDFQuery - MELHOR para CP (80% sucesso)"),
    
    # Tier 2: Bons para CP e extrações gerais
    ("extracao_pyMuPdf.py", "🥈 PyMuPDF - Rápido e eficiente (60% sucesso CP)"),
    ("extracao_pdfPlumber.py", "🥈 PDFPlumber - Estruturas e tabelas (60% sucesso CP)"),
    ("extracao_pdfMiner.py", "🥈 PDFMiner - Análise profunda (60% sucesso CP)"),
    ("extracao_pymupdf4llm.py", "🥈 PyMuPDF4LLM - Otimizado para IA (60% sucesso CP)"),
    ("extracao_pyPdf2.py", "🥈 PyPDF2 - Biblioteca clássica (60% sucesso CP)"),
    
    # Tier 3: Extração de tabelas
    ("extracao_camelot_tabelas.py", "📈 Camelot - Consolidação integrada"),
    
    # Tier 4: Scripts experimentais (requerem Java)
    # ("extracao_tabula.py", "📊 Tabula - Requer Java"),
    # ("extracao_tika.py", "🔍 Tika - Requer Java"),
]

# Configuração ESSENCIAL - Mínimo necessário para cobertura completa
EXTRACTION_SCRIPTS_ESSENTIAL = [
    ("extracao_pdfquery.py", "🥇 PDFQuery - Melhor para CP"),
    ("extracao_pyMuPdf.py", "🚀 PyMuPDF - Rápido"),
    ("extracao_camelot_tabelas.py", "📈 Camelot - Tabelas"),
]

# ==================== ESCOLHA SUA CONFIGURAÇÃO ====================

# Descomente APENAS UMA das linhas abaixo:

# Para máxima qualidade (recomendado):
EXTRACTION_SCRIPTS = EXTRACTION_SCRIPTS_PREMIUM

# Para análise completa:
# EXTRACTION_SCRIPTS = EXTRACTION_SCRIPTS_COMPLETE

# Para uso básico e rápido:
# EXTRACTION_SCRIPTS = EXTRACTION_SCRIPTS_ESSENTIAL

# ==================== PADRÕES DE DETECÇÃO OTIMIZADOS ====================

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

# ==================== NOTAS DA ANÁLISE DE QUALIDADE ====================

"""
📊 RESULTADOS DA ANÁLISE:

🏆 RANKING DE PERFORMANCE EM ARQUIVOS CP:
1. PDFQuery: 80% sucesso (melhor para documentos complexos)
2. PyMuPDF: 60% sucesso (rápido e confiável)
3. PDFPlumber: 60% sucesso (bom para estruturas)
4. PDFMiner: 60% sucesso (análise robusta)
5. PyMuPDF4LLM: 60% sucesso (otimizado para IA)
6. PyPDF2: 60% sucesso (biblioteca clássica)

🔍 ANÁLISE DETALHADA:
- Projetos 000.002 e 000.003: Arquivos CP são problemáticos (possivelmente baseados em imagem)
- Projetos 000.004, 000.005, 000.006: Todos os scripts funcionam bem nos arquivos CP
- PDFQuery é o mais robusto para casos difíceis
- PyMuPDF oferece o melhor equilíbrio velocidade/qualidade

💡 RECOMENDAÇÃO:
Use a configuração PREMIUM para obter os melhores resultados com o menor tempo de processamento.
Para análise acadêmica ou casos especiais, use a configuração COMPLETE.
"""
