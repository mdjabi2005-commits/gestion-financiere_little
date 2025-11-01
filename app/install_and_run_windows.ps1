# ====================================
# 🚀 Installation et lancement automatique
# Gestion Financière Little - Windows
# ====================================

# --- Relance en admin si nécessaire ---
$admin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $admin) {
    Write-Host "⚠️  Élévation des privilèges administrateur nécessaire..."
    Start-Process powershell -Verb RunAs -ArgumentList "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

# Définir le dossier racine
$root = Split-Path -Parent $PSCommandPath
Set-Location $root

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  🚀 Gestion Financière Little - Setup"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# Fonction pour vérifier si une commande existe
function Have($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

# Fonction pour afficher des messages popup
function Show-Message {
    param (
        [string]$title,
        [string]$message,
        [string]$type = "Information"
    )
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($message, $title, [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::$type)
}

# Fonction pour télécharger un fichier
function Download-File {
    param (
        [string]$url,
        [string]$destination
    )
    try {
        Write-Host "📥 Téléchargement depuis : $url"
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($url, $destination)
        return $true
    }
    catch {
        Write-Host "❌ Erreur de téléchargement : $_"
        return $false
    }
}

# ====================================
# ÉTAPE 1 : Vérification de Python
# ====================================
Write-Host "[1/6] 🐍 Vérification de Python..."

if (-not (Have "python")) {
    Write-Host "⚠️  Python n'est pas installé sur ce système."
    Write-Host ""
    $response = Read-Host "Voulez-vous installer Python automatiquement ? (O/n)"
    
    if ($response -match "^[OoYy]?$") {
        Write-Host "📦 Installation de Python 3.13.0..."
        
        # URL de Python 3.13.0 (64-bit)
        $pythonUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe"
        $pythonInstaller = Join-Path $env:TEMP "python_installer.exe"
        
        # Télécharger l'installateur
        if (Download-File -url $pythonUrl -destination $pythonInstaller) {
            Write-Host "✅ Téléchargement terminé"
            Write-Host "🔧 Installation en cours (cela peut prendre quelques minutes)..."
            
            # Installer Python silencieusement avec PATH
            Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
            
            # Nettoyer
            Remove-Item $pythonInstaller -ErrorAction SilentlyContinue
            
            # Rafraîchir les variables d'environnement
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            
            # Vérifier si Python est maintenant disponible
            Start-Sleep -Seconds 2
            if (-not (Have "python")) {
                Show-Message "Erreur" "❌ Python n'a pas pu être installé correctement.`n`nVeuillez l'installer manuellement depuis python.org" "Error"
                Read-Host "Appuyez sur Entrée pour fermer"
                exit 1
            }
            
            Write-Host "✅ Python installé avec succès !"
        }
        else {
            Show-Message "Erreur" "❌ Impossible de télécharger Python.`n`nVérifiez votre connexion Internet." "Error"
            Read-Host "Appuyez sur Entrée pour fermer"
            exit 1
        }
    }
    else {
        Write-Host ""
        Write-Host "📋 Installation manuelle requise :"
        Write-Host "   1. Téléchargez Python depuis https://www.python.org/downloads/"
        Write-Host "   2. Installez-le en cochant 'Add Python to PATH'"
        Write-Host "   3. Relancez ce script"
        Write-Host ""
        Read-Host "Appuyez sur Entrée pour fermer"
        exit 1
    }
}
else {
    $pythonVersion = python --version
    Write-Host "✅ Python détecté : $pythonVersion"
}

# ====================================
# ÉTAPE 2 : Mise à jour de pip
# ====================================
Write-Host ""
Write-Host "[2/6] 📦 Mise à jour de pip..."
try {
    python -m ensurepip --upgrade 2>&1 | Out-Null
    python -m pip install --upgrade pip setuptools wheel --quiet
    Write-Host "✅ pip mis à jour"
}
catch {
    Write-Host "⚠️  Erreur lors de la mise à jour de pip (peut être ignorée)"
}

# ====================================
# ÉTAPE 3 : Installation des dépendances
# ====================================
Write-Host ""
Write-Host "[3/6] 📚 Installation des dépendances Python..."
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
    Write-Host "✅ Tous les modules Python sont installés"
}
catch {
    Write-Host "⚠️  Erreur lors de l'installation des modules"
    Write-Host "   Tentative de réinstallation sans cache..."
    python -m pip install --upgrade $packages --no-cache-dir
}

# ====================================
# ÉTAPE 4 : Configuration de Tesseract
# ====================================
Write-Host ""
Write-Host "[4/6] 🔍 Configuration de Tesseract OCR..."

$tessLocal = Join-Path $root "tesseract\tesseract.exe"
if (Test-Path $tessLocal) {
    $env:PATH = "$($root)\tesseract;$env:PATH"
    Write-Host "✅ Tesseract local détecté et configuré"
}
else {
    # Vérifier si Tesseract est installé sur le système
    if (Have "tesseract") {
        Write-Host "✅ Tesseract système détecté"
    }
    else {
        Write-Host "⚠️  Tesseract OCR non détecté"
        Write-Host "   L'OCR automatique ne fonctionnera pas."
        Write-Host ""
        Write-Host "💡 Pour installer Tesseract :"
        Write-Host "   https://github.com/UB-Mannheim/tesseract/wiki"
    }
}

# ====================================
# ÉTAPE 5 : Test des imports
# ====================================
Write-Host ""
Write-Host "[5/6] 🧪 Vérification des modules..."

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
    Show-Message "Erreur" "❌ Un module Python est manquant ou corrompu :`n`n$result`n`nEssayez de réinstaller les dépendances manuellement." "Error"
    Read-Host "Appuyez sur Entrée pour fermer"
    exit 1
}

Write-Host "✅ Tous les modules sont opérationnels"

# ====================================
# ÉTAPE 6 : Lancement de l'application
# ====================================
Write-Host ""
Write-Host "[6/6] 🚀 Lancement de l'application..."

$mainScript = Join-Path $root "gestiolittle.py"
if (-not (Test-Path $mainScript)) {
    Show-Message "Erreur" "❌ Fichier gestiolittle.py introuvable dans :`n$root`n`nVérifiez l'installation." "Error"
    Read-Host "Appuyez sur Entrée pour fermer"
    exit 1
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  ✅ Configuration terminée !"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""
Write-Host "💡 L'application va s'ouvrir dans votre navigateur"
Write-Host "💡 Pour arrêter : Fermez cette fenêtre (Ctrl+C)"
Write-Host ""

Start-Sleep -Seconds 2

# Lancer Streamlit
Start-Process "python" "-m streamlit run `"$mainScript`" --server.port 8501 --server.headless true"

Show-Message "Gestion Financière Little" "✅ Application démarrée avec succès !`n`nElle devrait s'ouvrir dans votre navigateur dans quelques secondes." "Information"

Write-Host "✅ Application lancée"
Write-Host "🌐 Accès : http://localhost:8501"
Write-Host ""
Write-Host "📝 Gardez cette fenêtre ouverte tant que vous utilisez l'application"
Write-Host ""
