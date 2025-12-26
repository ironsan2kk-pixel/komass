@echo off
chcp 65001 >nul
title Komas - Test Database

echo ============================================================
echo   KOMAS TRADING SERVER - Database Test
echo ============================================================
echo.

cd /d "%~dp0"
cd backend

echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Run install_core.bat first
    pause
    exit /b 1
)

echo.
echo Running database tests...
echo.

python -m app.core.test_database

echo.
if errorlevel 1 (
    echo ============================================================
    echo   TEST FAILED!
    echo ============================================================
) else (
    echo ============================================================
    echo   Database location: data\komas.db
    echo ============================================================
)

echo.
pause
