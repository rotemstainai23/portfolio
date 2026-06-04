@echo off
title Portfolio OS — Mobile Mode
echo.
echo  ============================================
echo   Investment OS — Mobile Mode
echo   Accessible from phone on same network
echo  ============================================
echo.

:: Find local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "169.254"') do (
    set LOCAL_IP=%%a
    goto :found
)
:found
set LOCAL_IP=%LOCAL_IP: =%

echo  Local IP: %LOCAL_IP%
echo.
echo  Open on phone (same WiFi):
echo  http://%LOCAL_IP%:5000
echo.
echo  For access from anywhere (Tailscale):
echo  Install Tailscale on PC + phone, then use Tailscale IP
echo.
echo  Press Ctrl+C to stop.
echo.

set FLASK_HOST=0.0.0.0
python "%~dp0app.py"
pause
