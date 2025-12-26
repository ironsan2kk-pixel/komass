@echo off
echo ============================================
echo TRG OPTIMIZER - Install Dependencies
echo ============================================
echo.

cd /d "%~dp0"

echo Installing required packages...
echo.

pip install numpy pandas --break-system-packages

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo Dependencies installed successfully!
    echo.
    echo Now run: test_optimizer.bat
    echo ============================================
) else (
    echo.
    echo ============================================
    echo Installation failed! Try running as Admin
    echo or use: pip install numpy pandas
    echo ============================================
)

pause
