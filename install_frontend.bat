@echo off
chcp 65001 > nul
echo ============================================
echo   KOMAS Trading Server v3 - Frontend Setup
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] Проверка Node.js...
where node >nul 2>nul
if errorlevel 1 (
    echo ОШИБКА: Node.js не найден! Установите Node.js 18+
    pause
    exit /b 1
)
node -v

echo.
echo [2/3] Установка зависимостей frontend...
cd frontend
call npm install
if errorlevel 1 (
    echo ОШИБКА: npm install завершился с ошибкой!
    pause
    exit /b 1
)

echo.
echo [3/3] Готово!
echo.
echo Для запуска используйте: npm run dev
echo.
pause
