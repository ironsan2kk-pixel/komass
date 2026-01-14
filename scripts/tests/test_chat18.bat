@echo off
chcp 65001 >nul
echo ========================================
echo  KOMAS Chat #18: Testing Data Period
echo ========================================
echo.

REM Check if server is running
echo [1/4] Checking if server is running...
curl -s -o nul -w "" http://localhost:8000/api/data/symbols
if errorlevel 1 (
    echo [WARN] Server not running. Please start it first.
    echo Run: start.bat
    pause
    exit /b 1
)
echo [OK] Server is running

echo [2/4] Testing /api/indicator/calculate with date range...
curl -s -X POST http://localhost:8000/api/indicator/calculate ^
  -H "Content-Type: application/json" ^
  -d "{\"symbol\":\"BTCUSDT\",\"timeframe\":\"1h\",\"start_date\":\"2024-06-01\",\"end_date\":\"2024-12-31\"}" ^
  > test_response.json 2>&1

if errorlevel 1 (
    echo [ERROR] API call failed
    pause
    exit /b 1
)

echo [3/4] Checking response for data_range...
findstr /C:"data_range" test_response.json >nul
if errorlevel 1 (
    echo [ERROR] data_range not found in response
    echo Response:
    type test_response.json
    pause
    exit /b 1
)
echo [OK] data_range found in response

echo [4/4] Checking data_range fields...
findstr /C:"available_start" test_response.json >nul
if errorlevel 1 (
    echo [ERROR] available_start not found
    pause
    exit /b 1
)
findstr /C:"used_start" test_response.json >nul
if errorlevel 1 (
    echo [ERROR] used_start not found
    pause
    exit /b 1
)
echo [OK] All data_range fields present

echo.
echo ========================================
echo  All tests passed!
echo ========================================
echo.

REM Cleanup
del test_response.json 2>nul

pause
