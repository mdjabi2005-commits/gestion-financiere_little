#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestio V4 - Launcher Simplifié
Point d'entrée unique pour toutes les versions
"""

import sys
import os
from pathlib import Path
import subprocess

# Ajouter app au path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def check_first_run():
    """Vérifie si c'est le premier lancement"""
    flag_file = Path.home() / ".gestio_v4_initialized"
    return not flag_file.exists(), flag_file

def create_first_run_script():
    """Crée le script PowerShell de premier lancement"""
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = current_dir
    
    script_path = exe_dir / "first_run_check.ps1"
    
    script_content = """# Gestio V4 - Premier Lancement
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🚀 Gestio V4 - Configuration Initiale" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 VÉRIFICATIONS AU PREMIER LANCEMENT :" -ForegroundColor Yellow
Write-Host "   1. Python installé ?" -ForegroundColor White
Write-Host "   2. Modules requis (tkinter, requests) ?" -ForegroundColor White
Write-Host "   3. Marquage configuration terminée" -ForegroundColor White
Write-Host ""
Start-Sleep -Seconds 2

# ═══════════════════════════════════════════════════════════
# ÉTAPE 1 : Vérification Python
# ═══════════════════════════════════════════════════════════
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🔍 ÉTAPE 1/3 : Vérification Python" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python détecté : $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python non trouvé"
    }
} catch {
    Write-Host "❌ Python n'est pas installé" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 SOLUTION :" -ForegroundColor Yellow
    Write-Host "   Lancez install_and_run_windows.ps1 pour installer Python" -ForegroundColor White
    Write-Host ""
    Write-Host "Appuyez sur une touche pour quitter..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Start-Sleep -Seconds 1

# ═══════════════════════════════════════════════════════════
# ÉTAPE 2 : Vérification des modules critiques
# ═══════════════════════════════════════════════════════════
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📦 ÉTAPE 2/3 : Modules requis" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$modules = @("tkinter", "requests")
$allOk = $true

foreach ($module in $modules) {
    Write-Host "  Vérification de $module..." -ForegroundColor Gray -NoNewline
    
    $result = python -c "import $module" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host ""

if (-not $allOk) {
    Write-Host "⚠️ Modules manquants détectés" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Installez avec : pip install tkinter requests" -ForegroundColor White
    Write-Host ""
    Write-Host "Appuyez sur une touche pour continuer quand même..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# ═══════════════════════════════════════════════════════════
# ÉTAPE 3 : Marquage configuration terminée
# ═══════════════════════════════════════════════════════════
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ ÉTAPE 3/3 : Finalisation" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$flagFile = Join-Path $env:USERPROFILE ".gestio_v4_initialized"
New-Item -ItemType File -Path $flagFile -Force | Out-Null

Write-Host "✅ Configuration terminée !" -ForegroundColor Green
Write-Host ""
Write-Host "🔄 Le Control Center va maintenant s'ouvrir..." -ForegroundColor Yellow
Write-Host ""
Start-Sleep -Seconds 2
"""
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return script_path

def main():
    """Lance le Control Center GUI ou directement l'app selon l'environnement"""
    
    # Détecter le mode
    if getattr(sys, 'frozen', False):
        # Mode compilé
        is_first_run, flag_file = check_first_run()
        
        if is_first_run:
            # Premier lancement : ouvrir UNE console PowerShell
            script_path = create_first_run_script()
            
            # Lancer le script et attendre
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Vérifier si le flag a été créé
            if not flag_file.exists():
                # L'utilisateur a annulé
                sys.exit(1)
        
        # Lancer le Control Center
        from gui_launcher import main as gui_main
        gui_main()
    else:
        # Mode développement : lancer directement Streamlit
        print("🚀 Gestio V4 - Mode Développement")
        print("📍 Lancement de Streamlit...")
        os.system(f"{sys.executable} -m streamlit run {current_dir / 'main.py'}")

if __name__ == "__main__":
    main()
