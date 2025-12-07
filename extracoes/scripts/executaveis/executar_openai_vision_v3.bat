@echo off
echo 🔧 CONFIGURANDO AMBIENTE PARA OPENAI VISION
echo ============================================

REM Configura as variáveis de ambiente necessárias
set PATH=C:\Users\Maoki\poppler\poppler-23.11.0\Library\bin;%PATH%
set PDF_BASE_PATH=C:\Marimex - Doc's completos
set RESULTS_BASE_PATH=C:\Marimex - Doc's completos\resultados
set PROCESSADOS_PATH=C:\Marimex - Doc's completos\Processados
set CURRENT_PROJECT=
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
set MODEL_NAME=gpt-4.1-nano
set OPENAI_MAX_RPM=2000
set MAX_CPU=4
set MAX_CONCURRENT_API_CALLS=10
set MAX_PARALLEL_PROJECTS=3

echo ✅ Variáveis de ambiente configuradas:
echo    PDF_BASE_PATH=%PDF_BASE_PATH%
echo    RESULTS_BASE_PATH=%RESULTS_BASE_PATH%
echo    PROCESSADOS_PATH=%PROCESSADOS_PATH%
echo    CURRENT_PROJECT=%CURRENT_PROJECT%
echo    MAX_CPU=%MAX_CPU%
echo    MAX_CONCURRENT_API_CALLS=%MAX_CONCURRENT_API_CALLS%
echo    MAX_PARALLEL_PROJECTS=%MAX_PARALLEL_PROJECTS%
echo    Poppler adicionado ao PATH
echo.

echo 📋 ESCOLHA O MODO DE EXECUÇÃO:
echo    1. Processar projeto específico (definir CURRENT_PROJECT)
echo    2. Processar TODAS as pastas de PDFs (exceto Processados)
echo.

set /p choice="Digite sua escolha (1 ou 2): "

if "%choice%"=="1" (
    set /p project_name="Digite o nome do projeto (ex: 000.007): "
    set CURRENT_PROJECT=%project_name%
    echo � Processando projeto específico: %CURRENT_PROJECT%
) else (
    echo 📂 Processando TODAS as pastas de PDFs
)

echo.
echo �🐍 Executando script OpenAI Vision...
cd /d "%~dp0"
"C:\Users\Maoki\.virtualenvs\Projetos-5b04BKsC\Scripts\python.exe" extracao_openai_vision_v3.py

echo.
echo 🎉 Execução concluída!
echo 📁 Projetos processados foram movidos para a pasta Processados
pause
