@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS Backend v3.5 - Starting
echo ========================================
echo.

cd /d "%~dp0backend"

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting FastAPI on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
