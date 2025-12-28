@echo off
echo ========================================
echo KOMAS Chat #49 Fix - Optimizer UI
echo ========================================
echo.

cd /d "%~dp0"

echo Copying fixed Optimizer.jsx...
copy /Y "frontend\src\pages\Optimizer.jsx" "..\frontend\src\pages\Optimizer.jsx"

echo.
echo ========================================
echo Fix installed!
echo ========================================
echo.
echo Please restart frontend: npm run dev
echo.
pause
