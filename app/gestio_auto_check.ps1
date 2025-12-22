# Gestio V4 - Vérification Automatique Environnement
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🚀 Gestio V4 - Vérification Environnement" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Vérification automatique de l'environnement..." -ForegroundColor Yellow
Write-Host ""
Start-Sleep -Seconds 1

# ═══════════════════════════════════════════════════════════
# ÉTAPE 1 : Python
# ═══════════════════════════════════════════════════════════
Write-Host "──────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "📌 Étape 1/2 : Vérification Python" -ForegroundColor Cyan
Write-Host ""

$pythonOk = $false
$pythonCmd = $null

# Chercher Python dans le PATH (éviter l'alias Microsoft Store)
try {
    $pythonPath = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pythonPath -and $pythonPath.Source -notlike "*WindowsApps*") {
        $pythonCmd = $pythonPath.Source
    }
} catch {}

# Si pas trouvé, chercher dans les emplacements standards
if (-not $pythonCmd) {
    $standardPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe"
    )
    
    foreach ($path in $standardPaths) {
        if (Test-Path $path) {
            $pythonCmd = $path
            break
        }
    }
}

if ($pythonCmd) {
    try {
        $pythonVersion = & $pythonCmd --version 2>&1
        Write-Host "   ✅ Python détecté : $pythonVersion" -ForegroundColor Green
        Write-Host "   📍 Emplacement : $pythonCmd" -ForegroundColor Gray
        $pythonOk = $true
    } catch {
        Write-Host "   ❌ Python trouvé mais erreur d'exécution" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ Python NON détecté" -ForegroundColor Red
    Write-Host ""
    Write-Host "   💡 Action : Installation de Python requise" -ForegroundColor Yellow
    Write-Host ""
    
    $installerPath = Join-Path $PSScriptRoot "install_and_run_windows.ps1"
    
    if (Test-Path $installerPath) {
        Write-Host "   🔄 Lancement de l'installateur complet..." -ForegroundColor Cyan
        Write-Host ""
        Start-Sleep -Seconds 2
        & $installerPath
        exit 0
    } else {
        Write-Host "   ❌ ERREUR : Installateur introuvable" -ForegroundColor Red
        Write-Host ""
        Write-Host "   📥 Téléchargez le package complet depuis GitHub" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Appuyez sur une touche pour quitter..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

Write-Host ""
Start-Sleep -Seconds 1

# ═══════════════════════════════════════════════════════════
# ÉTAPE 2 : Dépendances
# ═══════════════════════════════════════════════════════════
if ($pythonOk) {
    Write-Host "──────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "📌 Étape 2/2 : Vérification dépendances" -ForegroundColor Cyan
    Write-Host ""
    
    $modules = @("streamlit", "pandas", "requests", "plotly", "numpy", "pytesseract", "PIL", "cv2", "pdfminer", "dateutil", "regex")
    $missing = @()
    
    foreach ($module in $modules) {
        Write-Host "   Vérification de $module..." -ForegroundColor Gray -NoNewline
        
        $result = & $pythonCmd -c "import $module" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅" -ForegroundColor Green
        } else {
            Write-Host " ❌" -ForegroundColor Red
            $missing += $module
        }
    }
    
    Write-Host ""
    
    if ($missing.Count -gt 0) {
        Write-Host "   ⚠️  Modules manquants : $($missing -join ', ')" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   🔄 Installation automatique..." -ForegroundColor Cyan
        Write-Host ""
        Start-Sleep -Seconds 1
        
        $installed = 0
        $failed = 0
        
        foreach ($module in $missing) {
            Write-Host "   📦 Installation de $module..." -ForegroundColor White -NoNewline
            
            & $pythonCmd -m pip install $module --quiet --disable-pip-version-check 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host " ✅" -ForegroundColor Green
                $installed++
            } else {
                Write-Host " ❌" -ForegroundColor Red
                $failed++
            }
        }
        
        Write-Host ""
        
        if ($failed -eq 0) {
            Write-Host "   ✅ Toutes les dépendances installées !" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $failed module(s) non installé(s)" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "   💡 Commande manuelle :" -ForegroundColor White
            Write-Host "      $pythonCmd -m pip install $($missing -join ' ')" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ✅ Toutes les dépendances sont déjà installées !" -ForegroundColor Green
    }
    
    # Afficher un résumé global
    Write-Host ""
    Write-Host "──────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "📊 RÉSUMÉ DE LA CONFIGURATION" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Python :      ✅ Prêt" -ForegroundColor Green
    if ($missing.Count -eq 0) {
        Write-Host "   Dépendances : ✅ Toutes installées" -ForegroundColor Green
    } else {
        Write-Host "   Dépendances : ⚠️  Certaines manquantes" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  ✅ VÉRIFICATION TERMINÉE" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Le Control Center va maintenant s'ouvrir..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Appuyez sur une touche pour continuer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
