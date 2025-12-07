# 📊 Sistema de Extração de PDFs - Configuração e Uso

## ✨ **FUNCIONALIDADES IMPLEMENTADAS**

### 🎯 **Principais Melhorias:**
- ✅ **Detecção de arquivos existentes** - Evita duplicatas automáticamente
- ✅ **Configuração flexível de caminhos** - Fácil adaptação para diferentes estruturas
- ✅ **Arquivo de configuração separado** - Personalização sem modificar código
- ✅ **Múltiplas opções de execução** - Pular existentes ou forçar re-execução
- ✅ **Relatórios detalhados** - Estatísticas completas de execução
- ✅ **Suporte a diferentes estruturas de projeto** - Flexível para várias organizações

---

## 🚀 **COMO USAR**

### 1. **Configuração Básica (Primeira vez)**

1. **Edite o arquivo `config_extracoes.py`** para definir seus caminhos:
```python
PDF_BASE_PATH = "../pdfs"          # Onde estão seus PDFs
RESULTS_BASE_PATH = "../resultados" # Onde salvar resultados
PROJECT_PREFIX = "000."            # Prefixo dos projetos
```

2. **Execute o script mestre:**
```bash
python executar_todas_extracoes.py
```

### 2. **Opções de Execução**

Quando executar o script, você terá as seguintes opções:

#### **Modo de Processamento:**
- **Opção 1 (Recomendado):** Pula arquivos já existentes - Execução rápida
- **Opção 2:** Re-executa tudo - Força recriação de todos os arquivos

#### **Seleção de Projetos:**
- **Todos os projetos:** Digite `s` ou Enter
- **Projetos específicos:** Digite `n` e depois selecione os números

---

## 📂 **CONFIGURAÇÕES AVANÇADAS**

### **Exemplo 1: Estrutura Corporativa**
```python
PDF_BASE_PATH = "//servidor/documentos/contratos"
RESULTS_BASE_PATH = "//servidor/análises/extrações"
PROJECT_PREFIX = "contrato_"
```

### **Exemplo 2: Organização por Data**
```python
PDF_BASE_PATH = "../documentos/2024"
RESULTS_BASE_PATH = "../extrações/2024"
PROJECT_PREFIX = "2024-"
```

### **Exemplo 3: Estrutura Simples**
```python
PDF_BASE_PATH = "pdfs"
RESULTS_BASE_PATH = "results"
PROJECT_PREFIX = "projeto"
```

---

## 🛠️ **PERSONALIZAÇÃO DE SCRIPTS**

### **Modificar Lista de Scripts:**
No arquivo `config_extracoes.py`, edite a lista `EXTRACTION_SCRIPTS`:

```python
EXTRACTION_SCRIPTS = [
    ("extracao_pyMuPdf.py", "🚀 PyMuPDF - Rápido"),
    ("extracao_camelot_tabelas.py", "📈 Camelot - Tabelas"),
    # Comente scripts que não quiser usar:
    # ("extracao_pdfMiner.py", "🔍 PDFMiner"),
]
```

### **Modificar Estrutura de Pastas:**
```python
RESULT_SUBDIRS = ['textos', 'tabelas', 'markdown', 'relatórios']
```

---

## 📊 **COMO FUNCIONA A DETECÇÃO DE DUPLICATAS**

### **Sistema Inteligente:**
- O sistema verifica se já existem arquivos gerados por cada script
- Compara padrões específicos para cada tipo de extração
- Pula automaticamente scripts já executados (modo padrão)
- Permite forçar re-execução quando necessário

### **Padrões de Detecção:**
```python
SCRIPT_OUTPUT_PATTERNS = {
    'extracao_pyMuPdf.py': ['txt/PyMuPDF_*.txt'],
    'extracao_camelot_tabelas.py': ['csv/*_T*.csv', 'relatorios/camelot_*.xlsx'],
    # ... outros padrões
}
```

---

## 🎯 **EXEMPLOS PRÁTICOS**

