"""
ANÁLISE DE QUALIDADE DAS EXTRAÇÕES - AVALIAÇÃO DOS MELHORES SCRIPTS
Este script analisa a qualidade das extrações de texto de diferentes bibliotecas
com foco especial nos arquivos CP (que são mais desafiadores)
"""
import os
import glob
import pandas as pd
from collections import defaultdict

def analyze_extraction_quality():
    """Analisa a qualidade das extrações de todos os scripts"""
    results_path = "../resultados"
    projects = [d for d in os.listdir(results_path) if os.path.isdir(os.path.join(results_path, d))]
    
    analysis_data = []
    script_stats = defaultdict(lambda: {'total_files': 0, 'successful_files': 0, 'total_size': 0, 'cp_files': 0, 'cp_successful': 0, 'cp_total_size': 0})
    
    # Scripts de extração de texto para analisar
    text_scripts = {
        'PyMuPDF': 'PyMuPDF_*.txt',
        'PDFPlumber': 'pdfPlumber_*.txt', 
        'PDFMiner': 'pdfMiner_*.txt',
        'PyPDF2': 'PyPDF2_*.txt',
        'PyMuPDF4LLM': 'pymupdf4llm_*.txt',
        'PDFQuery': 'pdfquery_*.txt'
    }
    
    print("📊 ANÁLISE DE QUALIDADE DAS EXTRAÇÕES")
    print("="*60)
    
    for project in sorted(projects):
        project_path = os.path.join(results_path, project)
        txt_path = os.path.join(project_path, "txt")
        
        if not os.path.exists(txt_path):
            continue
            
        print(f"\n🎯 PROJETO: {project}")
        print("-" * 40)
        
        for script_name, pattern in text_scripts.items():
            files = glob.glob(os.path.join(txt_path, pattern))
            
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                is_cp = '_CP_' in file_name
                is_successful = file_size > 10  # Considera sucesso se > 10 bytes
                
                # Estatísticas gerais
                script_stats[script_name]['total_files'] += 1
                if is_successful:
                    script_stats[script_name]['successful_files'] += 1
                    script_stats[script_name]['total_size'] += file_size
                
                # Estatísticas específicas para arquivos CP
                if is_cp:
                    script_stats[script_name]['cp_files'] += 1
                    if is_successful:
                        script_stats[script_name]['cp_successful'] += 1
                        script_stats[script_name]['cp_total_size'] += file_size
                
                # Dados para análise detalhada
                analysis_data.append({
                    'projeto': project,
                    'script': script_name,
                    'arquivo': file_name,
                    'tamanho': file_size,
                    'is_cp': is_cp,
                    'sucesso': is_successful
                })
                
                status = "✅" if is_successful else "❌"
                cp_marker = "🔴 CP" if is_cp else "📄"
                print(f"  {status} {cp_marker} {script_name}: {file_name} ({file_size} bytes)")
    
    print(f"\n📋 RELATÓRIO CONSOLIDADO DE QUALIDADE")
    print("="*60)
    
    # Ranking por taxa de sucesso geral
    success_ranking = []
    for script, stats in script_stats.items():
        if stats['total_files'] > 0:
            success_rate = (stats['successful_files'] / stats['total_files']) * 100
            avg_size = stats['total_size'] / max(stats['successful_files'], 1)
            
            # Taxa de sucesso específica para arquivos CP
            cp_success_rate = 0
            cp_avg_size = 0
            if stats['cp_files'] > 0:
                cp_success_rate = (stats['cp_successful'] / stats['cp_files']) * 100
                cp_avg_size = stats['cp_total_size'] / max(stats['cp_successful'], 1)
            
            success_ranking.append({
                'script': script,
                'taxa_sucesso_geral': success_rate,
                'tamanho_medio_geral': avg_size,
                'arquivos_cp_total': stats['cp_files'],
                'taxa_sucesso_cp': cp_success_rate,
                'tamanho_medio_cp': cp_avg_size,
                'score_cp': cp_success_rate * (cp_avg_size / 1000)  # Score ponderado
            })
    
    # Ordena por taxa de sucesso em arquivos CP (prioridade) e geral
    success_ranking.sort(key=lambda x: (x['taxa_sucesso_cp'], x['taxa_sucesso_geral']), reverse=True)
    
    print("\n🏆 RANKING DE QUALIDADE (com foco em arquivos CP):")
    print("-" * 60)
    
    for i, data in enumerate(success_ranking, 1):
        print(f"{i}. {data['script']}")
        print(f"   📊 Sucesso Geral: {data['taxa_sucesso_geral']:.1f}% (média: {data['tamanho_medio_geral']:.0f} bytes)")
        print(f"   🔴 Sucesso CP: {data['taxa_sucesso_cp']:.1f}% (média: {data['tamanho_medio_cp']:.0f} bytes)")
        print(f"   📈 Score CP: {data['score_cp']:.1f}")
        print()
    
    # Análise específica dos arquivos CP mais problemáticos
    print("\n🔍 ANÁLISE DE ARQUIVOS CP PROBLEMÁTICOS:")
    print("-" * 60)
    
    df = pd.DataFrame(analysis_data)
    cp_files = df[df['is_cp'] == True]
    
    # Agrupa por projeto e script para ver padrões
    cp_summary = cp_files.groupby(['projeto', 'script']).agg({
        'sucesso': 'sum',
        'tamanho': ['count', 'mean', 'sum']
    }).round(2)
    
    print("📋 RESUMO POR PROJETO (apenas arquivos CP):")
    for project in sorted(df['projeto'].unique()):
        project_cp = cp_files[cp_files['projeto'] == project]
        print(f"\n🎯 {project}:")
        
        for script in sorted(project_cp['script'].unique()):
            script_data = project_cp[project_cp['script'] == script]
            successful = script_data['sucesso'].sum()
            total = len(script_data)
            avg_size = script_data[script_data['sucesso']]['tamanho'].mean() if successful > 0 else 0
            
            status = "✅" if successful == total else "⚠️" if successful > 0 else "❌"
            print(f"  {status} {script}: {successful}/{total} sucessos (média: {avg_size:.0f} bytes)")
    
    # Recomendações finais
    print(f"\n💡 RECOMENDAÇÕES BASEADAS NA ANÁLISE:")
    print("-" * 60)
    
    top_3 = success_ranking[:3]
    print("🏆 TOP 3 SCRIPTS RECOMENDADOS para arquivos CP:")
    for i, script_data in enumerate(top_3, 1):
        if script_data['taxa_sucesso_cp'] > 0:
            print(f"{i}. {script_data['script']} - {script_data['taxa_sucesso_cp']:.1f}% sucesso em CP")
    
    # Scripts mais confiáveis para extrações gerais
    general_ranking = sorted(success_ranking, key=lambda x: x['taxa_sucesso_geral'], reverse=True)
    print(f"\n📊 TOP 3 SCRIPTS para extrações GERAIS:")
    for i, script_data in enumerate(general_ranking[:3], 1):
        print(f"{i}. {script_data['script']} - {script_data['taxa_sucesso_geral']:.1f}% sucesso geral")
    
    return analysis_data, script_stats

if __name__ == "__main__":
    analysis_data, script_stats = analyze_extraction_quality()
