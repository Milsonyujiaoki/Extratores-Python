# Extratores de PDF - Python

## Visão Geral

Este projeto contém três scripts especializados para extração de texto de arquivos PDF, cada um otimizado para diferentes tipos de documentos e cenários de uso. O sistema foi desenvolvido para fornecer máxima flexibilidade e robustez na extração de texto, suportando desde PDFs nativos até documentos escaneados.

## 🚀 Funcionalidades Principais

- **Extração Direta**: Para PDFs com texto nativo extraível
- **Extração por OCR**: Para PDFs escaneados ou baseados em imagens
- **Extração Híbrida**: Combina ambas as abordagens automaticamente
- **Configuração Flexível**: Sistema de configuração via arquivo INI
- **Tratamento de Erros Robusto**: Logging detalhado e recuperação de falhas
- **Gestão de Memória**: Limpeza automática para processar arquivos grandes

## 📁 Estrutura do Projeto

```text
Extratores-python/
├── Scripts/
│   ├── pdf_extractor_direct.py    # Extração direta de texto
│   ├── pdf_extractor_ocr.py       # Extração via OCR
│   ├── pdf_extractor_hybrid.py    # Extração híbrida (recomendado)
│   ├── config.ini                 # Configurações de caminhos
│   └── old/                       # Versões anteriores
├── src/                           # Código fonte adicional
├── .env                          # Variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
└── README.md                     # Esta documentação
```

## 🛠 Tecnologias e Dependências

### Ambiente Python

- **Versão**: Python 3.13.7
- **Tipo**: Virtual Environment (Pipenv)
- **Caminho**: `C:/Users/milso/.virtualenvs/OneDrive_-_Universidade_Federal_do_ABC-rilybLrp/Scripts/python.exe`

### Bibliotecas Principais

#### Extração de PDF

- **pdfplumber (0.11.7)**: Biblioteca principal para extração de texto de PDFs nativos
- **PyPDF2 (3.0.1)**: Biblioteca alternativa para extração direta
- **PyMuPDF (1.26.3)**: Biblioteca adicional para manipulação de PDFs

#### OCR (Reconhecimento Óptico de Caracteres)

- **pytesseract (0.3.13)**: Interface Python para Tesseract OCR
- **pdf2image (1.17.0)**: Conversão de páginas PDF para imagens
- **Pillow (11.3.0)**: Manipulação e processamento de imagens

#### Configuração e Logging

- **configparser (7.2.0)**: Leitura de arquivos de configuração INI
- **logging**: Módulo nativo Python para sistema de logs

### Dependências do Sistema

- **Tesseract OCR**: Instalado em `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **Poppler**: Necessário para pdf2image (conversão PDF→imagem)

## 📋 Scripts Detalhados

### 1. pdf_extractor_direct.py

**Propósito**: Extração rápida de texto de PDFs nativos (texto extraível)

**Características Técnicas**:

- Usa `pdfplumber` como método primário
- Fallback para `PyPDF2` se pdfplumber falhar
- Otimizado para velocidade e baixo uso de memória
- Suporte a encodings múltiplos (UTF-8, UTF-8-SIG, Latin1, CP1252)

**Fluxo de Execução**:

1. Carrega configuração do `config.ini`
2. Tenta extração com pdfplumber
3. Se falhar, tenta PyPDF2
4. Salva resultado em `OUTPUT_PATH_DIRECT`

**Casos de Uso Ideais**:

- PDFs criados digitalmente
- Documentos com texto selecionável
- Processamento em lote de múltiplos PDFs

### 2. pdf_extractor_ocr.py

**Propósito**: Extração de texto via OCR para documentos escaneados

**Características Técnicas**:

- Converte PDF para imagens (DPI configurável: 300 padrão)
- Usa Tesseract OCR com idioma português ('por')
- Processamento página por página com logging detalhado
- Limite configurável de páginas para evitar sobrecarga
- Limpeza automática de memória após cada página

**Parâmetros Configuráveis**:

- **DPI**: 300 (qualidade vs velocidade)
- **Idioma**: 'por' (português)
- **Max páginas**: Limitação para PDFs grandes

**Fluxo de Execução**:

1. Converte PDF para imagens com pdf2image
2. Aplica OCR em cada imagem com pytesseract
3. Combina texto de todas as páginas
4. Salva resultado em `OUTPUT_PATH_OCR`

**Casos de Uso Ideais**:

- Documentos escaneados
- PDFs com texto em imagens
- Documentos antigos digitalizados

### 3. pdf_extractor_hybrid.py (RECOMENDADO)

**Propósito**: Abordagem inteligente que combina extração direta e OCR

**Características Técnicas**:

- **Estratégia Adaptativa**: Tenta extração direta primeiro, OCR como fallback
- **Tratamento de Erro Avançado**: Continua processamento mesmo com páginas problemáticas
- **Logging Detalhado**: Rastreia qual método foi usado para cada página
- **Otimização de Memória**: Limpeza de garbage collection após cada operação

**Algoritmo de Decisão**:

```python
1. Tenta pdfplumber em todas as páginas
   ├── Se extrair texto → continua com pdfplumber
   └── Se falhar → tenta PyPDF2
