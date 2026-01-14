@echo off
chcp 65001 >nul
echo ===============================================
echo  TRG UI Schema Tests
echo ===============================================
echo.

cd /d "%~dp0"
cd backend\app\plugins\trg

echo [1/5] Checking file...
if not exist ui_schema.py (
    echo ERROR: ui_schema.py not found!
    echo Make sure to extract archive to your project root
    pause
    exit /b 1
)
echo OK: ui_schema.py found
echo.

echo [2/5] Running sections test...
python ui_schema.py sections
echo.

echo [3/5] Running tabs test...
python ui_schema.py tabs
echo.

echo [4/5] Running defaults test...
python ui_schema.py defaults
echo.

echo [5/5] Running validation test...
python ui_schema.py validate
echo.

echo ===============================================
echo  All tests complete!
echo ===============================================
pause
