@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Stop ZCLUM Prism OCR backend
echo ========================================
echo.

echo Stopping processes on port 8080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
    taskkill /f /pid %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul
echo.
echo Service stopped.
echo.
pause

