@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS - Stopping All Services
echo ========================================
echo.

echo Stopping Backend (Python)...
taskkill /FI "WINDOWTITLE eq KOMAS Backend*" /F >nul 2>&1

echo Stopping Frontend (Node)...
taskkill /FI "WINDOWTITLE eq KOMAS Frontend*" /F >nul 2>&1

echo.
echo Done.
timeout /t 2 >nul
