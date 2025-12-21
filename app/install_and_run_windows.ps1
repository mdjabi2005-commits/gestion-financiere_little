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


# Ce script est appelé uniquement quand Python n'est PAS installé
# On procède directement à l'installation

Write-Host "[1/5] Installation de Python 3.13.0..."
Write-Host ""

# Déterminer l'architecture
$arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
$pythonUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-$arch.exe"
$pythonInstaller = Join-Path $env:TEMP "python_installer.exe"

if (Download-File -Url $pythonUrl -Destination $pythonInstaller) {
    Write-Host "Téléchargement terminé"
    Write-Host "Installation en cours (cela peut prendre quelques minutes)..."
    
    # Installation avec tous les composants nécessaires
    $installArgs = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1"
    Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait
    
    Remove-Item $pythonInstaller -ErrorAction SilentlyContinue
    
    # Rafraîchir le PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # ATTENDRE QUE PYTHON SOIT VRAIMENT INSTALLÉ
    Write-Host "Vérification de l'installation..."
    Write-Host "(Cela peut prendre jusqu'à 20 minutes sur les ordinateurs lents)"
    $maxAttempts = 40  # 40 × 30s = 20 minutes
    $attempt = 0
    $pythonFound = $false
    
    while ($attempt -lt $maxAttempts -and -not $pythonFound) {
        Start-Sleep -Seconds 30
        $attempt++
        
        try {
            $version = & python --version 2>&1
            if ($version -match "Python") {
                $pythonFound = $true
                Write-Host "[OK] Python installé avec succès : $version"
            }
        }
        catch {
            # Continuer à attendre
        }
        
        if (-not $pythonFound -and $attempt -lt $maxAttempts) {
            $elapsed = $attempt * 30
            $remaining = ($maxAttempts - $attempt) * 30
            Write-Host "Attente de l'installation... (${elapsed}s écoulées, ${remaining}s restantes max)"
        }
    }
    
    if (-not $pythonFound) {
        Write-Host "[ERREUR] Python installé mais non détecté après 20 minutes"
        Write-Host "Veuillez redémarrer votre ordinateur et relancer l'application"
        Read-Host "Appuyez sur Entrée pour fermer"
        exit 1
    }
}
else {
    Write-Host "[ERREUR] Impossible de télécharger Python"
    Write-Host ""
    Write-Host "Installation manuelle requise :"
    Write-Host "   1. Téléchargez Python depuis https://www.python.org/downloads/"
    Write-Host "   2. IMPORTANT : Cochez 'Add Python to PATH'"
    Write-Host "   3. Relancez ce script"
    Write-Host ""
    Read-Host "Appuyez sur Entrée pour fermer"
    exit 1
}

# Définir la commande Python
$pythonCmd = "python"

# ETAPE 2 : Mise à jour de pip
Write-Host ""
Write-Host "[2/5] Mise à jour de pip..."
try {
    & $pythonCmd -m ensurepip --upgrade 2>&1 | Out-Null
    & $pythonCmd -m pip install --upgrade pip setuptools wheel --quiet 2>&1 | Out-Null
    Write-Host "[OK] pip mis à jour"
}
catch {
    Write-Host "[!] Erreur lors de la mise à jour de pip (peut être ignorée)"
}

# ETAPE 3 : Installation des paquets Python
Write-Host ""
Write-Host "[3/5] Installation des paquets Python..."
Write-Host "   (Cela peut prendre 2-5 minutes...)"
Write-Host ""

$packages = @(
    "streamlit",
    "pandas",
    "pytesseract",
    "Pillow",
    "python-dateutil",
    "opencv-python-headless",
    "numpy",
    "plotly",
    "regex",
    "requests",
    "pdfminer.six",
    "PyYAML"
)

Write-Host "Installation de $($packages.Count) packages..."
Write-Host ""

$installed = 0
$failed = 0

foreach ($package in $packages) {
    Write-Host "   📦 Installation de $package..." -ForegroundColor Cyan
    
    & $pythonCmd -m pip install $package --quiet --disable-pip-version-check
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✅ $package installé" -ForegroundColor Green
        $installed++
    }
    else {
        Write-Host "      ❌ Échec pour $package" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""

if ($failed -eq 0) {
    Write-Host "[OK] Tous les $installed paquets installés avec succès" -ForegroundColor Green
}
else {
    Write-Host "[AVERTISSEMENT] $installed/$($packages.Count) paquets installés, $failed échecs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tentative de réinstallation des paquets échoués sans cache..." -ForegroundColor Cyan
    Write-Host ""
    
    # Réessayer les échecs
    $retryFailed = 0
    foreach ($package in $packages) {
        # Vérifier si déjà installé
        & $pythonCmd -c "import $package" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   🔄 Retry: $package sans cache..." -ForegroundColor Yellow
            & $pythonCmd -m pip install $package --no-cache-dir --quiet --disable-pip-version-check
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "      ✅ $package installé" -ForegroundColor Green
            }
            else {
                Write-Host "      ❌ Toujours en échec" -ForegroundColor Red
                $retryFailed++
            }
        }
    }
    
    if ($retryFailed -gt 0) {
        Write-Host ""
        Write-Host "[ERREUR CRITIQUE] $retryFailed package(s) impossible(s) à installer" -ForegroundColor Red
        Write-Host ""
        Write-Host "Causes possibles :" -ForegroundColor White
        Write-Host "  - Pas de connexion Internet"
        Write-Host "  - Pare-feu bloque pip"
        Write-Host "  - Proxy requis"
        Write-Host ""
        Read-Host "Appuyez sur Entrée pour fermer"
        exit 1
    }
}

# ETAPE 4 : Configuration de Tesseract
Write-Host ""
Write-Host "[4/5] Configuration de Tesseract OCR..."

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
Write-Host "[5/5] Verification des modules..."

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
    import plotly
    import regex
    import requests
    import pdfminer.six
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

Write-Host ""
Write-Host "=========================================="
Write-Host "  ✅ Installation terminée avec succès !"
Write-Host "=========================================="
Write-Host ""
Write-Host "Pour lancer l'application :"
Write-Host ""
Write-Host " Relancez l'application"
Write-Host ""
Write-Host "=========================================="
Write-Host ""
Read-Host "Appuyez sur Entrée pour fermer"