2. Se extração direta falhar completamente
   └── Executa OCR completo no documento
3. Salva resultado final
```

**Vantagens**:

- Melhor qualidade quando possível (extração direta)
- Fallback robusto para documentos problemáticos
- Processamento adaptativo por página

## ⚙️ Configuração (config.ini)

```ini
[Paths]
PDF_PATH=caminho/para/arquivo.pdf
OUTPUT_PATH_DIRECT=_direct.txt
OUTPUT_PATH_HYBRID=_hybrid.txt  
OUTPUT_PATH_OCR=_ocr.txt
```

### Campos de Configuração

- **PDF_PATH**: Caminho absoluto para o arquivo PDF de entrada
- **OUTPUT_PATH_DIRECT**: Arquivo de saída para extração direta
- **OUTPUT_PATH_HYBRID**: Arquivo de saída para extração híbrida
- **OUTPUT_PATH_OCR**: Arquivo de saída para extração OCR

### Tratamento de Encoding

O sistema tenta automaticamente os seguintes encodings para o config.ini:

1. UTF-8
2. UTF-8-SIG (com BOM)
3. Latin1
4. CP1252

## 🔧 Instalação e Configuração

### 1. Ambiente Python

```bash
# Ativar ambiente virtual
C:/Users/milso/.virtualenvs/OneDrive_-_Universidade_Federal_do_ABC-rilybLrp/Scripts/python.exe

# Instalar dependências principais
pip install pdfplumber PyPDF2 pdf2image pytesseract pillow
```

### 2. Dependências do Sistema

**Tesseract OCR** (Windows):

- Download: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- Instalação padrão: `C:\Program Files\Tesseract-OCR\`
- Configurar PATH ou usar caminho absoluto no código

**Poppler** (para pdf2image):

- Download: [https://poppler.freedesktop.org/](https://poppler.freedesktop.org/)
- Adicionar ao PATH do sistema

### 3. Configuração do Arquivo config.ini

1. Copiar `config.ini` para o diretório Scripts/
2. Ajustar `PDF_PATH` para o arquivo desejado
3. Configurar caminhos de saída conforme necessário

## 🚦 Execução

### Comando Básico

```bash
cd Scripts/
python pdf_extractor_hybrid.py  # Recomendado para uso geral
```

### Execução Específica

```bash
python pdf_extractor_direct.py  # Apenas extração direta
python pdf_extractor_ocr.py     # Apenas OCR
```

### Com Ambiente Virtual

```bash
C:/Users/milso/.virtualenvs/OneDrive_-_Universidade_Federal_do_ABC-rilybLrp/Scripts/python.exe pdf_extractor_hybrid.py
```

## 📊 Sistema de Logging

### Níveis de Log

- **INFO**: Progresso normal de execução
- **WARNING**: Problemas não críticos (páginas com erro)
- **ERROR**: Erros que impedem execução
- **DEBUG**: Informações detalhadas de depuração

### Exemplos de Logs

```text
INFO:__main__:Configuração carregada com encoding: utf-8
INFO:__main__:Tentando extração direta...
INFO:__main__:pdfplumber extraiu texto de 245 páginas
INFO:__main__:Arquivo salvo com 863269 caracteres
INFO:__main__:✅ Extração concluída com sucesso!
```

## 🛡️ Tratamento de Erros

### Estratégias Implementadas

1. **Configuração**:

   - Múltiplos encodings para config.ini
   - Validação de seções e chaves obrigatórias
   - Mensagens de erro específicas
2. **Extração**:

   - Try-catch por página individual
   - Fallback entre métodos de extração
   - Continuação mesmo com páginas problemáticas
3. **Memória**:

   - Garbage collection forçado
   - Limpeza de objetos de imagem
   - Liberação de recursos PDF
4. **Arquivo**:

   - Limpeza de caracteres problemáticos
   - Normalização de quebras de linha
   - Encoding UTF-8 consistente

## 💡 Prompts para IA - Desenvolvimento de Novas Funcionalidades

### Estrutura de Prompt Base

```text
CONTEXTO: Sistema de extração de PDF em Python com 3 módulos especializados.

