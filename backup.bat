@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║            KOMAS TRADING SERVER v3.0 - BACKUP                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Create backups directory
if not exist "backups" mkdir backups

:: Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

set BACKUP_DIR=backups\backup_%TIMESTAMP%

echo [1/4] Creating backup directory...
mkdir "%BACKUP_DIR%"
echo       %BACKUP_DIR%

:: Backup data
echo [2/4] Backing up data files...
if exist "data" (
    xcopy /s /e /i /q "data" "%BACKUP_DIR%\data" >nul 2>&1
    echo       Data folder backed up
) else (
    echo       No data folder found
)

:: Backup database
echo [3/4] Backing up database...
if exist "backend\komas.db" (
    copy "backend\komas.db" "%BACKUP_DIR%\komas.db" >nul
    echo       Database backed up
) else (
    echo       No database found
)

:: Backup config
echo [4/4] Backing up configuration...
if exist "backend\.env" (
    copy "backend\.env" "%BACKUP_DIR%\.env" >nul
    echo       Configuration backed up
) else (
    echo       No .env file found
)

if exist "backend\config.json" (
    copy "backend\config.json" "%BACKUP_DIR%\config.json" >nul
    echo       config.json backed up
)

:: Calculate backup size
set SIZE=0
for /r "%BACKUP_DIR%" %%F in (*) do set /a SIZE+=%%~zF
set /a SIZE_KB=%SIZE%/1024
set /a SIZE_MB=%SIZE_KB%/1024

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      BACKUP COMPLETE                          ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Location: %BACKUP_DIR%
echo ║  Size:     %SIZE_KB% KB (%SIZE_MB% MB)
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Show all backups
echo Available backups:
echo.
for /d %%D in (backups\backup_*) do (
    echo   - %%~nxD
)
echo.

:: Cleanup old backups prompt
set /p CLEANUP="Delete backups older than 7 days? (Y/N): "
if /i "%CLEANUP%"=="Y" (
    echo.
    echo Cleaning up old backups...
    forfiles /p "backups" /d -7 /c "cmd /c if @isdir==TRUE rmdir /s /q @path" 2>nul
    echo Done.
)

echo.
pause
