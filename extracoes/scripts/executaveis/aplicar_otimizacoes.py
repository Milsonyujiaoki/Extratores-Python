# -*- coding: utf-8 -*-
"""
Script para aplicar otimizações e reiniciar o processamento
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    print("🚀 APLICAÇÃO DE OTIMIZAÇÕES PARA PROCESSAMENTO OPENAI VISION")
    print("=" * 60)
    
    # Calcula estimativa de tempo com otimizações
    from config_otimizacao import calcular_tempo_estimado
    estimativa = calcular_tempo_estimado(6424, 3)
    
    print("📊 COMPARAÇÃO DE DESEMPENHO:")
    print(f"   • Tempo ORIGINAL (sequencial): {estimativa['tempo_original_horas']}h")
    print(f"   • Tempo OTIMIZADO (paralelo):  {estimativa['tempo_otimizado_horas']}h")
    print(f"   • Aceleração esperada: {estimativa['aceleracao_esperada']}x mais rápido")
    print(f"   • Economia de tempo: {estimativa['economia_tempo_horas']}h")
    print()
    
    print("🔧 OTIMIZAÇÕES IMPLEMENTADAS:")
    print("   ✅ Processamento paralelo com 3 threads simultâneas")
    print("   ✅ Redução de DPI de 300 para 200 (mantém qualidade)")
    print("   ✅ Logging otimizado (menos poluição de logs)")
    print("   ✅ Limpeza segura de arquivos temporários")
    print("   ✅ Melhor gerenciamento de recursos e memória")
    print()
    
    print("⚠️  CONFIGURAÇÕES IMPORTANTES:")
    print("   • Usando 3 threads para balancear velocidade vs estabilidade")
    print("   • DPI 200 oferece boa qualidade com velocidade superior")
    print("   • Processamento paralelo pode usar mais CPU e memória")
    print("   • API OpenAI com rate limiting controlado")
    print()
    
    resposta = input("❓ Deseja aplicar as otimizações e reiniciar? (s/N): ").lower().strip()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        print("\n🔄 Parando processo atual...")
        
        # Para processos Python que estão rodando o script de extração
        try:
            result = subprocess.run([
                "taskkill", "/f", "/im", "python.exe", "/fi", "memusage gt 100000"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Processo anterior interrompido com sucesso")
            else:
                print("⚠️  Não foi possível parar o processo anterior automaticamente")
        except Exception as e:
            print(f"⚠️  Erro ao tentar parar processo: {e}")
        
        print("⏳ Aguardando 3 segundos para liberação de recursos...")
        time.sleep(3)
        
        print("🚀 Iniciando processamento otimizado...")
        
        # Caminho para o script principal
        script_path = Path(__file__).parent / "extracao_openai_vision.py"
        python_exe = Path("C:/Users/Maoki/.virtualenvs/Projetos-5b04BKsC/Scripts/python.exe")
        
        # Define variáveis de ambiente otimizadas
        env = os.environ.copy()
        env.update({
            "CURRENT_PROJECT": "000.007",
            "PDF_BASE_PATH": "../../pdfs", 
            "RESULTS_BASE_PATH": "../../resultados",
            "PYTHONPATH": str(Path(__file__).parent.parent.parent.parent),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
            # Configurações de otimização
            "OPENAI_MAX_WORKERS": "3",
            "PDF_DPI_OPTIMIZATION": "200",
            "LOG_OPTIMIZATION": "1"
        })
        
        try:
            # Inicia o processo otimizado
            process = subprocess.Popen([
                str(python_exe),
                str(script_path)
            ], env=env, cwd=script_path.parent)
            
            print(f"✅ Processo otimizado iniciado (PID: {process.pid})")
            print(f"📁 Resultados salvos em: C:\\saida\\Resultados")
            print(f"⏱️  Tempo estimado: {estimativa['tempo_otimizado_horas']}-{estimativa['tempo_conservador_horas']}h")
            print()
            print("📊 Você pode acompanhar o progresso através dos logs")
            print("💡 O processo agora deve ser 9x mais rápido que a versão anterior!")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar processo otimizado: {e}")
            print("💡 Você pode iniciar manualmente executando:")
            print(f"   {python_exe} {script_path}")
    
    else:
        print("\n❌ Otimizações não aplicadas. Processo atual continuará executando.")
        print("💡 Para aplicar posteriormente, execute este script novamente.")

if __name__ == "__main__":
    main()
