"""
Extração usando Tabula - Especializada em tabelas
Biblioteca: tabula-py
Instalação: pip install tabula-py
Requer Java instalado no sistema
"""
import tabula
import os

def extract_tables_tabula(pdf_path, output_dir):
    """
    Extrai tabelas usando Tabula - boa alternativa ao Camelot para tabelas
    """
    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Extrai todas as tabelas
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        
        results = []
        for i, table in enumerate(tables):
            # Salva cada tabela como CSV
            csv_path = os.path.join(output_dir, f"tabela_{i+1}.csv")
            table.to_csv(csv_path, index=False)
            
            # Salva como texto
            txt_path = os.path.join(output_dir, f"tabela_{i+1}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Tabela {i+1}\n")
                f.write("="*50 + "\n")
                f.write(table.to_string(index=False))
                f.write("\n\n")
            
            results.append({
                'tabela': i+1,
                'linhas': len(table),
                'colunas': len(table.columns)
            })
        
        # Relatório geral
        report_path = os.path.join(output_dir, "relatorio_tabula.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("Relatório de Extração - Tabula\n")
            f.write(f"Arquivo: {pdf_path}\n")
            f.write(f"Total de tabelas encontradas: {len(tables)}\n\n")
            
            for result in results:
                f.write(f"Tabela {result['tabela']}: {result['linhas']}x{result['colunas']}\n")
        
        print(f"Tabula: {len(tables)} tabelas extraídas com sucesso!")
        return results
        
    except Exception as e:
        print(f"Erro no Tabula: {e}")
        return []

def extract_text_tabula(pdf_path, output_path):
    """
    Extrai texto completo usando Tabula
    """
    try:
        # Extrai texto de todas as páginas
        tables = tabula.read_pdf(pdf_path, pages='all', output_format='dataframe')
        
        with open(output_path, "w", encoding="utf-8") as f:
            if isinstance(tables, list):
                for i, table in enumerate(tables):
                    f.write(f"=== Tabela/Seção {i+1} ===\n")
                    f.write(table.to_string(index=False))
                    f.write("\n\n")
            else:
                f.write(tables.to_string(index=False))
        
        print(f"Tabula: Texto extraído para {output_path}")
        
    except Exception as e:
        print(f"Erro na extração de texto com Tabula: {e}")

# Exemplo de uso para os arquivos da pasta 000.002
if __name__ == "__main__":
    pdf_files = [
        "../pdfs/000.002/000.002.pdf",
        "../pdfs/000.002/CP_000.002.pdf"
    ]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            filename = os.path.splitext(os.path.basename(pdf_file))[0]
            
            # Extração de tabelas
            output_dir = f"../resultados/000.002/txt/tabula_{filename}"
            print(f"Processando tabelas de {pdf_file}...")
            extract_tables_tabula(pdf_file, output_dir)
            
            # Extração de texto
            txt_output = f"../resultados/000.002/txt/tabula_{filename}.txt"
            print(f"Extraindo texto de {pdf_file}...")
            extract_text_tabula(pdf_file, txt_output)