ARQUITETURA ATUAL:
- pdf_extractor_direct.py: Extração direta (pdfplumber + PyPDF2)
- pdf_extractor_ocr.py: OCR com pytesseract 
- pdf_extractor_hybrid.py: Estratégia adaptativa

TECNOLOGIAS:
- Python 3.13.7, pdfplumber 0.11.7, PyPDF2 3.0.1, pytesseract 0.3.13
- pdf2image 1.17.0, Pillow 11.3.0, configparser 7.2.0
- Ambiente: Virtual Environment com Pipenv

FUNCIONALIDADE DESEJADA: [Descrever nova funcionalidade]

REQUISITOS:
- Manter compatibilidade com config.ini existente
- Seguir padrão de logging atual
- Implementar tratamento de erros robusto
- Otimizar uso de memória
- Documentar adequadamente
```

### Exemplos de Funcionalidades Potenciais

#### 1. Extração por Lotes

```text
FUNCIONALIDADE: Processamento de múltiplos PDFs em paralelo
- Aceitar diretório como entrada
- Processamento multithread/asyncio
- Relatório consolidado de resultados
- Progress bar para acompanhamento
```

#### 2. Interface Gráfica

```text
FUNCIONALIDADE: GUI com tkinter ou PyQt
- Seleção de arquivos via dialog
- Preview do texto extraído
- Configuração visual de parâmetros OCR
- Export em múltiplos formatos
```

#### 3. API REST

```text
FUNCIONALIDADE: Serviço web com FastAPI
- Upload de arquivos PDF
- Processamento assíncrono
- Retorno em JSON/texto
- Documentação automática Swagger
```

#### 4. Análise de Qualidade

```text
FUNCIONALIDADE: Métricas de qualidade da extração
- Confidence score do OCR
- Detecção de texto corrupto
- Sugestões de melhoria
- Comparação entre métodos
```

#### 5. Pré-processamento de Imagens

```text
FUNCIONALIDADE: Melhoria de qualidade para OCR
- Filtros de ruído
- Correção de inclinação
- Ajuste de contraste/brilho
- Detecção de layout automática
```

## 🔮 Roadmap Sugerido

### Versão 2.0

- [ ] Interface gráfica básica
- [ ] Processamento em lotes
- [ ] Suporte a múltiplos idiomas OCR
- [ ] Export para formatos estruturados (JSON, XML)

### Versão 3.0

- [ ] API REST completa
- [ ] Machine Learning para classificação de documentos
- [ ] Processamento distribuído
- [ ] Dashboard de monitoramento

### Versão 4.0

- [ ] Integração com cloud storage
- [ ] OCR com modelos de deep learning
- [ ] Análise semântica de conteúdo
- [ ] Microserviços arquitetura

## 📚 Recursos Adicionais

### Documentação das Bibliotecas

- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [PyPDF2](https://pypdf2.readthedocs.io/)
- [pytesseract](https://github.com/madmaze/pytesseract)
- [pdf2image](https://github.com/Belval/pdf2image)

### Tesseract OCR

- [Documentação oficial](https://tesseract-ocr.github.io/)
- [Idiomas suportados](https://github.com/tesseract-ocr/tessdata)
- [Configurações avançadas](https://github.com/tesseract-ocr/tesseract/wiki/Command-Line-Usage)

---

**Autor**: Sistema de Extração PDF Python
**Última Atualização**: 03/10/2025
**Versão**: 1.0
**Licença**: MIT
