@echo off
chcp 65001 >nul
echo ========================================
echo  KOMAS Chat #18 Hotfix: Error Handling
echo ========================================
echo.

if not exist "frontend\src\pages\Indicator.jsx" (
    echo [ERROR] Run from komas_indicator root directory!
    pause
    exit /b 1
)

echo [1/2] Backing up current file...
copy "frontend\src\pages\Indicator.jsx" "frontend\src\pages\Indicator.jsx.bak" >nul
echo [OK] Backup created

echo [2/2] Installing fixed Indicator.jsx...
copy /Y "Indicator.jsx" "frontend\src\pages\Indicator.jsx" >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy file
    pause
    exit /b 1
)

echo [OK] Indicator.jsx updated
echo.
echo ========================================
echo  Hotfix applied successfully!
echo  Fixed: Cannot read properties of undefined
echo ========================================
echo.
pause
