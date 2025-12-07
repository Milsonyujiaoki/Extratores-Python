"""
Script para executar ambos extratores (Direto e OCR) de forma paralela ou sequencial.
Inclui análise de recursos e recomendações de execução.
"""

import logging
import time
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import subprocess
import sys
from typing import Dict, Any, Tuple
from dataclasses import dataclass
import threading

# Configuração de log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemAnalysis:
    """Análise completa do sistema para execução paralela"""
    total_memory_gb: float
    available_memory_gb: float
    cpu_count: int
    cpu_percent: float
    disk_io: Dict[str, float]
    can_run_parallel: bool
    recommended_mode: str
    reasons: list
    
    @classmethod
    def analyze_system(cls, file_size_mb: float) -> 'SystemAnalysis':
        """Analisa sistema e recomenda modo de execução"""
        
        # Coleta métricas do sistema
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        try:
            disk_io = psutil.disk_io_counters()._asdict()
        except:
            disk_io = {}
        
        total_memory_gb = memory.total / (1024**3)
        available_memory_gb = memory.available / (1024**3)
        cpu_count = psutil.cpu_count()
        
        # Análise de viabilidade
        reasons = []
        can_run_parallel = True
        
        # Critério 1: Memória disponível
        memory_needed_gb = (file_size_mb / 1024) * 4  # Estima 4x o tamanho do arquivo
        if available_memory_gb < memory_needed_gb * 2:  # Precisa de 2x para execução paralela
            can_run_parallel = False
            reasons.append(f"Memória insuficiente: {available_memory_gb:.1f}GB disponível, {memory_needed_gb*2:.1f}GB necessário")
        
        # Critério 2: CPU
        if cpu_percent > 80:
            can_run_parallel = False
            reasons.append(f"CPU muito ocupada: {cpu_percent:.1f}%")
        
        # Critério 3: Arquivo muito grande
        if file_size_mb > 500:
            can_run_parallel = False
            reasons.append(f"Arquivo muito grande: {file_size_mb:.1f}MB")
        
        # Critério 4: Pouca memória total
        if total_memory_gb < 8:
            can_run_parallel = False
            reasons.append(f"Sistema com pouca memória: {total_memory_gb:.1f}GB total")
        
        # Recomendação final
        if can_run_parallel:
            if available_memory_gb >= 16 and cpu_count >= 8:
                recommended_mode = "parallel_processes"
                reasons.append("Sistema robusto: recomenda execução em processos paralelos")
            elif available_memory_gb >= 8 and cpu_count >= 4:
                recommended_mode = "parallel_threads"
                reasons.append("Sistema adequado: recomenda execução em threads paralelas")
            else:
                recommended_mode = "sequential_optimized"
                reasons.append("Sistema básico: recomenda execução sequencial otimizada")
        else:
            recommended_mode = "sequential_safe"
            reasons.append("Execução sequencial recomendada por limitações de recursos")
        
        return cls(
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            cpu_count=cpu_count,
            cpu_percent=cpu_percent,
            disk_io=disk_io,
            can_run_parallel=can_run_parallel,
            recommended_mode=recommended_mode,
            reasons=reasons
        )

