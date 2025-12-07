"""
Extração usando PDFQuery - Permite queries CSS-like em PDFs
Biblioteca: pdfquery
Instalação: pip install pdfquery
"""
import pdfquery
import xml.etree.ElementTree as ET
import os

def extract_text_pdfquery(pdf_path, txt_path):
    """
    Extrai texto usando PDFQuery - permite seleções precisas com CSS-like queries
    """
    try:
        # Abre o PDF
        pdf = pdfquery.PDFQuery(pdf_path)
        pdf.load()
        
        # Extrai todo o texto
        text_elements = pdf.tree.iter()
        
        extracted_text = []
        for element in text_elements:
            if element.text and element.text.strip():
                extracted_text.append(element.text.strip())
        
        # Salva o texto extraído
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_text))
        
        print(f"PDFQuery: Texto extraído para {txt_path}")
        
    except Exception as e:
        print(f"Erro no PDFQuery: {e}")

def extract_structured_pdfquery(pdf_path, output_path):
    """
    Extrai informações estruturadas usando PDFQuery
    """
    try:
        pdf = pdfquery.PDFQuery(pdf_path)
        pdf.load()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("Extração Estruturada - PDFQuery\n")
            f.write("="*50 + "\n\n")
            
            # Tenta extrair títulos (texto em negrito ou maior)
            f.write("=== TÍTULOS POTENCIAIS ===\n")
            try:
                titles = pdf.tree.xpath("//LTTextBox[contains(@fontname,'Bold') or @fontsize>12]")
                for title in titles[:10]:  # Limita a 10 primeiros
                    if title.text and title.text.strip():
                        f.write(f"- {title.text.strip()}\n")
            except:
                f.write("Não foi possível extrair títulos\n")
            
            f.write("\n=== TEXTO GERAL ===\n")
            # Extrai todo o texto de forma organizada
            text_boxes = pdf.tree.xpath("//LTTextBox")
            for i, box in enumerate(text_boxes[:20]):  # Limita a 20 primeiros
                if box.text and box.text.strip():
                    f.write(f"Bloco {i+1}: {box.text.strip()}\n\n")
        
        print(f"PDFQuery: Extração estruturada salva em {output_path}")
        
    except Exception as e:
        print(f"Erro na extração estruturada com PDFQuery: {e}")

# Sistema multiprojeto - usa variável de ambiente CURRENT_PROJECT
if __name__ == "__main__":
    import glob
    
    # Obtém o projeto atual da variável de ambiente
    current_project = os.environ.get('CURRENT_PROJECT', '000.002')
    pdf_base_path = os.environ.get('PDF_BASE_PATH', '../pdfs')
    results_base_path = os.environ.get('RESULTS_BASE_PATH', '../resultados')
    
    # Descobre automaticamente os PDFs do projeto
    pdf_pattern = f"{pdf_base_path}/{current_project}/*.pdf"
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"❌ Nenhum PDF encontrado em {pdf_base_path}/{current_project}/")
    else:
        print(f"📂 Processando projeto {current_project} com {len(pdf_files)} PDFs")
        
        # Garante que o diretório de saída existe para o projeto
        project_output_dir = f"{results_base_path}/{current_project}"
        os.makedirs(project_output_dir, exist_ok=True)
        
        for pdf_file in pdf_files:
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Cria pasta individual para cada arquivo PDF
            pdf_dir = f"{project_output_dir}/{filename}"
            os.makedirs(pdf_dir, exist_ok=True)
            
            # Extração de texto simples
            txt_output = f"{pdf_dir}/pdfquery_{filename}.txt"
            print(f"Extraindo texto de {pdf_file} com PDFQuery...")
            extract_text_pdfquery(pdf_file, txt_output)
            
            # Extração estruturada
            struct_output = f"{pdf_dir}/pdfquery_estruturado_{filename}.txt"
            print(f"Fazendo extração estruturada de {pdf_file}...")
            extract_structured_pdfquery(pdf_file, struct_output)
