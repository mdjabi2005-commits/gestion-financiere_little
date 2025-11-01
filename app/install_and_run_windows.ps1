# ====================================
# Installation et lancement automatique
# Gestion Financiere Little - Windows
# ====================================

# Relance en admin si necessaire
$admin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $admin) {
    Write-Host "Elevation des privileges administrateur necessaire..."
    Start-Process powershell -Verb RunAs -ArgumentList "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$root = Split-Path -Parent $PSCommandPath
Set-Location $root

Write-Host ""
Write-Host "=========================================="
Write-Host "  Gestion Financiere Little - Setup"
Write-Host "=========================================="
Write-Host ""

function Have($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Show-Message {
    param (
        [string]$Title,
        [string]$Message,
        [string]$Type = "Information"
    )
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($Message, $Title, [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::$Type)
}

function Download-File {
    param (
        [string]$Url,
        [string]$Destination
    )
    try {
        Write-Host "Telechargement depuis : $Url"
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $Destination)
        return $true
    }
    catch {
        Write-Host "Erreur de telechargement : $_"
        return $false
    }
}

# ETAPE 1 : Verification de Python
Write-Host "[1/6] Verification de Python..."

if (-not (Have "python")) {
    Write-Host "Python n'est pas installe sur ce systeme."
    Write-Host ""
    $response = Read-Host "Voulez-vous installer Python automatiquement ? (O/n)"
    
    if ($response -match "^[OoYy]?$") {
        Write-Host "Installation de Python 3.13.0..."
        
        $pythonUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe"
        $pythonInstaller = Join-Path $env:TEMP "python_installer.exe"
        
        if (Download-File -Url $pythonUrl -Destination $pythonInstaller) {
            Write-Host "Telechargement termine"
            Write-Host "Installation en cours (cela peut prendre quelques minutes)..."
            
            Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
            
            Remove-Item $pythonInstaller -ErrorAction SilentlyContinue
            
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            
            Start-Sleep -Seconds 2
            if (-not (Have "python")) {
                Show-Message "Erreur" "Python n'a pas pu etre installe correctement. Veuillez l'installer manuellement depuis python.org" "Error"
                Read-Host "Appuyez sur Entree pour fermer"
                exit 1
            }
            
            Write-Host "Python installe avec succes !"
        }
        else {
            Show-Message "Erreur" "Impossible de telecharger Python. Verifiez votre connexion Internet." "Error"
            Read-Host "Appuyez sur Entree pour fermer"
            exit 1
        }
    }
    else {
        Write-Host ""
        Write-Host "Installation manuelle requise :"
        Write-Host "   1. Telechargez Python depuis https://www.python.org/downloads/"
        Write-Host "   2. Installez-le en cochant 'Add Python to PATH'"
        Write-Host "   3. Relancez ce script"
        Write-Host ""
        Read-Host "Appuyez sur Entree pour fermer"
        exit 1
    }
}
else {
    $pythonVersion = python --version
    Write-Host "Python detecte : $pythonVersion"
}

# ETAPE 2 : Mise a jour de pip
Write-Host ""
Write-Host "[2/6] Mise a jour de pip..."
try {
    python -m ensurepip --upgrade 2>&1 | Out-Null
    python -m pip install --upgrade pip setuptools wheel --quiet
    Write-Host "pip mis a jour"
}
catch {
    Write-Host "Erreur lors de la mise a jour de pip (peut etre ignoree)"
}

# ETAPE 3 : Installation des dependances
Write-Host ""
Write-Host "[3/6] Installation des dependances Python..."
Write-Host "   (Cela peut prendre quelques minutes...)"

$packages = @(
    "streamlit",
    "pandas",
    "pytesseract",
    "Pillow",
    "python-dateutil",
    "opencv-python-headless",
    "numpy",
    "matplotlib",
    "pdfminer.six",
    "requests"
)

try {
    python -m pip install --upgrade $packages --quiet
    Write-Host "Tous les modules Python sont installes"
}
catch {
    Write-Host "Erreur lors de l'installation des modules"
    Write-Host "   Tentative de reinstallation sans cache..."
    python -m pip install --upgrade $packages --no-cache-dir
}

# ETAPE 4 : Configuration de Tesseract
Write-Host ""
Write-Host "[4/6] Configuration de Tesseract OCR..."

$tessLocal = Join-Path $root "tesseract\tesseract.exe"
if (Test-Path $tessLocal) {
    $env:PATH = "$($root)\tesseract;$env:PATH"
    Write-Host "Tesseract local detecte et configure"
}
else {
    if (Have "tesseract") {
        Write-Host "Tesseract systeme detecte"
    }
    else {
        Write-Host "Tesseract OCR non detecte"
        Write-Host "   L'OCR automatique ne fonctionnera pas."
        Write-Host ""
        Write-Host "Pour installer Tesseract :"
        Write-Host "   https://github.com/UB-Mannheim/tesseract/wiki"
    }
}

# ETAPE 5 : Test des imports
Write-Host ""
Write-Host "[5/6] Verification des modules..."

$checkScript = @"
try:
    import streamlit
    import pandas
    import pytesseract
    import PIL
    import dateutil
    import cv2
    import numpy
    import matplotlib
    import requests
    print("OK")
except Exception as e:
    print(f"ERR: {e}")
"@

$result = python -c $checkScript
if ($result -notmatch "^OK") {
    Show-Message "Erreur" "Un module Python est manquant ou corrompu : $result Essayez de reinstaller les dependances manuellement." "Error"
    Read-Host "Appuyez sur Entree pour fermer"
    exit 1
}

Write-Host "Tous les modules sont operationnels"

# ETAPE 6 : Lancement de l'application
Write-Host ""
Write-Host "[6/6] Lancement de l'application..."

$mainScript = Join-Path $root "gestiolittle.py"
if (-not (Test-Path $mainScript)) {
    Show-Message "Erreur" "Fichier gestiolittle.py introuvable dans : $root Verifiez l'installation." "Error"
    Read-Host "Appuyez sur Entree pour fermer"
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "  Configuration terminee !"
Write-Host "=========================================="
Write-Host ""
Write-Host "L'application va s'ouvrir dans votre navigateur"
Write-Host "Pour arreter : Fermez cette fenetre (Ctrl+C)"
Write-Host ""

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "🚀 Lancement de l'application Streamlit..."
Write-Host "💡 L'application va s'ouvrir dans votre navigateur (http://localhost:8501)"
Write-Host "💡 Gardez cette fenêtre ouverte tant que vous l'utilisez."
Write-Host ""
Start-Sleep -Seconds 2

# Lancer Streamlit dans la même fenêtre (bloquant)
try {
    python -m streamlit run "`"$mainScript`"" --server.port 8501 --server.headless true
}
catch {
    Show-Message "Erreur de lancement" "Impossible de démarrer Streamlit. Vérifiez l'installation." "Error"
    Read-Host "Appuyez sur Entrée pour fermer"
    exit 1
}

# Quand Streamlit se ferme, garder la console ouverte
Write-Host ""
Write-Host "🛑 L'application a été arrêtée."
Write-Host "Appuyez sur une touche pour fermer cette fenêtre."
Pause
