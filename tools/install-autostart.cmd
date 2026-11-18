@echo off
rem Registers the "ContentStudio" logon task: the wall starts hidden at every Windows logon
rem and restarts itself if it crashes (see tools\run-server.ps1). Run once by double-click.
schtasks /Create /TN "ContentStudio" /SC ONLOGON /RL LIMITED /F /TR "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\src\content-studio\tools\run-server.ps1"
schtasks /Run /TN "ContentStudio"
echo.
echo Done. Content Studio wall: http://127.0.0.1:8791
pause
