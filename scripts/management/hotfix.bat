@echo off
echo ========================================
echo KOMAS Chat #31-33 HOTFIX
echo Fix: API_URL import error in Presets.jsx
echo ========================================
echo.

cd /d "%~dp0"

REM Check if frontend directory exists
if not exist "..\..\..\frontend\src\pages\Presets.jsx" (
    echo ERROR: Presets.jsx not found
    echo Make sure you run this from the extracted archive
    pause
    exit /b 1
)

echo Applying fix to Presets.jsx...
copy /Y "frontend\src\pages\Presets.jsx" "..\..\..\frontend\src\pages\Presets.jsx"

echo.
echo DONE! Restart the frontend to apply changes.
echo.
pause
