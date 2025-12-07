"""
Script para extrair tabelas usando Camelot
Ideal para PDFs com tabelas estruturadas
"""
import camelot
import os

def extract_tables_camelot(pdf_path, output_dir):
    """Extrai tabelas usando Camelot"""
    try:
        # Extrai tabelas de todas as páginas
        tables = camelot.read_pdf(pdf_path, pages='all')
        
        filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        print(f"\nCamelot: Encontradas {len(tables)} tabelas em {pdf_path}")
        
        if len(tables) == 0:
            print("Nenhuma tabela encontrada.")
            return
        
        # Salva cada tabela em CSV
        for i, table in enumerate(tables):
            csv_path = f"{output_dir}/camelot_{filename}_tabela_{i+1}.csv"
            table.to_csv(csv_path)
            print(f"Tabela {i+1} salva: {csv_path}")
            print(f"  Dimensões: {table.shape}")
            print(f"  Acurácia: {table.accuracy:.2f}")
            
        # Salva relatório completo
        report_path = f"{output_dir}/camelot_{filename}_relatorio.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"RELATÓRIO CAMELOT - {filename}\n")
            f.write("="*50 + "\n\n")
            
            for i, table in enumerate(tables):
                f.write(f"TABELA {i+1}:\n")
                f.write(f"Dimensões: {table.shape}\n")
                f.write(f"Acurácia: {table.accuracy:.2f}\n")
                f.write(f"Página: {table.page}\n")
                f.write("\nDados (primeiras 5 linhas):\n")
                f.write(table.df.head().to_string())
                f.write("\n" + "="*30 + "\n\n")
                
        print(f"Relatório salvo: {report_path}")
        
    except Exception as e:
        print(f"Erro no Camelot: {e}")

# Executa para arquivos da nova estrutura organizada
if __name__ == "__main__":
    # Paths atualizados para nova estrutura
    pdf_files = [
        "../pdfs/000.002/000.002.pdf", 
        "../pdfs/000.002/CP_000.002.pdf"
    ]
    output_dir = "../resultados/000.002/csv"
    
    # Garante que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            print(f"Processando {pdf_file} com Camelot...")
            extract_tables_camelot(pdf_file, output_dir)
        else:
            print(f"Arquivo não encontrado: {pdf_file}")
            print(f"Verifique se o arquivo existe em: {os.path.abspath(pdf_file)}")
