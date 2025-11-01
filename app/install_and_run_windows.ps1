# --- relance en admin si nécessaire ---
$admin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $admin) {
    Start-Process powershell -Verb RunAs -ArgumentList "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$root = Split-Path -Parent $PSCommandPath
Set-Location $root

function Have($cmd) { $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue) }

function Show-Message {
    param ($title, $message, $type = "Information")
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($message, $title, [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::$type)
}

Write-Host "[1/5] Vérification de Python..."
if (-not (Have "python")) {
    $url = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe"
    $tmp = Join-Path $env:TEMP "python_installer.exe"
    (New-Object System.Net.WebClient).DownloadFile($url, $tmp)
    Start-Process -FilePath $tmp -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
    Remove-Item $tmp -ErrorAction SilentlyContinue
    if (-not (Have "python")) {
        Show-Message "Erreur" "Python n'a pas pu être installé."
        Read-Host "Entrée pour fermer"
        exit 1
    }
}
Write-Host "Python OK"

Write-Host "[2/5] Mise à jour de pip..."
python -m ensurepip --upgrade | Out-Null
python -m pip install --upgrade pip setuptools wheel | Out-Null

Write-Host "[3/5] Installation des dépendances..."
$pkgs = @(
    "streamlit","pandas","pytesseract","Pillow","python-dateutil",
    "opencv-python-headless","numpy","matplotlib","pdfminer.six","requests"
)
python -m pip install --upgrade $pkgs | Out-Null
Write-Host "Modules installés."

$tessLocal = Join-Path $root "tesseract\tesseract.exe"
if (Test-Path $tessLocal) {
    $env:PATH = "$($root)\tesseract;$env:PATH"
}

Write-Host "[4/5] Test des imports..."
$check = @"
try:
    import streamlit, pandas, pytesseract, PIL, dateutil, cv2, numpy, matplotlib, requests
    print("OK")
except Exception as e:
    print("ERR:", e)
"@
$result = python -c $check
if ($result -notmatch "^OK") {
    Show-Message "Erreur" "Un module Python est manquant : $result"
    Read-Host "Entrée pour fermer"
    exit 1
}

Write-Host "[5/5] Lancement..."
$main = Join-Path $root "gestiolittle.py"
if (-not (Test-Path $main)) {
    Show-Message "Erreur" "Fichier gestiolittle.py introuvable."
    Read-Host "Entrée pour fermer"
    exit 1
}

Start-Process "python" "-m streamlit run `"$main`" --server.headless true"
Show-Message "Lancement" "Gestion Financière Little a démarré."
