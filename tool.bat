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
echo   Lumia ScriptorRAG 管理工具
echo ========================================
echo.
echo   [1] 启动后端 + 打开浏览器
echo   [2] 停止后端服务
echo   [3] 构建前端
echo   [4] 端到端测试
echo   [5] 查看服务状态
echo   [6] 退出
echo.

set /p choice="请选择操作 (1-6): "

if "%choice%"=="1" (
    call "%ROOT%start.bat"
)
if "%choice%"=="2" (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do taskkill /f /pid %%a >nul 2>&1
    echo 服务已停止。
)
if "%choice%"=="3" (
    cd /d "%ROOT%frontend"
    npm run build
    echo 前端构建完成。
)
if "%choice%"=="4" (
    if not defined PYTHON_CMD (
      echo [错误] 未找到 Python。
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
