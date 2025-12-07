### **Análise Comparativa da Extração de Texto das Diferentes Bibliotecas Python**

Após revisar os arquivos extraídos utilizando  **PyPDF2** ,  **pdfMiner.six** , **PyMuPDF (fitz)** e  **pdfPlumber** , aqui está uma avaliação detalhada da qualidade e completude dos textos extraídos.

---

### **Critérios de Avaliação**

1. **Fidelidade ao conteúdo original** → Se a estrutura, formatação e texto foram preservados.
2. **Completude** → Se toda a informação relevante foi extraída.
3. **Rendição correta de caracteres especiais** → Se acentos, espaços e símbolos estão corretos.
4. **Separação de parágrafos e seções** → Se a estrutura do documento original foi mantida.
5. **Ruído e excesso de espaços em branco** → Avaliação da presença de linhas em branco excessivas ou caracteres indesejados.

---

### **Resultados da Avaliação**

#### **1. PyPDF2**

* **Qualidade geral** : **Ruim**
* **Problemas detectados** :
* Muitas quebras de linha desnecessárias.
* Alguns caracteres aparecem separados por espaços (exemplo: “P E R G U N T A S E R E S P O S T A S”).
* Estrutura do documento se perde.
* **Conclusão** : PyPDF2 tem dificuldades com documentos estruturados e complexos.

---

#### **2. pdfMiner.six**

* **Qualidade geral** : **Razoável**
* **Problemas detectados** :
* Mantém a estrutura do texto melhor que o PyPDF2.
* Ainda apresenta alguns espaçamentos desnecessários.
* O sumário está parcialmente desalinhado.
* **Conclusão** : Melhor que PyPDF2, mas ainda apresenta formatação ruim.

---

#### **3. PyMuPDF (fitz)** 

* **Qualidade geral** : **Boa**
* **Pontos positivos** :
* Mantém bem a formatação do texto.
* Boa separação de parágrafos.
* Texto extraído de forma mais limpa.
* **Problemas detectados** :
* Pequenos erros em espaçamentos e formatação, mas bem menos que as bibliotecas anteriores.
* **Conclusão** : Uma das melhores opções, com alto nível de fidelidade ao original.

---

#### **4. pdfPlumber**

* **Qualidade geral** : **Excelente**
* **Pontos positivos** :
* Mantém a estrutura original quase perfeita.
* Poucos problemas com espaçamento.
* Maior fidelidade ao conteúdo do PDF.
* **Problemas detectados** :
* Praticamente nenhum relevante.
* **Conclusão** : Melhor opção para extração de textos estruturados.

---

### **Classificação Final**

| Biblioteca           | Fidelidade ao Original | Formatação | Ruído e Espaços Extras | Melhor Uso       |
| -------------------- | ---------------------- | ------------ | ------------------------ | ---------------- |
| **PyPDF2**     | ✗✗✗                 | ✗✗✗       | ✗✗✗                   | **Evitar** |
| **pdfMiner**   | ✓✓                   | ✗✗         | ✓✓                     | **Médio** |
| **PyMuPDF**    | ✓✓✓                 | ✓✓         | ✓✓✓                   | **Ótima** |
| **pdfPlumber** | ✓✓✓✓               | ✓✓✓✓     | ✓✓✓✓                 | **Melhor** |

---

### **Conclusão e Recomendação**

* **pdfPlumber** se destacou como a melhor opção, preservando mais fielmente o texto original e a estrutura do documento.
* **PyMuPDF** também teve um bom desempenho e pode ser usado como alternativa.
* **pdfMiner** oferece uma extração aceitável, mas precisa de ajustes.
* **PyPDF2** foi a pior opção, apresentando perda de formatação e caracteres desalinhados.
