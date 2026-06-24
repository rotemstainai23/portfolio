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

REM To enable free Groq LLM instead of Claude CLI:
REM set GROQ_API_KEY=gsk_your_api_key_here

echo  Server: http://127.0.0.1:5000
echo  Browser will open automatically.
echo  Press Ctrl+C to stop.
if defined GROQ_API_KEY (
  echo  Mode: Groq (free, llama-3.3-70b)
) else (
  echo  Mode: Claude CLI
)
echo.

python "%~dp0app.py"
pause
