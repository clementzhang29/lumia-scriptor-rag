@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo.
echo ========================================
echo   ZCLUM Prism OCR Management Tool
echo ========================================
echo.
echo   [1] Start backend and open browser
echo   [2] Stop backend
echo   [3] Build frontend
echo   [4] Run E2E test
echo   [5] Check service status
echo   [6] Exit
echo.

set /p choice="Choose an action (1-6): "

if "%choice%"=="1" (
    call "%ROOT%start.bat"
)
if "%choice%"=="2" (
    call "%ROOT%stop.bat"
)
if "%choice%"=="3" (
    cd /d "%ROOT%frontend"
    npm run build
    echo Frontend build completed.
)
if "%choice%"=="4" (
    if not defined PYTHON_CMD (
      echo [ERROR] Python was not found.
    ) else (
      %PYTHON_CMD% -B test_e2e.py
    )
)
if "%choice%"=="5" (
    powershell -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8080/api/health' | ConvertTo-Json } catch { $_.Exception.Message }"
)
if "%choice%"=="6" exit /b

echo.
pause

