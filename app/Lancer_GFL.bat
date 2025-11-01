@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

"%PS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_and_run_windows.ps1"
endlocal
pause
