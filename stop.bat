@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS Frontend v3.5 - Stopping
echo ========================================
echo.

echo Stopping Node.js processes...
taskkill /F /IM node.exe >nul 2>&1

echo Done.
timeout /t 2 >nul
