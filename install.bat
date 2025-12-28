@echo off
echo ========================================
echo HOTFIX v2: Optimizer DB path + closure fix
echo ========================================
echo.

cd /d "%~dp0"

echo Copying fixed optimizer_routes.py...
copy /y "patch\backend\app\api\optimizer_routes.py" "backend\app\api\optimizer_routes.py"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy file
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Fixed:
echo  - NameError: closure bug with 'e' variable
echo  - Database path: now correctly points to data/komas.db
echo  - Friendly error messages in Russian
echo.
echo Restart backend: stop.bat, start.bat
echo.
pause
