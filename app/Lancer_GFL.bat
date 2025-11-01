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

REM Vérifier si Python est installé
where python >nul 2>nul
IF %ERRORLEVEL%==0 (
    ECHO [INFO] Python détecté !
    ECHO [INFO] Vérification de la présence de Streamlit...
    
    REM Vérifie si Streamlit est installé
    python -m pip show streamlit >nul 2>nul
    IF %ERRORLEVEL% NEQ 0 (
        ECHO [AVERTISSEMENT] Streamlit non détecté. Installation automatique...
        python -m pip install streamlit pandas pytesseract Pillow python-dateutil opencv-python-headless numpy matplotlib pdfminer.six requests
        IF %ERRORLEVEL% NEQ 0 (
            ECHO [ERREUR] Impossible d'installer Streamlit automatiquement.
            ECHO Vérifiez votre connexion Internet ou installez-le manuellement :
            ECHO     python -m pip install streamlit
            PAUSE
            EXIT /B 1
        )
        ECHO [OK] Streamlit installé avec succès.
    ) ELSE (
        ECHO [OK] Streamlit déjà présent.
    )
    
    ECHO [INFO] Lancement de l'application...
    timeout /t 1 >nul
    python -m streamlit run gestiolittle.py --server.headless true
    PAUSE
    EXIT /B
) ELSE (
    ECHO [INFO] Python n'est pas détecté sur ce système.
    ECHO [INFO] Lancement de l'installateur automatique...
    ECHO.
    PowerShell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_and_run_windows.ps1"
)

REM Vérifier le code de sortie du PowerShell
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [ERREUR] Le script PowerShell a rencontré une erreur.
    ECHO Code de sortie : %ERRORLEVEL%
    ECHO.
    PAUSE
    EXIT /B %ERRORLEVEL%
)

ECHO.
ECHO [INFO] Script terminé avec succès.
ECHO.
PAUSE
ENDLOCAL
