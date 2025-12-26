@echo off
chcp 65001 >nul
echo ============================================
echo  KOMAS TELEGRAM - RUNNING TESTS
echo ============================================
echo.

cd backend
call venv\Scripts\activate
cd ..

echo Running notification tests...
python -m pytest tests/test_notifications.py -v --tb=short

echo.
echo ============================================
echo  TESTS COMPLETE
echo ============================================
pause
