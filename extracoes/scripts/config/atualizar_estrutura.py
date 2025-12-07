"""
Script para atualizar todos os scripts de extração para a nova estrutura de pastas
"""
import os
import glob
import sys

def update_script_paths():
    """Atualiza os caminhos em todos os scripts de extração"""
    
    scripts_dir = "scripts"
    
    # Mapeamento de substituições
    path_updates = {
        '"000.002/000.002.pdf"': '"../pdfs/000.002/000.002.pdf"',
        '"000.002/CP_000.002.pdf"': '"../pdfs/000.002/CP_000.002.pdf"',
        "'000.002/000.002.pdf'": "'../pdfs/000.002/000.002.pdf'",
        "'000.002/CP_000.002.pdf'": "'../pdfs/000.002/CP_000.002.pdf'",
        'output_dir = "000.002"': 'output_dir = "../resultados/000.002/txt"',
        "output_dir = '000.002'": "output_dir = '../resultados/000.002/txt'",
        '"000.002/"': '"../resultados/000.002/txt/"',
        "'000.002/'": "'../resultados/000.002/txt/'",
        'f"000.002/': 'f"../resultados/000.002/txt/',
        "f'000.002/": "f'../resultados/000.002/txt/",
        '"000.002/camelot_': '"../resultados/000.002/csv/camelot_',
        "'000.002/camelot_": "'../resultados/000.002/csv/camelot_",
        '"000.002/pymupdf4llm_': '"../resultados/000.002/md/pymupdf4llm_',
        "'000.002/pymupdf4llm_": "'../resultados/000.002/md/pymupdf4llm_",
    }
    
    # Encontra todos os scripts Python na pasta scripts
    script_files = glob.glob(os.path.join(scripts_dir, "extracao_*.py"))
    
    print(f"🔧 Atualizando {len(script_files)} scripts...")
    
    for script_path in script_files:
        print(f"\n📝 Processando: {os.path.basename(script_path)}")
        
        try:
            # Lê o conteúdo do arquivo
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aplica as substituições
            original_content = content
            for old_path, new_path in path_updates.items():
                content = content.replace(old_path, new_path)
            
            # Adiciona verificação de diretório se não existir
            if 'os.makedirs' not in content and 'output_dir' in content:
                content = content.replace(
                    'if __name__ == "__main__":',
                    '''if __name__ == "__main__":
    import os'''
                )
                content = content.replace(
                    'for pdf_file in pdf_files:',
                    '''# Garante que os diretórios de saída existem
    if 'output_dir' in locals():
        os.makedirs(output_dir, exist_ok=True)
    
    for pdf_file in pdf_files:'''
                )
            
            # Salva apenas se houve mudanças
            if content != original_content:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Atualizado com sucesso!")
            else:
                print(f"  ⏭️ Nenhuma mudança necessária")
                
        except Exception as e:
            print(f"  ❌ Erro ao processar: {e}")

def create_master_script():
    """Cria um script mestre para executar extrações com a nova estrutura"""
    
    master_content = '''"""
SCRIPT MESTRE - EXTRAÇÃO DE PDFs COM NOVA ESTRUTURA ORGANIZADA
Execute este script da pasta scripts/ para rodar todas as extrações
"""
import os
import sys
import time

def run_extraction_script(script_name, description):
    """Executa um script de extração individual"""
    print(f"\\n{'='*60}")
    print(f"🚀 {description}")
    print(f"📄 Executando: {script_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Executa o script
        exit_code = os.system(f"python {script_name}")
        
        if exit_code == 0:
            print(f"✅ {script_name} executado com sucesso!")
        else:
            print(f"⚠️ {script_name} terminou com código: {exit_code}")
            
    except Exception as e:
        print(f"❌ Erro ao executar {script_name}: {e}")
    
    elapsed = time.time() - start_time
    print(f"⏱️ Tempo decorrido: {elapsed:.2f}s")

def main():
    """Função principal - executa todas as extrações"""
    print("🏁 INICIANDO EXTRAÇÃO COMPLETA DE PDFs")
    print("📁 Estrutura organizada ativa!")
    print(f"📍 Diretório atual: {os.getcwd()}")
    
    # Lista de scripts para executar
    extraction_scripts = [
        ("extracao_pyMuPdf.py", "🚀 PyMuPDF - Extração rápida e eficiente"),
        ("extracao_pdfPlumber.py", "📊 PDFPlumber - Estruturas e tabelas"),
        ("extracao_pdfMiner.py", "🔍 PDFMiner - Análise profunda"),
        ("extracao_pyPdf2.py", "📄 PyPDF2 - Biblioteca clássica"),
        ("extracao_pymupdf4llm.py", "🤖 PyMuPDF4LLM - Otimizado para IA"),
        ("extracao_pdfquery.py", "🔎 PDFQuery - Consultas estruturadas"),
        ("extracao_camelot_tabelas.py", "📈 Camelot - Especialista em tabelas"),
        ("extracao_camelot.py", "📊 Camelot - Extração de tabelas"),
    ]
    
    total_start = time.time()
    successful = 0
    failed = 0
    
    for script_name, description in extraction_scripts:
        if os.path.exists(script_name):
            run_extraction_script(script_name, description)
            successful += 1
        else:
            print(f"⚠️ Script não encontrado: {script_name}")
            failed += 1
    
    # Relatório final
    total_elapsed = time.time() - total_start
    print(f"\\n{'='*60}")
    print("📋 RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"✅ Scripts executados: {successful}")
    print(f"❌ Scripts faltando: {failed}")
    print(f"⏱️ Tempo total: {total_elapsed:.2f}s")
    print(f"📁 Resultados em: ../resultados/000.002/")
    print(f"📊 Tabelas em: ../resultados/000.002/csv/")
    print(f"📝 Textos em: ../resultados/000.002/txt/")
    print(f"🤖 Markdown em: ../resultados/000.002/md/")
    
    print("\\n🎉 EXTRAÇÃO COMPLETA FINALIZADA!")

if __name__ == "__main__":
    main()
'''
    
    with open("scripts/executar_todas_extracoes.py", "w", encoding="utf-8") as f:
        f.write(master_content)
    
    print("✅ Script mestre criado: scripts/executar_todas_extracoes.py")

def show_new_structure():
    """Mostra a nova estrutura de pastas"""
    print("\n📁 NOVA ESTRUTURA ORGANIZADA:")
    print("="*50)
    
    structure = """
extracoes/
├── 📂 scripts/           # Scripts de extração
├── 📂 resultados/        # Resultados organizados
│   └── 000.002/
│       ├── txt/         # Textos extraídos
│       ├── csv/         # Tabelas CSV
│       ├── md/          # Markdown para LLMs
│       └── relatorios/  # Relatórios de análise
├── 📂 pdfs/             # PDFs originais
├── 📂 ranking/          # Análises comparativas
└── 📂 docs/             # Documentação
"""
    print(structure)

if __name__ == "__main__":
    print("🚀 ATUALIZADOR DE ESTRUTURA DE PASTAS")
    print("="*50)
    
    # Verifica se estamos no diretório correto
    if not os.path.exists("scripts"):
        print("❌ Erro: Execute este script da pasta 'extracoes'")
        sys.exit(1)
    
    # Executa as atualizações
    update_script_paths()
    create_master_script()
    show_new_structure()
    
    print("\n✅ ATUALIZAÇÃO CONCLUÍDA!")
    print("💡 Para executar todas as extrações: cd scripts && python executar_todas_extracoes.py")
