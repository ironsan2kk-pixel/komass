@echo off
echo ========================================
echo KOMAS - Database Migration
echo ========================================
echo.
echo This will:
echo  1. Drop old presets table
echo  2. Create new table with correct schema
echo  3. Seed 125+ Dominant presets
echo.
echo WARNING: Existing presets will be deleted!
echo.
pause

cd /d "%~dp0"
cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONPATH=%CD%;%CD%\app

echo.
echo Running migration...
echo.

python "%~dp0migrate_presets_table.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Migration failed!
    pause
    exit /b 1
)

echo.
pause
