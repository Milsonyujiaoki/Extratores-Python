"""
Script de análise de desempenho e comparação entre extratores.
Gera relatórios detalhados e métricas de performance.
"""

import json
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import logging

# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analisador de performance dos extratores"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.results_file = self.output_dir / "performance_results.json"
        self.reports_dir = self.output_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def save_execution_results(self, results: Dict[str, Any], test_name: str = None):
        """Salva resultados de execução"""
        
        # Prepara dados para salvamento
        execution_data = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name or f"test_{int(time.time())}",
            'mode': results.get('mode', 'unknown'),
            'total_time': results.get('total_time', 0),
            'success_count': results.get('success_count', 0),
            'system_info': self._get_system_info(),
            'extractors': {}
        }
        
        # Dados do extrator direto
        if results.get('direct'):
            execution_data['extractors']['direct'] = results['direct']
        
        # Dados do extrator OCR
        if results.get('ocr'):
            execution_data['extractors']['ocr'] = results['ocr']
        
        # Carrega resultados existentes
        existing_results = []
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
            except:
                existing_results = []
        
        # Adiciona novo resultado
        existing_results.append(execution_data)
        
        # Salva resultados atualizados
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Resultados salvos em: {self.results_file}")
        
        return execution_data
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Coleta informações do sistema"""
        memory = psutil.virtual_memory()
        
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total_gb': memory.total / (1024**3),
            'memory_available_gb': memory.available / (1024**3),
            'platform': f"{psutil.WINDOWS} {psutil.LINUX} {psutil.MACOS}".strip()
        }
    
    def load_results(self) -> List[Dict[str, Any]]:
        """Carrega todos os resultados salvos"""
        if not self.results_file.exists():
            return []
        
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar resultados: {e}")
            return []
    
    def generate_comparison_report(self):
        """Gera relatório de comparação entre métodos"""
        results = self.load_results()
        if not results:
            logger.warning("Nenhum resultado encontrado para análise")
            return
        
        # Agrupa por modo de execução
        modes = {}
        for result in results:
            mode = result['mode']
            if mode not in modes:
                modes[mode] = []
            modes[mode].append(result)
        
        # Gera relatório
        report_file = self.reports_dir / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Relatório de Comparação de Performance - Extratores PDF\n\n")
            f.write(f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n")
            
            # Resumo geral
            f.write("## 📊 Resumo Geral\n\n")
            f.write(f"- **Total de execuções:** {len(results)}\n")
            f.write(f"- **Modos testados:** {', '.join(modes.keys())}\n")
            f.write(f"- **Período:** {results[0]['timestamp'][:10]} a {results[-1]['timestamp'][:10]}\n\n")
            
            # Análise por modo
            for mode, executions in modes.items():
                f.write(f"## 🔍 Análise - Modo: {mode.upper()}\n\n")
                f.write(f"**Execuções:** {len(executions)}\n\n")
                
                # Estatísticas de tempo
                times = [exec['total_time'] for exec in executions]
                if times:
                    f.write("### ⏱️ Tempos de Execução\n\n")
                    f.write(f"- **Tempo médio:** {sum(times)/len(times):.1f}s\n")
                    f.write(f"- **Tempo mínimo:** {min(times):.1f}s\n")
                    f.write(f"- **Tempo máximo:** {max(times):.1f}s\n\n")
                
                # Taxa de sucesso
                success_rates = [exec['success_count'] for exec in executions]
                if success_rates:
                    avg_success = sum(success_rates) / len(success_rates)
                    f.write(f"- **Taxa de sucesso média:** {avg_success:.1f}/2 ({avg_success/2*100:.0f}%)\n\n")
                
                # Análise por extrator
                direct_times = []
                ocr_times = []
                
                for exec in executions:
                    if exec.get('extractors', {}).get('direct', {}).get('success'):
                        direct_times.append(exec['extractors']['direct']['execution_time'])
                    if exec.get('extractors', {}).get('ocr', {}).get('success'):
                        ocr_times.append(exec['extractors']['ocr']['execution_time'])
                
                if direct_times:
                    f.write("### 🔹 Extrator Direto\n")
                    f.write(f"- **Execuções bem-sucedidas:** {len(direct_times)}\n")
                    f.write(f"- **Tempo médio:** {sum(direct_times)/len(direct_times):.1f}s\n")
                    f.write(f"- **Melhor tempo:** {min(direct_times):.1f}s\n\n")
                
                if ocr_times:
                    f.write("### 🔹 Extrator OCR\n")
                    f.write(f"- **Execuções bem-sucedidas:** {len(ocr_times)}\n")
                    f.write(f"- **Tempo médio:** {sum(ocr_times)/len(ocr_times):.1f}s\n")
                    f.write(f"- **Melhor tempo:** {min(ocr_times):.1f}s\n\n")
                
                f.write("---\n\n")
            
            # Recomendações
            f.write("## 💡 Recomendações\n\n")
            
            # Encontra o modo mais eficiente
            mode_efficiency = {}
            for mode, executions in modes.items():
                if executions:
                    avg_time = sum(exec['total_time'] for exec in executions) / len(executions)
                    avg_success = sum(exec['success_count'] for exec in executions) / len(executions)
                    efficiency = avg_success / avg_time if avg_time > 0 else 0
                    mode_efficiency[mode] = {
                        'avg_time': avg_time,
                        'avg_success': avg_success,
                        'efficiency': efficiency
                    }
            
            if mode_efficiency:
                best_mode = max(mode_efficiency.keys(), key=lambda x: mode_efficiency[x]['efficiency'])
                f.write(f"### 🏆 Modo Mais Eficiente: **{best_mode.upper()}**\n\n")
                f.write(f"- **Tempo médio:** {mode_efficiency[best_mode]['avg_time']:.1f}s\n")
                f.write(f"- **Taxa de sucesso:** {mode_efficiency[best_mode]['avg_success']:.1f}/2\n")
                f.write(f"- **Índice de eficiência:** {mode_efficiency[best_mode]['efficiency']:.3f}\n\n")
            
            # Recomendações específicas
            f.write("### 📋 Diretrizes de Uso\n\n")
            
            for mode, stats in mode_efficiency.items():
                if mode == "sequential_safe":
                    f.write(f"- **{mode}:** Recomendado para sistemas com limitações de memória (< 8GB) ou arquivos > 500MB\n")
                elif mode == "parallel_threads":
                    f.write(f"- **{mode}:** Ideal para sistemas intermediários (8-16GB RAM, 4-8 cores)\n")
                elif mode == "parallel_processes":
                    f.write(f"- **{mode}:** Melhor para sistemas robustos (> 16GB RAM, > 8 cores)\n")
            
            f.write("\n---\n\n")
            f.write("*Relatório gerado automaticamente pelo PerformanceAnalyzer*\n")
        
        logger.info(f"📄 Relatório gerado: {report_file}")
        return report_file
    
    def generate_performance_chart(self):
        """Gera gráfico de performance"""
        results = self.load_results()
        if len(results) < 2:
            logger.warning("Poucos dados para gerar gráfico")
            return
        
        try:
            # Prepara dados
            data = []
            for result in results:
                data.append({
                    'timestamp': result['timestamp'],
                    'mode': result['mode'],
                    'total_time': result['total_time'],
                    'success_count': result['success_count'],
                    'direct_time': result.get('extractors', {}).get('direct', {}).get('execution_time', 0),
                    'ocr_time': result.get('extractors', {}).get('ocr', {}).get('execution_time', 0)
                })
            
            df = pd.DataFrame(data)
            
            # Cria gráfico
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Análise de Performance - Extratores PDF', fontsize=16)
            
            # Gráfico 1: Tempo total por modo
            mode_times = df.groupby('mode')['total_time'].mean()
            axes[0, 0].bar(mode_times.index, mode_times.values)
            axes[0, 0].set_title('Tempo Médio por Modo')
            axes[0, 0].set_ylabel('Tempo (segundos)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Gráfico 2: Taxa de sucesso por modo
            mode_success = df.groupby('mode')['success_count'].mean()
            axes[0, 1].bar(mode_success.index, mode_success.values)
            axes[0, 1].set_title('Taxa de Sucesso por Modo')
            axes[0, 1].set_ylabel('Sucessos (de 2)')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Gráfico 3: Comparação de tempo entre extratores
            extractor_times = df[['direct_time', 'ocr_time']].mean()
            axes[1, 0].bar(['Direto', 'OCR'], extractor_times.values)
            axes[1, 0].set_title('Tempo Médio por Extrator')
            axes[1, 0].set_ylabel('Tempo (segundos)')
            
            # Gráfico 4: Timeline de execuções
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            for mode in df['mode'].unique():
                mode_data = df[df['mode'] == mode]
                axes[1, 1].plot(mode_data['timestamp'], mode_data['total_time'], 
                               marker='o', label=mode)
            
            axes[1, 1].set_title('Timeline de Execuções')
            axes[1, 1].set_ylabel('Tempo (segundos)')
            axes[1, 1].legend()
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Salva gráfico
            chart_file = self.reports_dir / f"performance_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Gráfico gerado: {chart_file}")
            return chart_file
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico: {e}")
            return None
    
    def get_quick_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas rápidas"""
        results = self.load_results()
        if not results:
            return {'message': 'Nenhum dado disponível'}
        
        total_executions = len(results)
        successful_executions = sum(1 for r in results if r['success_count'] == 2)
        
        # Tempo médio por modo
        modes = {}
        for result in results:
            mode = result['mode']
            if mode not in modes:
                modes[mode] = []
            modes[mode].append(result['total_time'])
        
        mode_stats = {mode: sum(times)/len(times) for mode, times in modes.items()}
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions * 100,
            'average_times_by_mode': mode_stats,
            'fastest_mode': min(mode_stats.keys(), key=lambda x: mode_stats[x]) if mode_stats else None,
            'last_execution': results[-1]['timestamp'] if results else None
        }

