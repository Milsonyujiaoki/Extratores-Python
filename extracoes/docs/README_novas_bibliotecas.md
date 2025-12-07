# Bibliotecas para Extração de PDF - Guia de Instalação

## Bibliotecas Já Testadas
- ✅ **PyPDF2**: `pip install PyPDF2`
- ✅ **pdfminer.six**: `pip install pdfminer.six`
- ✅ **PyMuPDF (fitz)**: `pip install PyMuPDF`
- ✅ **pdfplumber**: `pip install pdfplumber`

## Novas Bibliotecas para Testar

### 1. Camelot (Especializada em Tabelas)
```bash
pip install camelot-py[cv]
```
**Características:**
- Excelente para extrair tabelas estruturadas
- Fornece métricas de acurácia
- Salva em múltiplos formatos (CSV, Excel, JSON)

### 2. Tabula (Alternativa para Tabelas)
```bash
pip install tabula-py
```
**Requisitos:** Java deve estar instalado
**Características:**
- Focada em extração de tabelas
- Interface simples
- Boa precisão para documentos tabulares

### 3. Apache Tika
```bash
pip install tika
```
**Requisitos:** Java deve estar instalado
**Características:**
- Extrai texto e metadados
- Suporta diversos formatos além de PDF
- Muito robusta para análise de metadados

### 4. PDFQuery (Queries CSS-like)
```bash
pip install pdfquery
```
**Características:**
- Permite seleções precisas usando sintaxe CSS
- Boa para extrair informações específicas
- Útil para documentos com layout conhecido

### 5. PyMuPDF4LLM (Otimizado para IA)
```bash
pip install pymupdf4llm
```
**Características:**
- Otimizado para processamento por Large Language Models
- Mantém formatação adequada para IA
- Converte diretamente para Markdown

## Como Usar

1. **Instalar as bibliotecas:**
```bash
pip install camelot-py[cv] tabula-py tika pdfquery pymupdf4llm
```

2. **Executar teste individual:**
```bash
cd extracoes
python extracao_camelot.py
```

3. **Executar todos os testes:**
```bash
python teste_todas_bibliotecas.py
```

## Comparação Esperada

| Biblioteca | Melhor Para | Formato Saída |
|------------|-------------|---------------|
| **pdfplumber** | Texto geral estruturado | TXT |
| **PyMuPDF** | Texto limpo e rápido | TXT |
| **Camelot** | Tabelas complexas | CSV, Excel |
| **Tabula** | Tabelas simples | CSV |
| **Tika** | Metadados e análise | TXT + Metadata |
| **PDFQuery** | Extração seletiva | TXT estruturado |
| **PyMuPDF4LLM** | Processamento por IA | Markdown |

## Arquivos de Saída

Os resultados serão salvos na pasta `000.002/` com prefixos indicando a biblioteca usada:
- `camelot_*.csv` - Tabelas extraídas pelo Camelot
- `tabula_*.csv` - Tabelas extraídas pelo Tabula  
- `tika_*.txt` - Texto extraído pelo Tika
- `pdfquery_*.txt` - Extração estruturada
- `pymupdf4llm_*.md` - Markdown otimizado para LLM
