# ====================================
# Installation et lancement automatique
# Gestion Financiere Little - Windows
# ====================================

# Configuration encodage UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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
        # Utiliser Invoke-WebRequest pour un meilleur support SSL/TLS
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
        return $true
    }
    catch {
        Write-Host "Erreur de telechargement : $_"
        return $false
    }
}

# ETAPE 1 : Verification de Python
Write-Host "[1/6] Verification de Python..."

# Chercher Python dans plusieurs endroits
$pythonFound = $false
$pythonCmd = ""

# Chercher dans PATH
if (Have "python") {
    $pythonCmd = "python"
    $pythonFound = $true
}
elseif (Have "python3") {
    $pythonCmd = "python3"
    $pythonFound = $true
}

# Chercher dans les emplacements standards
if (-not $pythonFound) {
    $pythonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe"
    )
    
    foreach ($path in $pythonPaths) {
        if (Test-Path $path) {
            $pythonCmd = $path
            $pythonFound = $true
            Write-Host "Python trouve : $path"
            break
        }
    }
}

if (-not $pythonFound) {
    Write-Host "Python n'est pas installe sur ce systeme."
    Write-Host ""
    $response = Read-Host "Voulez-vous installer Python automatiquement ? (O/n)"
    
    if ($response -match "^[OoYy]?$") {
        Write-Host "Installation de Python 3.13.0..."
        
        # Determiner l'architecture
        $arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
        $pythonUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-$arch.exe"
        $pythonInstaller = Join-Path $env:TEMP "python_installer.exe"
        
        if (Download-File -Url $pythonUrl -Destination $pythonInstaller) {
            Write-Host "Telechargement termine"
            Write-Host "Installation en cours (cela peut prendre quelques minutes)..."
            
            # Installation avec tous les composants necessaires
            $installArgs = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1"
            Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait
            
            Remove-Item $pythonInstaller -ErrorAction SilentlyContinue
            
            # Rafraichir le PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # Attendre que Python soit disponible
            Start-Sleep -Seconds 3
            
            # Re-verifier
            if (Have "python") {
                $pythonCmd = "python"
                Write-Host "Python installe avec succes !"
            }
            else {
                Show-Message "Erreur" "Python n'a pas pu etre installe correctement. Veuillez l'installer manuellement depuis python.org" "Error"
                Read-Host "Appuyez sur Entree pour fermer"
                exit 1
            }
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
        Write-Host "   2. IMPORTANT : Cochez 'Add Python to PATH'"
        Write-Host "   3. Relancez ce script"
        Write-Host ""
        Read-Host "Appuyez sur Entree pour fermer"
        exit 1
    }
}
else {
    try {
        $pythonVersion = & $pythonCmd --version 2>&1
        Write-Host "Python detecte : $pythonVersion"
    }
    catch {
        Write-Host "Python detecte : $pythonCmd"
    }
}

# ETAPE 2 : Mise a jour de pip
Write-Host ""
Write-Host "[2/6] Mise a jour de pip..."
try {
    & $pythonCmd -m ensurepip --upgrade 2>&1 | Out-Null
    & $pythonCmd -m pip install --upgrade pip setuptools wheel --quiet 2>&1 | Out-Null
    Write-Host "[OK] pip mis a jour"
}
catch {
    Write-Host "[!] Erreur lors de la mise a jour de pip (peut etre ignoree)"
}

# ETAPE 3 : Installation des dependances
Write-Host ""
Write-Host "[3/6] Installation des dependances Python..."
Write-Host "   (Cela peut prendre 2-5 minutes...)"

$packages = @(
    "streamlit",
    "pandas",
    "pytesseract",
    "Pillow",
    "python-dateutil",
    "opencv-python-headless",
    "numpy",
    "matplotlib",
    "plotly",
    "regex",
    "requests"
)

# Convertir en string pour la commande
$packagesStr = $packages -join " "

Write-Host "   Packages : $packagesStr"

try {
    # Installation avec affichage minimal
    $installCmd = "& `"$pythonCmd`" -m pip install --upgrade $packagesStr"
    Invoke-Expression $installCmd
    Write-Host "[OK] Tous les modules Python sont installes"
}
catch {
    Write-Host "[!] Erreur lors de l'installation des modules"
    Write-Host "   Tentative de reinstallation sans cache..."
    $installCmd = "& `"$pythonCmd`" -m pip install --upgrade --no-cache-dir $packagesStr"
    Invoke-Expression $installCmd
}

# ETAPE 4 : Configuration de Tesseract
Write-Host ""
Write-Host "[4/6] Configuration de Tesseract OCR..."

$tessLocal = Join-Path $root "tesseract\tesseract.exe"
if (Test-Path $tessLocal) {
    $env:PATH = "$($root)\tesseract;$env:PATH"
    Write-Host "[OK] Tesseract local detecte et configure"
}
else {
    if (Have "tesseract") {
        Write-Host "[OK] Tesseract systeme detecte"
    }
    else {
        Write-Host "[!] Tesseract OCR non detecte"
        Write-Host "    L'OCR automatique ne fonctionnera pas."
        Write-Host "    Pour installer : https://github.com/UB-Mannheim/tesseract/wiki"
    }
}

# ETAPE 5 : Test des imports
Write-Host ""
Write-Host "[5/6] Verification des modules..."

$checkScript = @"
import sys
try:
    import streamlit
    import pandas
    import pytesseract
    import PIL
    import dateutil
    import cv2
    import numpy
    import matplotlib
    import plotly
    import regex
    import requests
    print("OK")
except Exception as e:
    print(f"ERR: {e}")
    sys.exit(1)
"@

$tempFile = Join-Path $env:TEMP "check_imports.py"
$checkScript | Out-File -FilePath $tempFile -Encoding UTF8

$result = & $pythonCmd $tempFile 2>&1
Remove-Item $tempFile -ErrorAction SilentlyContinue

if ($result -notmatch "OK") {
    Write-Host "[ERREUR] Un module Python est manquant : $result"
    Write-Host ""
    Write-Host "Essayez d'installer manuellement :"
    Write-Host "  $pythonCmd -m pip install streamlit pandas pytesseract"
    Read-Host "Appuyez sur Entree pour fermer"
    exit 1
}

Write-Host "[OK] Tous les modules sont operationnels"

# ETAPE 6 : Lancement de l'application
Write-Host ""
Write-Host "[6/6] Lancement de l'application..."

# Chercher le launcher V4
$mainScript = Join-Path $root "lancer_gestiolittle.py"
if (-not (Test-Path $mainScript)) {
    # Essayer main.py directement
    $mainScript = Join-Path $root "main.py"
}

if (-not (Test-Path $mainScript)) {
    Show-Message "Erreur" "Fichier de lancement introuvable dans : $root" "Error"
    Read-Host "Appuyez sur Entree pour fermer"
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "  Configuration terminee !"
Write-Host "=========================================="
Write-Host ""
Write-Host "[>] L'application va s'ouvrir dans votre navigateur"
Write-Host "[!] Pour arreter : Fermez cette fenetre (Ctrl+C)"
Write-Host ""


Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[>] Lancement de Gestio V4..."
Write-Host "[!] Gardez cette fenetre ouverte"
Write-Host ""

# Lancer le launcher
try {
    & $pythonCmd $mainScript
}
catch {
    Show-Message "Erreur de lancement" "Impossible de demarrer l'application. Verifiez l'installation." "Error"
    Read-Host "Appuyez sur Entree pour fermer"
    exit 1
}

# Quand Streamlit se ferme
Write-Host ""
Write-Host "[!] L'application a ete arretee."
Write-Host "Appuyez sur une touche pour fermer cette fenetre."
Pause