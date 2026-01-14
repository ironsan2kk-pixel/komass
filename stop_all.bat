@echo off
echo ========================================
echo KOMAS - Stopping All Services
echo ========================================
echo.

echo Stopping Python processes...
taskkill /f /im python.exe 2>nul
taskkill /f /im uvicorn.exe 2>nul

echo Stopping Node processes...
taskkill /f /im node.exe 2>nul

echo.
echo All services stopped.
pause
