# =============================
# 🚀 INSTALLATEUR AUTOMATIQUE GUI
# Gestion Financière Little
# =============================

Add-Type -AssemblyName PresentationFramework

function Show-Message {
    param ($title, $message, $type = "Info")
    [System.Windows.MessageBox]::Show($message, $title, [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::$type)
}

function Show-Progress {
    param($message)
    Write-Host ""
    Write-Host "🕐 $message..."
}

function Download-File {
    param ($url, $destination)
    $client = New-Object System.Net.WebClient
    $client.DownloadFile($url, $destination)
}

# 1️⃣ Vérification des droits administrateur
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Show-Message "Droits administrateur requis" "❌ Ce script doit être lancé en tant qu'administrateur.`nClique droit → Exécuter avec PowerShell (Administrateur)" "Error"
    exit
}

# 2️⃣ Vérifier Python
Show-Progress "Vérification de Python"
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue

if (-not $pythonInstalled) {
    $answer = [System.Windows.MessageBox]::Show("Python n'est pas installé.`nVoulez-vous l'installer automatiquement ?", "Installation de Python", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Question)
    if ($answer -eq "No") { exit }

    $url = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe"
    $installer = "$env:TEMP\python_installer.exe"
    Show-Progress "Téléchargement de Python 3.13..."
    Download-File $url $installer

    Show-Progress "Installation silencieuse de Python"
    Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
    Remove-Item $installer -ErrorAction SilentlyContinue
    Show-Message "Installation terminée" "✅ Python 3.13 a été installé avec succès !" "Information"
}

# 3️⃣ Vérifier pip
Show-Progress "Vérification de pip"
try {
    python -m ensurepip --upgrade | Out-Null
    python -m pip install --upgrade pip setuptools wheel | Out-Null
} catch {
    Show-Message "Erreur pip" "❌ Impossible d'installer pip automatiquement.`nVeuillez réessayer après redémarrage du PC." "Error"
    exit
}

# 4️⃣ Installer les dépendances
Show-Progress "Installation des dépendances (cela peut prendre quelques minutes)"
try {
    python -m pip install --upgrade streamlit pandas pytesseract Pillow python-dateutil opencv-python-headless numpy matplotlib pdfminer.six requests | Out-Null
} catch {
    Show-Message "Erreur" "❌ L'installation des dépendances a échoué.`nVérifiez votre connexion internet." "Error"
    exit
}
Show-Message "Dépendances installées" "✅ Toutes les dépendances ont été installées avec succès !" "Information"

# 5️⃣ Lancer l’application
Show-Progress "Lancement de Gestion Financière Little"
try {
    Start-Process "python" "-m streamlit run gestiolittle.py --server.headless true"
    Show-Message "Application lancée" "🚀 Gestion Financière Little a été démarrée avec succès !" "Information"
} catch {
    Show-Message "Erreur" "❌ Impossible de démarrer l'application." "Error"
}
