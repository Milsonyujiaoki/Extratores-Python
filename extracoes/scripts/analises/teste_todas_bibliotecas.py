"""
Script principal para testar todas as bibliotecas de extração
nos arquivos da pasta 000.002
"""
import os
import time
from datetime import datetime

def run_extraction_tests():
    """
    Executa todos os testes de extração disponíveis
    """
    print("="*60)
    print("TESTE DE BIBLIOTECAS DE EXTRAÇÃO DE PDF")
    print("="*60)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Lista de arquivos PDF para testar
    pdf_files = [
        "000.002/000.002.pdf",
        "000.002/CP_000.002.pdf"
    ]
    
    # Verifica se os arquivos existem
    existing_files = []
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            existing_files.append(pdf_file)
            print(f"✓ Arquivo encontrado: {pdf_file}")
        else:
            print(f"✗ Arquivo não encontrado: {pdf_file}")
    
    if not existing_files:
        print("Nenhum arquivo PDF encontrado para testar!")
        return
    
    print(f"\nTestando {len(existing_files)} arquivo(s)...\n")
    
    # Lista de scripts de extração para executar
    extraction_scripts = [
        ("PyPDF2", "extracao_pyPdf2.py"),
        ("PDFMiner", "extracao_pdfMiner.py"),
        ("PyMuPDF", "extracao_pyMuPdf.py"),
        ("PDFPlumber", "extracao_pdfPlumber.py"),
        ("Camelot", "extracao_camelot.py"),
        ("Tabula", "extracao_tabula.py"),
        ("Tika", "extracao_tika.py"),
        ("PDFQuery", "extracao_pdfquery.py"),
        ("PyMuPDF4LLM", "extracao_pymupdf4llm.py")
    ]
    
    results = {}
    
    for name, script in extraction_scripts:
        print(f"--- Testando {name} ---")
        start_time = time.time()
        
        try:
            if os.path.exists(script):
                # Executa o script
                exec(open(script).read())
                status = "✓ Sucesso"
            else:
                status = "✗ Script não encontrado"
        except Exception as e:
            status = f"✗ Erro: {str(e)[:50]}..."
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        results[name] = {
            'status': status,
            'time': execution_time
        }
        
        print(f"   {status}")
        print(f"   Tempo: {execution_time:.2f}s")
        print()
    
    # Relatório final
    print("="*60)
    print("RELATÓRIO FINAL")
    print("="*60)
    
    for name, result in results.items():
        print(f"{name:15} | {result['status']:20} | {result['time']:6.2f}s")
    
    print(f"\nTeste concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_extraction_tests()