def main():
    """Função principal para teste do analisador"""
    
    # Configuração
    script_dir = Path(__file__).parent
    output_dir = script_dir / 'performance_analysis'
    
    analyzer = PerformanceAnalyzer(output_dir)
    
    # Menu de opções
    logger.info("🔍 === ANALISADOR DE PERFORMANCE ===")
    logger.info("1. Ver estatísticas rápidas")
    logger.info("2. Gerar relatório de comparação")
    logger.info("3. Gerar gráfico de performance")
    logger.info("4. Executar análise completa")
    logger.info("5. Sair")
    
    try:
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == "1":
            stats = analyzer.get_quick_stats()
            logger.info("\n📊 ESTATÍSTICAS RÁPIDAS:")
            for key, value in stats.items():
                logger.info(f"   {key}: {value}")
        
        elif choice == "2":
            analyzer.generate_comparison_report()
        
        elif choice == "3":
            analyzer.generate_performance_chart()
        
        elif choice == "4":
            logger.info("🔄 Executando análise completa...")
            analyzer.generate_comparison_report()
            analyzer.generate_performance_chart()
            stats = analyzer.get_quick_stats()
            logger.info("\n📊 ESTATÍSTICAS FINAIS:")
            for key, value in stats.items():
                logger.info(f"   {key}: {value}")
        
        elif choice == "5":
            logger.info("👋 Saindo...")
        
        else:
            logger.error("❌ Opção inválida")
    
    except KeyboardInterrupt:
        logger.warning("⏹️ Operação interrompida")
    except Exception as e:
        logger.error(f"💥 Erro: {e}")

if __name__ == "__main__":
    main()