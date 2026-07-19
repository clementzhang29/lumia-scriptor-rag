@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ========================================
echo   Lumia ScriptorRAG 智能文档产品
echo   http://127.0.0.1:8080/
echo ========================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not defined PYTHON_CMD (
  echo [错误] 未找到 Python。请安装 Python 或确认 py/python 命令可用。
  pause
  exit /b 1
)

echo [1/3] 正在停止旧的 8080 服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] 正在启动后端...
start "Lumia ScriptorRAG-Backend" /min cmd /c "%PYTHON_CMD% -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info > server.log 2> server_err.log"

echo [3/3] 正在等待服务就绪...
for /l %%i in (1,1,30) do (
  powershell -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8080/api/health' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
  if !errorlevel! equ 0 goto ready
  timeout /t 1 /nobreak >nul
)

echo [错误] 服务未能在 30 秒内启动。请查看 server_err.log
type server_err.log
pause
exit /b 1

:ready
echo.
echo 服务已启动： http://127.0.0.1:8080/
echo API 文档：   http://127.0.0.1:8080/docs
start "" "http://127.0.0.1:8080/"
echo.
echo 这个窗口可以关闭；后端会在后台继续运行。
pause
