@echo off
echo ============================================
echo   Enable Windows Proxy for Video Capture
echo ============================================
echo.
echo This will configure Windows to use the proxy
echo at 127.0.0.1:8080 for capturing video URLs.
echo.

:: Enable proxy
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:8080" /f

echo.
echo ✅ Proxy enabled! (127.0.0.1:8080)
echo.
echo IMPORTANT: Run the Python script first, then:
echo 1. Open Edge and visit http://mitm.it
echo 2. Download and install the certificate for Windows
echo 3. Then browse to SharePoint!
echo.
echo To disable proxy later, run: disable_proxy.bat
echo.
pause
