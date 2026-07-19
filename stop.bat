@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   停止 Lumia ScriptorRAG 后端服务
echo ========================================
echo.

echo 正在查找占用的端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
    taskkill /f /pid %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul
echo.
echo 服务已停止。
echo.
pause
