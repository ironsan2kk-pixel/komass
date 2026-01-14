@echo off
echo ========================================
echo KOMAS - Starting Full Application
echo ========================================
echo.

cd /d %~dp0

echo Starting Backend (port 8000)...
start "KOMAS Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo Starting Frontend (port 5173)...
start "KOMAS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Services started:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to open browser...
pause > nul

start http://localhost:5173
