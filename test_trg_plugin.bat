@echo off
REM ============================================
REM Komas Trading System - Test TRG Plugin
REM ============================================

echo.
echo =============================================
echo    KOMAS TRG PLUGIN - TEST SUITE
echo =============================================
echo.

cd /d "%~dp0"

REM Find the trg plugin directory
set TRG_DIR=

if exist "backend\app\indicators\plugins\trg\tests.py" (
    set TRG_DIR=backend\app\indicators\plugins\trg
) else if exist "app\indicators\plugins\trg\tests.py" (
    set TRG_DIR=app\indicators\plugins\trg
) else if exist "indicators\plugins\trg\tests.py" (
    set TRG_DIR=indicators\plugins\trg
) else if exist "plugins\trg\tests.py" (
    set TRG_DIR=plugins\trg
) else if exist "trg\tests.py" (
    set TRG_DIR=trg
)

if "%TRG_DIR%"=="" (
    echo ERROR: Cannot find TRG plugin directory!
    echo Looking for tests.py in:
    echo   - backend\app\indicators\plugins\trg\
    echo   - app\indicators\plugins\trg\
    echo   - indicators\plugins\trg\
    echo   - plugins\trg\
    echo   - trg\
    pause
    exit /b 1
)

echo Found TRG plugin at: %TRG_DIR%
echo.

REM Activate venv if exists
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Running TRG plugin tests...
echo.

REM Run tests directly from the plugin directory
cd /d "%~dp0%TRG_DIR%"
python tests.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =============================================
    echo    ALL TESTS PASSED!
    echo =============================================
) else (
    echo.
    echo =============================================
    echo    SOME TESTS FAILED
    echo =============================================
)

echo.
pause
