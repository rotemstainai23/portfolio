@echo off
title Investment OS
echo.
echo  ============================================
echo   Investment OS — Starting...
echo  ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo  ERROR: Python not found.
  echo  Install Python 3.8+ from https://python.org
  pause
  exit /b 1
)

echo  Installing / checking dependencies...
python -m pip install -r "%~dp0requirements.txt" -q 2>nul
echo  Dependencies OK.
echo.
echo  Server: http://127.0.0.1:5000
echo  Browser will open automatically.
echo  Press Ctrl+C to stop.
echo.

python "%~dp0app.py"
pause
