@echo off
title  Lancement Gestion Financière Little
color 0A

echo ==========================================================
echo      Gestion Financiere Little - Lanceur Intelligent
echo ==========================================================
echo.

REM --- Vérifie si Python est installé ---
where python >nul 2>nul
if %errorlevel%==0 (
    echo  Python détecté ! Lancement direct de l'application...
    timeout /t 1 >nul
    python -m streamlit run gestiolittle.py --server.headless true
    exit /b
) else (
    echo  Python n'est pas détecté sur ce système.
    echo  Lancement de l'installateur automatique...
    echo.
    powershell -ExecutionPolicy Bypass -File "install_and_run_windows.ps1"
)
pause
