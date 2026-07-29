@echo off
TITLE DataNexus AI - Control Center & API Launcher
COLOR 0A

echo =========================================================================
echo               DataNexus AI - Enterprise Control Center
echo =========================================================================
echo.

cd /d "%~dp0"

REM 1. Activate Virtual Environment
if exist "venv\Scripts\activate.bat" (
    echo [1/3] Virtuelle Umgebung venv aktivieren...
    call venv\Scripts\activate.bat
) else (
    echo [1/3] Erstelle neue virtuelle Umgebung venv...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [1/3] Installiere Abhaengigkeiten...
    pip install -r requirements.txt
    pip install streamlit fastapi uvicorn httpx
)

REM 2. Start FastAPI Backend in new window with --reload for auto-updates
echo [2/3] Starte FastAPI REST-API Backend Server (Port 8000)...
start "DataNexus API Backend" cmd /k "venv\Scripts\python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

REM 3. Start Streamlit Control Center Web Dashboard
echo [3/3] Starte Streamlit Control Center Web UI (Port 8501)...
echo.
echo Öffne Control Center Dashboard im Browser unter: http://localhost:8501
echo.
venv\Scripts\python.exe -m streamlit run app.py --server.port 8501

pause
