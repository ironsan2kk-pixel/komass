@echo off
echo ========================================
echo Generate Dominant Presets
echo ========================================
echo.

cd /d "%~dp0"
cd ..

if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

call backend\venv\Scripts\activate.bat
set PYTHONPATH=%CD%\backend

echo Running generator...
python "%~dp0generate_dominant_presets.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Generation completed with errors
) else (
    echo.
    echo Generation completed successfully!
)

pause