class ResourceMonitor:
    """Monitor de recursos durante execução"""
    
    def __init__(self):
        self.monitoring = False
        self.max_memory_usage = 0
        self.max_cpu_usage = 0
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Inicia monitoramento de recursos"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitor de recursos iniciado")
    
    def stop_monitoring(self):
        """Para monitoramento de recursos"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info(f"Monitor finalizado - Pico memória: {self.max_memory_usage:.1f}%, Pico CPU: {self.max_cpu_usage:.1f}%")
    
    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self.monitoring:
            try:
                # Monitora recursos
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent()
                
                memory_percent = (memory.total - memory.available) / memory.total * 100
                
                self.max_memory_usage = max(self.max_memory_usage, memory_percent)
                self.max_cpu_usage = max(self.max_cpu_usage, cpu)
                
                # Alerta se crítico
                if memory_percent > 85:
                    logger.warning(f"⚠️ Memória crítica: {memory_percent:.1f}%")
                if cpu > 90:
                    logger.warning(f"⚠️ CPU crítica: {cpu:.1f}%")
                
                time.sleep(2)  # Monitora a cada 2 segundos
            except:
                break

class ParallelExtractorOrchestrator:
    """Orquestrador para execução de extratores"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.script_dir = config_file.parent
        self.monitor = ResourceMonitor()
        
    def get_file_size(self) -> float:
        """Obtém tamanho do arquivo PDF do config"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            pdf_path = Path(config['Paths']['PDF_PATH'])
            return pdf_path.stat().st_size / (1024 * 1024)  # MB
        except Exception as e:
            logger.warning(f"Erro ao obter tamanho do arquivo: {e}")
            return 100  # Fallback
    
    def run_direct_extractor(self) -> Tuple[bool, str, float]:
        """Executa extrator direto otimizado"""
        logger.info("🔹 Iniciando extrator direto...")
        start_time = time.time()
        
        try:
            script_path = self.script_dir / "pdf_extractor_direct_optimized.py"
            
            # Executa o script
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, encoding='utf-8')
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Extrator direto concluído em {execution_time:.1f}s")
                return True, result.stdout, execution_time
            else:
                logger.error(f"❌ Extrator direto falhou: {result.stderr}")
                return False, result.stderr, execution_time
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"💥 Erro no extrator direto: {e}")
            return False, str(e), execution_time
    
    def run_ocr_extractor(self) -> Tuple[bool, str, float]:
        """Executa extrator OCR otimizado"""
        logger.info("🔹 Iniciando extrator OCR...")
        start_time = time.time()
        
        try:
            script_path = self.script_dir / "pdf_extractor_ocr_optimized.py"
            
            # Executa o script
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, encoding='utf-8')
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Extrator OCR concluído em {execution_time:.1f}s")
                return True, result.stdout, execution_time
            else:
                logger.error(f"❌ Extrator OCR falhou: {result.stderr}")
                return False, result.stderr, execution_time
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"💥 Erro no extrator OCR: {e}")
            return False, str(e), execution_time
    
    def run_sequential(self) -> Dict[str, Any]:
        """Executa extratores sequencialmente"""
        logger.info("🔄 === EXECUÇÃO SEQUENCIAL ===")
        
        self.monitor.start_monitoring()
        start_time = time.time()
        
        results = {
            'mode': 'sequential',
            'start_time': start_time,
            'direct': None,
            'ocr': None,
            'total_time': 0,
            'success_count': 0
        }
        
        try:
            # Executa direto primeiro
            direct_success, direct_output, direct_time = self.run_direct_extractor()
            results['direct'] = {
                'success': direct_success,
                'output': direct_output,
                'execution_time': direct_time
            }
            if direct_success:
                results['success_count'] += 1
            
            # Pequena pausa entre execuções
            time.sleep(2)
            
            # Executa OCR
            ocr_success, ocr_output, ocr_time = self.run_ocr_extractor()
            results['ocr'] = {
                'success': ocr_success,
                'output': ocr_output,
                'execution_time': ocr_time
            }
            if ocr_success:
                results['success_count'] += 1
            
        finally:
            results['total_time'] = time.time() - start_time
            self.monitor.stop_monitoring()
        
        return results
    
    def run_parallel_threads(self) -> Dict[str, Any]:
        """Executa extratores em threads paralelas"""
        logger.info("🔀 === EXECUÇÃO PARALELA (THREADS) ===")
        
        self.monitor.start_monitoring()
        start_time = time.time()
        
        results = {
            'mode': 'parallel_threads',
            'start_time': start_time,
            'direct': None,
            'ocr': None,
            'total_time': 0,
            'success_count': 0
        }
        
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submete ambos os trabalhos
                direct_future = executor.submit(self.run_direct_extractor)
                ocr_future = executor.submit(self.run_ocr_extractor)
                
                # Aguarda resultados
                for future in as_completed([direct_future, ocr_future]):
                    if future == direct_future:
                        direct_success, direct_output, direct_time = future.result()
                        results['direct'] = {
                            'success': direct_success,
                            'output': direct_output,
                            'execution_time': direct_time
                        }
                        if direct_success:
                            results['success_count'] += 1
                    else:
                        ocr_success, ocr_output, ocr_time = future.result()
                        results['ocr'] = {
                            'success': ocr_success,
                            'output': ocr_output,
                            'execution_time': ocr_time
                        }
                        if ocr_success:
                            results['success_count'] += 1
        
        finally:
            results['total_time'] = time.time() - start_time
            self.monitor.stop_monitoring()
        
        return results
    
    def run_parallel_processes(self) -> Dict[str, Any]:
        """Executa extratores em processos paralelos"""
        logger.info("⚡ === EXECUÇÃO PARALELA (PROCESSOS) ===")
        
        self.monitor.start_monitoring()
        start_time = time.time()
        
        results = {
            'mode': 'parallel_processes',
            'start_time': start_time,
            'direct': None,
            'ocr': None,
            'total_time': 0,
            'success_count': 0
        }
        
        try:
            with ProcessPoolExecutor(max_workers=2) as executor:
                # Submete ambos os trabalhos
                direct_future = executor.submit(self.run_direct_extractor)
                ocr_future = executor.submit(self.run_ocr_extractor)
                
                # Aguarda resultados
                for future in as_completed([direct_future, ocr_future]):
                    if future == direct_future:
                        direct_success, direct_output, direct_time = future.result()
                        results['direct'] = {
                            'success': direct_success,
                            'output': direct_output,
                            'execution_time': direct_time
                        }
                        if direct_success:
                            results['success_count'] += 1
                    else:
                        ocr_success, ocr_output, ocr_time = future.result()
                        results['ocr'] = {
                            'success': ocr_success,
                            'output': ocr_output,
                            'execution_time': ocr_time
                        }
                        if ocr_success:
                            results['success_count'] += 1
        
        finally:
            results['total_time'] = time.time() - start_time
            self.monitor.stop_monitoring()
        
        return results
    
    def print_results_summary(self, results: Dict[str, Any]):
        """Imprime resumo dos resultados"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESUMO DA EXECUÇÃO - Modo: {results['mode'].upper()}")
        logger.info(f"{'='*60}")
        
        # Tempo total
        logger.info(f"⏱️ Tempo total: {results['total_time']:.1f} segundos ({results['total_time']/60:.1f} minutos)")
        logger.info(f"✅ Sucessos: {results['success_count']}/2")
        
        # Resultados do extrator direto
        if results['direct']:
            direct = results['direct']
            status = "✅" if direct['success'] else "❌"
            logger.info(f"{status} Extrator Direto: {direct['execution_time']:.1f}s")
        
        # Resultados do extrator OCR
        if results['ocr']:
            ocr = results['ocr']
            status = "✅" if ocr['success'] else "❌"
            logger.info(f"{status} Extrator OCR: {ocr['execution_time']:.1f}s")
        
        # Recursos utilizados
        logger.info(f"🖥️ Pico de Memória: {self.monitor.max_memory_usage:.1f}%")
        logger.info(f"⚡ Pico de CPU: {self.monitor.max_cpu_usage:.1f}%")

