@echo off
setlocal
title ZestyFinance - Analisis Acciones (Bolsa de Santiago Oficial)

:: Asegurar que el directorio de trabajo sea la carpeta del script
cd /d "%~dp0"

echo ================================================================
echo    ZestyFinance - Screener y Analizador de Acciones Chilenas
echo    Fuente de Datos: 100%% Oficial Bolsa de Santiago
echo    Puerto: 8502
echo ================================================================
echo.

:: 1. Detectar comando de Python disponible
set PY_CMD=

:: a. Verificar si existe Python Portable dentro de la carpeta
if exist "%~dp0python_portable\python.exe" (
    set PY_CMD="%~dp0python_portable\python.exe"
    goto :PYTHON_FOUND
)

:: b. Verificar comando python en PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PY_CMD=python
    goto :PYTHON_FOUND
)

:: c. Verificar lanzador py en PATH
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set PY_CMD=py -3
    goto :PYTHON_FOUND
)

:: d. Buscar en instalaciones locales comunes de Windows
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :PYTHON_FOUND
)
if exist "%ProgramFiles%\Python312\python.exe" (
    set PY_CMD="%ProgramFiles%\Python312\python.exe"
    goto :PYTHON_FOUND
)
if exist "%ProgramFiles%\Python311\python.exe" (
    set PY_CMD="%ProgramFiles%\Python311\python.exe"
    goto :PYTHON_FOUND
)

echo [ERROR] No se encontro Python en este equipo.
echo.
echo Para abrir esta aplicacion en cualquier PC se requiere Python:
echo  1. Descargalo gratis desde: https://www.python.org/downloads/
echo  2. IMPORTANTE: Durante la instalacion marca la casilla "[X] Add Python to PATH"
echo  3. Vuelve a hacer doble clic en este archivo run_analisis.bat.
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [*] Python detectado: %PY_CMD%

:: 2. Verificar dependencias requeridas
echo [*] Comprobando librerias del sistema...
%PY_CMD% -c "import streamlit, pandas, plotly, websockets, numpy" >nul 2>&1
if not errorlevel 1 goto :DEPS_OK

echo.
echo [*] Faltan librerias requeridas. Instalando dependencias automaticamente...
echo     (Esto se hace una sola vez y tomara aproximadamente 1 minuto)
echo.
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :INSTALL_ERROR
echo [*] Dependencias instaladas exitosamente.
goto :DEPS_OK

:INSTALL_ERROR
echo.
echo [ERROR] Ocurrio un problema al instalar las dependencias con pip.
echo Verifica tu conexion a internet o ejecuta manualmente en tu terminal:
echo   pip install -r requirements.txt
echo.
pause
exit /b 1

:DEPS_OK
echo [*] Todas las dependencias estan listas.

:: 3. Configurar credenciales silenciosas de Streamlit si es la primera vez
%PY_CMD% -c "from streamlit.web.cli import Credentials; cred = Credentials.get_current(); cred.email = ''; cred.save()" >nul 2>&1

:: 4. Iniciar aplicacion Streamlit
echo.
echo ================================================================
echo    Iniciando servidor en http://localhost:8502 ...
echo    El navegador se abrira automaticamente.
echo    Para cerrar la aplicacion, simplemente cierra esta ventana.
echo ================================================================
echo.

%PY_CMD% -m streamlit run app.py --server.port 8502 --server.showEmailPrompt false --browser.gatherUsageStats false

pause
