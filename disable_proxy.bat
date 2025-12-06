@echo off
echo ============================================
echo   Disable Windows Proxy
echo ============================================
echo.

:: Disable proxy
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f

echo.
echo ✅ Proxy disabled!
echo.
echo You can now browse normally.
echo.
pause
