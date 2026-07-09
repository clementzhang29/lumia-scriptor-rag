@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ========================================
echo   ZCLUM Prism OCR / 光棱 OCR
echo   http://127.0.0.1:8080/
echo ========================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not defined PYTHON_CMD (
  echo [ERROR] Python was not found. Please install Python or make py/python available.
  pause
  exit /b 1
)

echo [1/3] Stopping old service on port 8080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] Starting backend...
start "ZCLUM-Prism-OCR-Backend" /min cmd /c "%PYTHON_CMD% -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info > server.log 2> server_err.log"

echo [3/3] Waiting for service...
for /l %%i in (1,1,30) do (
  powershell -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8080/api/health' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
  if !errorlevel! equ 0 goto ready
  timeout /t 1 /nobreak >nul
)

echo [ERROR] Service did not start within 30 seconds. See server_err.log.
type server_err.log
pause
exit /b 1

:ready
echo.
echo Service started: http://127.0.0.1:8080/
echo API docs:        http://127.0.0.1:8080/docs
start "" "http://127.0.0.1:8080/"
echo.
echo You can close this window. The backend keeps running in the background.
pause

