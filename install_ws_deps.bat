@echo off
echo ========================================
echo Komas WebSocket Dependencies Installer
echo ========================================
echo.

cd /d %~dp0

echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

echo.
echo Installing WebSocket dependencies...
pip install websockets>=12.0 --break-system-packages

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo WebSocket dependencies installed!
echo ========================================
echo.
echo New features available:
echo   - Real-time price streaming
echo   - SSE endpoints for frontend
echo   - Auto-reconnect WebSocket client
echo.
echo API Endpoints:
echo   GET  /api/ws/status           - Connection status
echo   POST /api/ws/connect          - Connect to Binance
echo   POST /api/ws/subscribe        - Subscribe to streams
echo   GET  /api/ws/sse/prices       - SSE price updates
echo   GET  /api/ws/sse/klines       - SSE kline updates
echo.
pause
