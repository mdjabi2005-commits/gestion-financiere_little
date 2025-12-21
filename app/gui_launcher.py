"""
Gestio V4 - Centre de Contrôle (Control Center)
Interface complète de gestion : logs, MAJ, changelog, aide
"""

import os
import sys
import json
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import requests
import threading
import time
from datetime import datetime
import zipfile
import shutil

# Helper pour PyInstaller
def get_base_path():
    """Retourne le chemin de base (gère PyInstaller frozen apps)"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent

def get_exe_directory():
    """Retourne le dossier de l'exécutable"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent

# Configuration
SCRIPT_DIR = get_base_path()
EXE_DIR = get_exe_directory()
CONFIG_FILE = SCRIPT_DIR / "launcher_config.json"
GITHUB_REPO = "mdjabi2005-commits/gestion-financiere_little"
LOG_DIR = Path.home() / "analyse" / "logs"

def load_config():
    """Charge la configuration du launcher"""
    default_config = {
        "title": "Gestio V4",
        "subtitle": "Gestion Financière Personnelle",
        "docs_url": "https://mdjabi2005-commits.github.io/gestion-financiere_little",
        "github_url": f"https://github.com/{GITHUB_REPO}",
        "support_url": "https://mdjabi2005-commits.github.io/gestion-financiere_little/support"
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
        except:
            pass
    
    return default_config

def get_version():
    """Lit la version actuelle"""
    version_file = SCRIPT_DIR.parent / "version.txt"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.4.0"

class ControlCenterGUI:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.version = get_version()
        self.app_process = None
        self.python_ready = False
        
        # Configuration fenêtre
        self.root.title(f"{self.config['title']} - Centre de Contrôle")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs V4 (from main.css)
        self.primary_color = "#10b981"      # Vert principal
        self.secondary_color = "#3b82f6"    # Bleu secondaire
        self.danger_color = "#ef4444"       # Rouge danger  
        self.warning_color = "#f59e0b"      # Orange warning
        self.bg_gradient_start = "#1f2937"  # Gris foncé (sidebar)
        self.bg_gradient_end = "#111827"    # Gris très foncé
        self.text_primary = "#1f2937"       # Texte principal
        self.text_secondary = "#6b7280"     # Texte secondaire
        
        # Couleurs pour l'UI
        self.bg_color = self.bg_gradient_start
        self.accent_color = self.primary_color
        
        self.create_ui()
        
        # CRITIQUE : Lancer vérification automatique au démarrage
        threading.Thread(target=self.auto_verify_setup, daemon=True).start()
        
        # Vérifier MAJ au démarrage
        threading.Thread(target=self.check_updates_silent, daemon=True).start()
    
    def auto_verify_setup(self):
        """Vérifie automatiquement Python + dépendances - Lance console si besoin"""
        # Attendre que l'interface soit prête
        import time
        time.sleep(1)
        
        # Créer et lancer le script de vérification automatique
        self.log_message("INFO", "🔍 Vérification de l'environnement Python...")
        self.launch_auto_check_console()
    
    def create_ui(self):
        """Crée l'interface utilisateur"""
        
        # Header
        header = tk.Frame(self.root, bg=self.bg_color, height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(
            header, 
            text=f"💰 {self.config['title']} - Centre de Contrôle", 
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg="white"
        )
        title.pack(pady=15)
        
        version_label = tk.Label(
            header,
            text=f"Version {self.version}",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg="white"
        )
        version_label.pack()
        
        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Accueil
        self.create_home_tab()
        
        # Tab 2: Logs
        self.create_logs_tab()
        
        # Tab 3: Mises à jour
        self.create_updates_tab()
        
        # Tab 4: Aide
        self.create_help_tab()
    
    def create_home_tab(self):
        """Onglet Accueil"""
        home_frame = ttk.Frame(self.notebook)
        self.notebook.add(home_frame, text="🏠 Accueil")
        
        # Message de bienvenue
        welcome = tk.Label(
            home_frame,
            text="Bienvenue dans Gestio V4",
            font=("Segoe UI", 16, "bold"),
            fg=self.accent_color
        )
        welcome.pack(pady=20)
        
        # Status app
        self.status_frame = tk.LabelFrame(home_frame, text="📊 État de l'application", font=("Segoe UI", 10, "bold"))
        self.status_frame.pack(fill='x', padx=20, pady=10)
        
        self.app_status_label = tk.Label(
            self.status_frame,
            text="● Application arrêtée",
            font=("Segoe UI", 10),
            fg="red"
        )
        self.app_status_label.pack(pady=10)
        
        # Boutons principaux
        btn_frame = tk.Frame(home_frame)
        btn_frame.pack(pady=20)
        
        self.launch_btn = tk.Button(
            btn_frame,
            text="🚀 Lancer l'application",
            command=self.launch_app,
            bg=self.accent_color,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=20,
            height=2,
            relief='flat',
            cursor='hand2'
        )
        self.launch_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹️ Arrêter",
            command=self.stop_app,
            bg="#DC2626",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=15,
            height=2,
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.stop_btn.grid(row=0, column=1, padx=10)
        
        # Actions rapides
        quick_frame = tk.LabelFrame(home_frame, text="⚡ Actions rapides", font=("Segoe UI", 10, "bold"))
        quick_frame.pack(fill='x', padx=20, pady=10)
        
        actions = [
            ("📖 Ouvrir Documentation", lambda: webbrowser.open(self.config['docs_url'])),
            ("🔍 Vérifier les mises à jour", self.check_updates),
            ("📋 Voir les logs", lambda: self.notebook.select(1))
        ]
        
        for i, (text, cmd) in enumerate(actions):
            btn = tk.Button(
                quick_frame,
                text=text,
                command=cmd,
                font=("Segoe UI", 9),
                relief='flat',
                cursor='hand2'
            )
            btn.grid(row=i, column=0, sticky='ew', padx=10, pady=5)
    
    def create_logs_tab(self):
        """Onglet Logs avec parsing intelligent"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")
        
        # Filtres
        filter_frame = tk.Frame(logs_frame)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(filter_frame, text="Filtrer:", font=("Segoe UI", 9, "bold")).pack(side='left', padx=5)
        
        self.log_filter = tk.StringVar(value="ALL")
        filters = [("Tous", "ALL"), ("Erreurs", "ERROR"), ("Warnings", "WARNING"), ("Info", "INFO")]
        
        for text, value in filters:
            tk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.log_filter,
                value=value,
                command=self.filter_logs
            ).pack(side='left', padx=5)
        
        tk.Button(
            filter_frame,
            text="🗑️ Effacer",
            command=self.clear_logs,
            relief='flat'
        ).pack(side='right', padx=5)
        
        # Zone de logs
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Tags pour coloration
        self.log_text.tag_config("ERROR", foreground="#f87171")
        self.log_text.tag_config("WARNING", foreground="#fbbf24")
        self.log_text.tag_config("INFO", foreground="#60a5fa")
        self.log_text.tag_config("SUCCESS", foreground="#34d399")
        self.log_text.tag_config("TIMESTAMP", foreground="#9ca3af")
    
    def create_updates_tab(self):
        """Onglet Mises à jour"""
        updates_frame = ttk.Frame(self.notebook)
        self.notebook.add(updates_frame, text="🔄 Mises à jour")
        
        # Status MAJ
        self.update_status_frame = tk.LabelFrame(
            updates_frame,
            text="État des mises à jour",
            font=("Segoe UI", 10, "bold")
        )
        self.update_status_frame.pack(fill='x', padx=20, pady=10)
        
        self.update_status_label = tk.Label(
            self.update_status_frame,
            text="Vérification en cours...",
            font=("Segoe UI", 10)
        )
        self.update_status_label.pack(pady=10)
        
        self.download_btn = tk.Button(
            self.update_status_frame,
            text="📥 Télécharger et installer",
            command=self.download_update,
            bg=self.accent_color,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.download_btn.pack(pady=10)
        
        # Changelog
        changelog_frame = tk.LabelFrame(
            updates_frame,
            text="📝 Nouveautés",
            font=("Segoe UI", 10, "bold")
        )
        changelog_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.changelog_text = scrolledtext.ScrolledText(
            changelog_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9)
        )
        self.changelog_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_help_tab(self):
        """Onglet Aide"""
        help_frame = ttk.Frame(self.notebook)
        self.notebook.add(help_frame, text="❓ Aide")
        
        tk.Label(
            help_frame,
            text="Centre d'aide Gestio V4",
            font=("Segoe UI", 14, "bold"),
            fg=self.accent_color
        ).pack(pady=20)
        
        # Liens d'aide
        help_links = [
            ("📖 Guide de démarrage", self.config['docs_url'] + "/getting-started"),
            ("🎓 Tutoriels vidéo", self.config['docs_url'] + "/tutorials"),
            ("💬 Support & FAQ", self.config.get('support_url', self.config['docs_url'])),
            ("🐛 Signaler un bug", self.config['github_url'] + "/issues"),
            ("💡 Proposer une fonctionnalité", self.config['github_url'] + "/discussions")
        ]
        
        for text, url in help_links:
            btn = tk.Button(
                help_frame,
                text=text,
                command=lambda u=url: webbrowser.open(u),
                font=("Segoe UI", 10),
                relief='flat',
                cursor='hand2',
                anchor='w'
            )
            btn.pack(fill='x', padx=50, pady=5)
    
    def launch_auto_check_console(self):
        """Lance UNE console qui vérifie TOUT automatiquement"""
        self.log_message("INFO", "Lancement de la vérification automatique...")
        
        check_script = EXE_DIR / "gestio_auto_check.ps1"
        
        script_content = """# Gestio V4 - Vérification Automatique Environnement
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
    
    $modules = @("streamlit", "pandas", "requests")
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
        Write-Host "   ✅ Toutes les dépendances sont installées !" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  ✅ VÉRIFICATION TERMINÉE" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Vous pouvez maintenant utiliser Gestio V4" -ForegroundColor Yellow
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"""
        
        try:
            # Écrire le script
            with open(check_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Lancer la console de vérification
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(check_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.log_message("INFO", "Console de vérification lancée")
            
        except Exception as e:
            self.log_message("ERROR", f"❌ Erreur : {str(e)}")
    
    def check_dependencies(self):
        """Vérifie les dépendances Python (fonction helper)"""
        required = ['streamlit', 'pandas', 'requests']
        missing = []
        
        for module in required:
            try:
                result = subprocess.run(
                    ["python", "-c", f"import {module}"],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode != 0:
                    missing.append(module)
            except:
                missing.append(module)
        
        return missing

    def launch_unified_setup(self, modules=None, need_python=False):
        """Lance UN SEUL script PowerShell pour toute la configuration"""
        self.log_message("INFO", "Création du script de configuration unique...")
        
        setup_script = EXE_DIR / "gestio_setup.ps1"
        
        # Script PowerShell COMPLET et UNIQUE
        if need_python:
            # Cas 1 : Python manquant
            script_content = """# Gestio V4 - Installation Complète
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🚀 Gestio V4 - Installation Complète" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "❌ Python n'est pas installé sur ce système" -ForegroundColor Red
Write-Host ""
Write-Host "🔄 Lancement de l'installateur complet..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$installerPath = Join-Path $PSScriptRoot "install_and_run_windows.ps1"

if (Test-Path $installerPath) {
    Write-Host "✅ Installateur trouvé" -ForegroundColor Green
    Write-Host ""
    & $installerPath
} else {
    Write-Host "❌ Installateur introuvable : $installerPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Téléchargez le package complet depuis GitHub" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Appuyez sur une touche pour quitter..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
"""
        else:
            # Cas 2 : Juste installer des dépendances
            modules_list = ", ".join([f'"{m}"' for m in modules])
            script_content = f"""# Gestio V4 - Installation Dépendances
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  � Gestio V4 - Installation Dépendances" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Modules à installer : {', '.join(modules)}" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏱️  Durée estimée : 2-3 minutes" -ForegroundColor Gray
Write-Host ""
Start-Sleep -Seconds 2

$modules = @({modules_list})
$installed = 0
$failed = 0

foreach ($module in $modules) {{
    Write-Host "──────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "📦 Installation de : $module" -ForegroundColor Cyan
    Write-Host "   Veuillez patienter..." -ForegroundColor Gray
    
    python -m pip install $module --quiet --disable-pip-version-check
    
    if ($LASTEXITCODE -eq 0) {{
        Write-Host "   ✅ $module installé avec succès !" -ForegroundColor Green
        $installed++
    }} else {{
        Write-Host "   ❌ Échec de l'installation de $module" -ForegroundColor Red
        $failed++
    }}
    Write-Host ""
}}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "� RÉSULTAT FINAL" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "   ✅ Installés : $installed" -ForegroundColor Green
if ($failed -gt 0) {{
    Write-Host "   ❌ Échoués   : $failed" -ForegroundColor Red
}}
Write-Host ""

if ($failed -eq 0) {{
    Write-Host "✅ Installation terminée avec succès !" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔄 Relancez Gestio V4 pour utiliser l'application" -ForegroundColor Yellow
}} else {{
    Write-Host "⚠️  Installation terminée avec erreurs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Commande manuelle :" -ForegroundColor White
    Write-Host "   python -m pip install {' '.join(modules)}" -ForegroundColor Gray
}}

Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"""
        
        try:
            # Écrire le script
            with open(setup_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.log_message("INFO", "Lancement de l'installation...")
            
            # Lancer UNE SEULE console PowerShell
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(setup_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            messagebox.showinfo(
                "Installation en cours",
                "L'installation a démarré dans une console PowerShell.\n\n"
                "Suivez les instructions et relancez Gestio V4 après."
            )
            
            # Fermer le Control Center
            self.root.quit()
            
        except Exception as e:
            self.log_message("ERROR", f"❌ Erreur : {str(e)}")
            messagebox.showerror("Erreur", f"Impossible de lancer l'installation:\n{str(e)}")
    
    def launch_app(self):
        """Lance l'application Streamlit"""
        # Vérifier que Python est prêt
        if not self.python_ready:
            messagebox.showwarning(
                "Python non prêt",
                "Python ou les dépendances ne sont pas installés.\n\n"
                "Veuillez installer Python et les dépendances d'abord."
            )
            return
        
        try:
            self.log_message("INFO", "Lancement de l'application Streamlit...")
            
            # main.py est le point d'entrée Streamlit
            main_path = SCRIPT_DIR / "main.py"
            
            if not main_path.exists():
                raise FileNotFoundError(f"main.py introuvable dans {SCRIPT_DIR}")
            
            # CRITICAL: En mode frozen, sys.executable = GestionFinanciere.exe
            # qui relancerait le launcher -> boucle infinie ! 
            # On utilise 'python' du PATH système
            python_cmd = "python" if getattr(sys, 'frozen', False) else sys.executable
            
            self.app_process = subprocess.Popen([
                python_cmd, "-m", "streamlit", "run", str(main_path),
                "--server.port=8501",
                "--server.headless=true"
            ])
            
            self.app_status_label.config(text="● Application en cours d'exécution", fg="green")
            self.launch_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
            self.log_message("SUCCESS", "✅ Application lancée sur http://localhost:8501")
            
            # Ouvrir navigateur
            time.sleep(2)
            webbrowser.open("http://localhost:8501")
            
        except Exception as e:
            self.log_message("ERROR", f"❌ Erreur au lancement: {str(e)}")
            messagebox.showerror("Erreur", f"Impossible de lancer l'application:\n{str(e)}")
    
    def stop_app(self):
        """Arrête l'application"""
        if self.app_process:
            self.app_process.terminate()
            self.app_process = None
            
            self.app_status_label.config(text="● Application arrêtée", fg="red")
            self.launch_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            
            self.log_message("INFO", "Application arrêtée")
    
    def log_message(self, level, message):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "TIMESTAMP")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
    
    def monitor_logs(self):
        """Surveille les logs de l'application en temps réel"""
        log_file = LOG_DIR / "app.log"
        
        # Créer le fichier s'il n'existe pas
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.touch()
        
        last_position = 0
        
        while self.log_monitoring:
            try:
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                        # Aller à la dernière position lue
                        f.seek(last_position)
                        new_lines = f.readlines()
                        last_position = f.tell()
                        
                        # Parser et afficher les nouvelles lignes
                        for line in new_lines:
                            self.parse_and_display_log(line.strip())
                
                time.sleep(1)  # Vérifier toutes les secondes
            except Exception as e:
                print(f"Erreur monitoring logs: {e}")
                time.sleep(5)
    
    def parse_and_display_log(self, line):
        """Parse une ligne de log et l'affiche avec intelligence"""
        if not line:
            return
        
        # Détecter le niveau de log
        level = "INFO"
        if "ERROR" in line or "Exception" in line or "Traceback" in line:
            level = "ERROR"
        elif "WARNING" in line or "WARN" in line:
            level = "WARNING"
        elif "SUCCESS" in line or "✅" in line:
            level = "SUCCESS"
        
        # Parser les erreurs pour identifier le module
        error_info = self.identify_error_source(line)
        
        if error_info:
            # Afficher erreur avec contexte
            self.log_message(
                level,
                f"{error_info['module']} : {error_info['message']}"
            )
            if error_info.get('solution'):
                self.log_message("INFO", f"  💡 Solution : {error_info['solution']}")
        else:
            # Afficher ligne normale
            self.log_message(level, line)
    
    def identify_error_source(self, line):
        """Identifie le module et la cause d'une erreur"""
        error_patterns = {
            "ModuleNotFoundError": {
                "module": "Imports",
                "solution": "Vérifier les dépendances installées"
            },
            "FileNotFoundError": {
                "module": "Fichiers",
                "solution": "Vérifier les chemins de fichiers"
            },
            "DatabaseError": {
                "module": "Base de données",
                "solution": "Vérifier l'intégrité de finances.db"
            },
            "OCR": {
                "module": "Scanner OCR",
                "solution": "Vérifier Tesseract et les images"
            },
            "streamlit": {
                "module": "Interface Streamlit",
                "solution": "Redémarrer l'application"
            },
            "domains.transactions": {
                "module": "Gestion Transactions",
                "solution": "Vérifier la base de données"
            },
            "domains.ocr": {
                "module": "Module OCR",
                "solution": "Vérifier les patterns OCR"
            },
            "shared.database": {
                "module": "Accès Base de données",
                "solution": "Vérifier la connexion DB"
            }
        }
        
        for pattern, info in error_patterns.items():
            if pattern in line:
                return {
                    "module": info["module"],
                    "message": line,
                    "solution": info["solution"]
                }
        
        return None
    
    def filter_logs(self):
        """Filtre les logs par niveau"""
        filter_value = self.log_filter.get()
        
        if filter_value == "ALL":
            return  # Tout afficher
        
        # Réafficher seulement les logs du niveau sélectionné
        # TO DO: Implémenter filtrage avec stockage des logs
        self.log_message("INFO", f"Filtre {filter_value} activé")
    
    def clear_logs(self):
        """Efface les logs affichés"""
        self.log_text.delete(1.0, tk.END)
    
    def check_updates_silent(self):
        """Vérifie les MAJ en arrière-plan"""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip('v')
                
                if latest_version and latest_version != self.version:
                    self.update_data = data
                    self.update_status_label.config(
                        text=f"🎉 Nouvelle version {latest_version} disponible !",
                        fg="green"
                    )
                    self.download_btn.config(state='normal')
                    
                    # Charger changelog
                    changelog = data.get("body", "Aucune description disponible")
                    self.changelog_text.delete(1.0, tk.END)
                    self.changelog_text.insert(1.0, changelog)
                else:
                    self.update_status_label.config(
                        text="✅ Vous avez la dernière version",
                        fg="green"
                    )
        except:
            self.update_status_label.config(
                text="❌ Impossible de vérifier les mises à jour",
                fg="red"
            )
    
    def check_updates(self):
        """Force la vérification des MAJ"""
        self.update_status_label.config(text="Vérification en cours...")
        threading.Thread(target=self.check_updates_silent, daemon=True).start()
    
    def download_update(self):
        """Ouvre la page de téléchargement GitHub"""
        if hasattr(self, 'update_data'):
            webbrowser.open(self.update_data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"))
        else:
            webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases")

def main():
    root = tk.Tk()
    app = ControlCenterGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
