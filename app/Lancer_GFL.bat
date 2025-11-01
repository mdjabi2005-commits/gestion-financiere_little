@echo off
REM ====================================
REM Lanceur Gestion Financière Little
REM ====================================

SETLOCAL EnableDelayedExpansion

REM Définir le dossier du script
SET "SCRIPT_DIR=%~dp0"
CD /D "%SCRIPT_DIR%"

REM Titre de la fenêtre
TITLE Gestion Financiere Little - Lanceur

ECHO.
ECHO ============================================
ECHO   Gestion Financiere Little - Setup
ECHO ============================================
ECHO.

REM Vérifier si PowerShell est disponible
WHERE powershell >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERREUR] PowerShell n'est pas disponible sur ce systeme.
    ECHO.
    ECHO Veuillez installer PowerShell ou lancer gestiolittle.py manuellement.
    PAUSE
    EXIT /B 1
)

ECHO [INFO] Lancement du script d'installation PowerShell...
ECHO.

REM --- Vérifie si Python est installé ---
where python >nul 2>nul
if %errorlevel%==0 (
    echo  Python detecte ! Lancement direct de l'application...
    timeout /t 1 >nul
    python -m streamlit run gestiolittle.py --server.headless true
    PAUSE
    exit /b
) else (
    echo  Python n'est pas détecté sur ce système.
    echo  Lancement de l'installateur automatique...
    echo.
    PowerShell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_and_run_windows.ps1"
)

REM Vérifier le code de sortie du PowerShell
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [ERREUR] Le script PowerShell a rencontre une erreur.
    ECHO Code de sortie : %ERRORLEVEL%
    ECHO.
    PAUSE
    EXIT /B %ERRORLEVEL%
)

ECHO.
ECHO [INFO] Script termine avec succes.
ECHO.
PAUSE
ENDLOCAL