def main():
    """Função principal do orquestrador"""
    logger.info("🚀 === ORQUESTRADOR DE EXTRATORES PDF ===")
    
    # Configuração
    script_dir = Path(__file__).parent
    config_file = script_dir / 'config.ini'
    
    if not config_file.exists():
        logger.error(f"❌ Arquivo config.ini não encontrado: {config_file}")
        return
    
    # Inicializa orquestrador
    orchestrator = ParallelExtractorOrchestrator(config_file)
    
    # Análise do sistema
    file_size_mb = orchestrator.get_file_size()
    analysis = SystemAnalysis.analyze_system(file_size_mb)
    
    logger.info(f"\n{'='*60}")
    logger.info("📋 ANÁLISE DO SISTEMA")
    logger.info(f"{'='*60}")
    logger.info(f"💾 Memória: {analysis.available_memory_gb:.1f}GB disponível / {analysis.total_memory_gb:.1f}GB total")
    logger.info(f"⚡ CPU: {analysis.cpu_count} cores, {analysis.cpu_percent:.1f}% uso atual")
    logger.info(f"📄 Arquivo PDF: {file_size_mb:.1f} MB")
    logger.info(f"🤖 Execução paralela possível: {'✅ Sim' if analysis.can_run_parallel else '❌ Não'}")
    logger.info(f"💡 Modo recomendado: {analysis.recommended_mode}")
    
    for reason in analysis.reasons:
        logger.info(f"   • {reason}")
    
    # Menu de escolha
    logger.info(f"\n{'='*60}")
    logger.info("🎛️ ESCOLHA O MODO DE EXECUÇÃO:")
    logger.info("1. Seguir recomendação do sistema")
    logger.info("2. Execução sequencial (segura)")
    logger.info("3. Execução paralela com threads")
    logger.info("4. Execução paralela com processos")
    logger.info("5. Cancelar")
    
    try:
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == "1":
            mode = analysis.recommended_mode
        elif choice == "2":
            mode = "sequential_safe"
        elif choice == "3":
            mode = "parallel_threads"
        elif choice == "4":
            mode = "parallel_processes"
        elif choice == "5":
            logger.info("❌ Operação cancelada pelo usuário")
            return
        else:
            logger.error("❌ Opção inválida")
            return
        
        # Executa conforme escolha
        logger.info(f"\n🎯 Executando em modo: {mode}")
        
        if mode in ["sequential_safe", "sequential_optimized"]:
            results = orchestrator.run_sequential()
        elif mode == "parallel_threads":
            results = orchestrator.run_parallel_threads()
        elif mode == "parallel_processes":
            results = orchestrator.run_parallel_processes()
        
        # Mostra resultados
        orchestrator.print_results_summary(results)
        
    except KeyboardInterrupt:
        logger.warning("⏹️ Operação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro crítico: {e}")

if __name__ == "__main__":
    main()