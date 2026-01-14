@echo off
echo ============================================
echo TRG OPTIMIZER - Test Runner
echo ============================================
echo.

cd /d "%~dp0"
cd backend\app\indicators\plugins\trg

echo Running optimizer tests...
echo.

python test_optimizer.py

echo.
echo ============================================
if %ERRORLEVEL% EQU 0 (
    echo Tests completed successfully!
) else (
    echo Some tests failed!
)
echo ============================================

pause