### **Cenário 1: Primeira Execução**
```bash
# Todos os scripts são executados
python executar_todas_extracoes.py
```

### **Cenário 2: Re-execução (com arquivos existentes)**
```bash
# Apenas scripts não executados são processados
python executar_todas_extracoes.py
# Escolha: 1 (pular existentes)
```

### **Cenário 3: Forçar Recriação**
```bash
# Todos os scripts são re-executados
python executar_todas_extracoes.py
# Escolha: 2 (re-executar tudo)
```

### **Cenário 4: Projetos Específicos**
```bash
python executar_todas_extracoes.py
# Escolha: n (não processar todos)
# Digite: 1,3,5 (apenas projetos 1, 3 e 5)
```

---

## 🔧 **ESTRUTURA DE ARQUIVOS**

### **Configuração:**
```
scripts/
├── executar_todas_extracoes.py      # Script principal
├── config_extracoes.py              # Configuração principal
├── config_exemplo_alternativo.py    # Exemplo alternativo
└── README_configuracao.md           # Este arquivo
```

### **Resultados Gerados:**
```
resultados/
├── projeto1/
│   ├── txt/           # Textos extraídos
│   ├── csv/           # Tabelas CSV
│   ├── md/            # Markdown
│   └── relatorios/    # Consolidados
└── projeto2/
    └── ...
```

---

## 📋 **RELATÓRIOS GERADOS**

### **Informações Incluídas:**
- ✅ Scripts executados com sucesso
- ⏭️ Scripts pulados (arquivos já existem)
- ❌ Scripts com erro ou não encontrados
- ⏱️ Tempo total de execução
- 📅 Data/hora de conclusão
- 📂 Estrutura de resultados

### **Exemplo de Relatório:**
```
📋 RELATÓRIO FINAL
📂 Projetos processados: 3
✅ Scripts executados: 15
⏭️ Scripts pulados (já existem): 6
❌ Scripts com erro/faltando: 0
⏱️ Tempo total: 45.67s
📅 Concluído em: 22/07/2025 23:10:22
```

---

## 🚨 **SOLUÇÃO DE PROBLEMAS**

### **Problema: "Nenhum projeto encontrado"**
- Verifique se `PDF_BASE_PATH` está correto
- Confirme se existem pastas com o `PROJECT_PREFIX` especificado
- Verifique se as pastas contêm arquivos PDF

### **Problema: "Script não encontrado"**
- Verifique se os arquivos de extração estão na pasta `scripts/`
- Confirme se os nomes dos scripts em `EXTRACTION_SCRIPTS` estão corretos

### **Problema: "Configurações não carregadas"**
- Verifique se `config_extracoes.py` existe na pasta `scripts/`
- Confirme se não há erros de sintaxe no arquivo de configuração

---

## 💡 **DICAS AVANÇADAS**

### **1. Backup de Configuração**
Mantenha sempre uma cópia do arquivo `config_extracoes.py` antes de modificar

### **2. Configuração por Ambiente**
Crie diferentes arquivos de configuração para diferentes ambientes:
- `config_producao.py`
- `config_teste.py`
- `config_desenvolvimento.py`

### **3. Logs Detalhados**
O sistema mostra informações em tempo real - use para monitorar progresso

### **4. Estruturas Flexíveis**
O sistema adapta-se a qualquer estrutura de pastas - experimente diferentes organizações

---

## 🎉 **BENEFÍCIOS IMPLEMENTADOS**

✅ **Economia de Tempo:** Evita re-processamento desnecessário  
✅ **Flexibilidade:** Adapta-se a diferentes estruturas  
✅ **Controle:** Opções de execução personalizáveis  
✅ **Transparência:** Relatórios detalhados  
✅ **Manutenibilidade:** Configuração centralizada  
✅ **Robustez:** Detecção inteligente de duplicatas  

---

**Sistema desenvolvido para máxima eficiência e flexibilidade na extração de PDFs!** 🚀
