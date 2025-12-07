# -*- coding: utf-8 -*-
"""
Script de verificação de PDFs - Localiza e lista todos os PDFs disponíveis
"""
import os
import glob

def find_pdfs():
    """Encontra todos os PDFs no projeto"""
    print("🔍 LOCALIZANDO PDFs NO PROJETO")
    print("="*50)
    
    base_paths = [
        ".",
        "./pdfs",
        "../pdfs",
        "../../pdfs",
        "./extracoes",
        "../extracoes"
    ]
    
    pdf_locations = {}
    
    for base_path in base_paths:
        if os.path.exists(base_path):
            # Busca recursiva por PDFs
            pattern = os.path.join(base_path, "**", "*.pdf")
            found_pdfs = glob.glob(pattern, recursive=True)
            
            if found_pdfs:
                pdf_locations[base_path] = found_pdfs
                print(f"📁 {base_path}: {len(found_pdfs)} PDFs encontrados")
            else:
                print(f"📂 {base_path}: Nenhum PDF encontrado")
    
    if pdf_locations:
        print(f"\n📋 RESUMO DOS PDFs ENCONTRADOS:")
        total_pdfs = 0
        
        for location, pdfs in pdf_locations.items():
            print(f"\n📁 {location}:")
            
            # Agrupa por pasta
            folders = {}
            for pdf in pdfs:
                folder = os.path.dirname(pdf)
                if folder not in folders:
                    folders[folder] = []
                folders[folder].append(pdf)
            
            for folder, folder_pdfs in folders.items():
                print(f"   📂 {folder}: {len(folder_pdfs)} PDFs")
                for pdf in folder_pdfs[:3]:  # Mostra apenas os 3 primeiros
                    size = os.path.getsize(pdf) / 1024
                    print(f"      📄 {os.path.basename(pdf)} ({size:.1f} KB)")
                if len(folder_pdfs) > 3:
                    print(f"      ... e mais {len(folder_pdfs) - 3} arquivos")
                total_pdfs += len(folder_pdfs)
        
        print(f"\n🎯 TOTAL: {total_pdfs} PDFs encontrados")
        return pdf_locations
    else:
        print("❌ Nenhum PDF encontrado no projeto")
        return {}

def suggest_test_command(pdf_locations):
    """Sugere comandos de teste baseado nos PDFs encontrados"""
    if not pdf_locations:
        return
    
    print(f"\n💡 SUGESTÕES DE TESTE:")
    print("="*50)
    
    for location, pdfs in pdf_locations.items():
        # Agrupa por pasta
        folders = {}
        for pdf in pdfs:
            folder = os.path.dirname(pdf)
            parent_folder = os.path.basename(folder)
            if parent_folder not in folders:
                folders[parent_folder] = folder
        
        for folder_name, folder_path in folders.items():
            if folder_name and folder_name != ".":
                relative_path = os.path.relpath(os.path.dirname(folder_path), ".")
                print(f"📁 Para testar pasta '{folder_name}':")
                print(f"   $env:CURRENT_PROJECT='{folder_name}'")
                print(f"   $env:PDF_BASE_PATH='{relative_path}'")
                print(f"   $env:RESULTS_BASE_PATH='../resultados'")
                print(f"   C:\\Users\\Maoki\\.virtualenvs\\Projetos-5b04BKsC\\Scripts\\python.exe extracao_openai_vision.py")
                print()

if __name__ == "__main__":
    pdf_locations = find_pdfs()
    suggest_test_command(pdf_locations)
