"""
Demonstração de bibliotecas avançadas: Unstructured e LlamaIndex
Estas bibliotecas não foram incluídas no teste principal pelos motivos explicados no ranking.
"""

# =============================================================================
# UNSTRUCTURED - Biblioteca para múltiplos formatos de documento
# =============================================================================
"""
Instalação:
pip install unstructured[pdf]
pip install unstructured[local-inference]

Características:
- Suporte a PDF, DOCX, HTML, TXT, XML, etc.
- Particionamento inteligente de documentos
- Detecção automática de elementos
- Ideal para pipelines RAG complexos
"""

def exemplo_unstructured():
    """
    Exemplo de uso da biblioteca Unstructured
    """
    try:
        from unstructured.partition.pdf import partition_pdf
        import os
        
        def extract_with_unstructured(pdf_path, output_path):
            # Particiona o PDF em elementos estruturados
            elements = partition_pdf(pdf_path)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=== EXTRAÇÃO COM UNSTRUCTURED ===\n\n")
                
                for element in elements:
                    # Cada elemento tem tipo (Title, Text, Table, etc.)
                    element_type = type(element).__name__
                    f.write(f"[{element_type}] {element.text}\n\n")
            
            print(f"Unstructured: Arquivo processado -> {output_path}")
            return len(elements)
        
        # Exemplo de uso
        pdf_files = [
            "000.002/000.002.pdf",
            "000.002/CP_000.002.pdf"
        ]
        
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                filename = os.path.splitext(os.path.basename(pdf_file))[0]
                output = f"000.002/unstructured_{filename}.txt"
                elements_count = extract_with_unstructured(pdf_file, output)
                print(f"  └─ {elements_count} elementos extraídos")
                
    except ImportError:
        print("❌ Unstructured não instalada. Instale com: pip install unstructured[pdf]")
    except Exception as e:
        print(f"❌ Erro no Unstructured: {e}")

# =============================================================================
# LLAMAINDEX (LlamaParse) - Serviço premium de parsing
# =============================================================================
"""
Instalação:
pip install llama-parse
pip install llama-index

Características:
- Serviço PAGO (requer API key)
- Parsing semântico avançado
- Otimizado para RAG
- Suporte a documentos complexos
"""

def exemplo_llamaparse():
    """
    Exemplo de uso do LlamaParse (requer API key)
    """
    try:
        from llama_parse import LlamaParse
        import os
        
        def extract_with_llamaparse(pdf_path, output_path):
            # Requer LLAMA_CLOUD_API_KEY no environment
            parser = LlamaParse(
                result_type="markdown",  # ou "text"
                language="portuguese",
                verbose=True
            )
            
            # Parse do documento
            documents = parser.load_data(pdf_path)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=== EXTRAÇÃO COM LLAMAPARSE ===\n\n")
                for doc in documents:
                    f.write(doc.text)
                    f.write("\n\n---\n\n")
            
            print(f"LlamaParse: Arquivo processado -> {output_path}")
            return len(documents)
        
        # Verifica se a API key está configurada
        api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        if not api_key:
            print("⚠️ LLAMA_CLOUD_API_KEY não configurada")
            print("   Configure com: set LLAMA_CLOUD_API_KEY=sua_chave_aqui")
            return
        
        # Exemplo de uso
        pdf_files = [
            "000.002/000.002.pdf",
            "000.002/CP_000.002.pdf"
        ]
        
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                filename = os.path.splitext(os.path.basename(pdf_file))[0]
                output = f"000.002/llamaparse_{filename}.md"
                docs_count = extract_with_llamaparse(pdf_file, output)
                print(f"  └─ {docs_count} documentos processados")
                
    except ImportError:
        print("❌ LlamaParse não instalada. Instale com: pip install llama-parse")
    except Exception as e:
        print(f"❌ Erro no LlamaParse: {e}")

# =============================================================================
# COMPARAÇÃO DE CASOS DE USO
# =============================================================================

def quando_usar_cada_biblioteca():
    """
    Guia de quando usar cada biblioteca
    """
    print("\n" + "="*60)
    print("🎯 GUIA DE ESCOLHA DE BIBLIOTECA")
    print("="*60)
    
    casos_uso = {
        "📄 Extração Simples de Texto": {
            "Recomendado": "PyMuPDF",
            "Alternativa": "PDFMiner",
            "Razão": "Velocidade e qualidade"
        },
        "📊 Documentos com Tabelas": {
            "Recomendado": "Camelot + PDFPlumber",
            "Alternativa": "Tabula (requer Java)",
            "Razão": "Especialização em estruturas tabulares"
        },
        "🤖 Integração com LLMs": {
            "Recomendado": "PyMuPDF4LLM",
            "Alternativa": "Unstructured",
            "Razão": "Formatação otimizada para IA"
        },
        "🏢 Pipeline Empresarial": {
            "Recomendado": "Unstructured",
            "Alternativa": "Combinação de bibliotecas",
            "Razão": "Suporte multi-formato e escalabilidade"
        },
        "💎 Documentos Críticos": {
            "Recomendado": "LlamaParse",
            "Alternativa": "Unstructured + PyMuPDF",
            "Razão": "Máxima qualidade (com custo)"
        },
        "🔬 Documentos Científicos": {
            "Recomendado": "LlamaParse",
            "Alternativa": "PDFMiner + pós-processamento",
            "Razão": "Compreensão semântica avançada"
        }
    }
    
    for caso, info in casos_uso.items():
        print(f"\n{caso}:")
        print(f"  ✅ Recomendado: {info['Recomendado']}")
        print(f"  🔄 Alternativa: {info['Alternativa']}")
        print(f"  💡 Razão: {info['Razão']}")

# =============================================================================
# DEMONSTRAÇÃO PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print("🧪 DEMONSTRAÇÃO - BIBLIOTECAS AVANÇADAS")
    print("="*50)
    
    print("\n1️⃣ Testando Unstructured...")
    exemplo_unstructured()
    
    print("\n2️⃣ Testando LlamaParse...")
    exemplo_llamaparse()
    
    print("\n3️⃣ Guia de uso...")
    quando_usar_cada_biblioteca()
    
    print("\n✅ Demonstração concluída!")
    print("\n💡 Dica: Para projetos reais, avalie o custo-benefício:")
    print("   • Gratuitas: PyMuPDF, Camelot, PDFPlumber")
    print("   • Premium: LlamaParse (melhor qualidade)")
    print("   • Intermediárias: Unstructured (mais features)")
