#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestio V4 - Launcher Console Minimaliste
Actions essentielles + redirection vers site web pour aide
"""

import os
import sys
import subprocess
import webbrowser
import requests
from pathlib import Path

# ==========================================================================
# ⚙️ CONFIGURATION
# ==========================================================================

GITHUB_REPO = "mdjabi2005-commits/gestion-financiere_little"
DOCS_URL = "https://mdjabi2005-commits.github.io/gestion-financiere_little"  # GitHub Pages
VERSION_FILE = Path("version.txt")

# Couleurs console
class C:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(text):
    print(f"{C.GREEN}✅ {text}{C.END}")

def print_error(text):
    print(f"{C.RED}❌ {text}{C.END}")

def print_info(text):
    print(f"{C.BLUE}ℹ️  {text}{C.END}")

# ==========================================================================
# 🚀 FONCTIONS PRINCIPALES
# ==========================================================================

def get_version():
    """Lit version actuelle"""
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text().strip()
    except:
        pass
    return "0.4.0"

def check_update():
    """Vérifie mise à jour sur GitHub"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            latest = response.json().get("tag_name", "").lstrip('v')
            current = get_version()
            if latest != current:
                return latest, response.json().get("html_url")
    except:
        pass
    return None, None

def launch_app():
    """Lance Streamlit"""
    print_info("🚀 Lancement de Gestio V4...")
    print_info("📍 Ouverture dans votre navigateur...")
    print_info("⚠️  Pour arrêter : Ctrl+C\n")
    
    # Trouver main.py dans le même dossier que launcher.py
    script_dir = Path(__file__).parent
    main_path = script_dir / "main.py"
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(main_path),
            "--server.port=8501"
        ])
    except KeyboardInterrupt:
        print_info("\n✋ Application arrêtée")

def open_docs(page=""):
    """Ouvre site web documentation"""
    if page:
        url = f"{DOCS_URL}#{page}"
    else:
        url = DOCS_URL
    print_info(f"📖 Ouverture: {url}")
    webbrowser.open(url)

def open_github():
    """Ouvre page GitHub releases"""
    url = f"https://github.com/{GITHUB_REPO}/releases"
    print_info(f"🔗 Ouverture: {url}")
    webbrowser.open(url)

# ==========================================================================
# 🎨 INTERFACE
# ==========================================================================

def show_banner():
    """Banner d'accueil"""
    version = get_version()
    print(f"""
{C.BOLD}{C.BLUE}
╔═══════════════════════════════════════════════════╗
║                                                   ║
║         💰 Gestio V4 - Launcher                  ║
║         Gestion Financière Personnelle            ║
║         Version {version:<10}                          ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
{C.END}
""")

def show_menu():
    """Menu principal minimaliste"""
    print("\n📋 Actions disponibles:\n")
    print("  1. 🚀 Lancer l'application")
    print("  2. 🔍 Vérifier les mises à jour")
    print("  3. 📖 Documentation (site web)")
    print("  4. 📚 Guide d'installation (site web)")
    print("  5. 🎥 Tutoriels vidéo (site web)")
    print("  6. 💬 Aide et support (site web)")
    print("  7. ❌ Quitter")
    print()
    
    return input("👉 Votre choix: ").strip()

def main():
    """Boucle principale"""
    
    show_banner()
    
    # Check update au démarrage (discret)
    latest, url = check_update()
    if latest:
        print(f"{C.YELLOW}🎉 Nouvelle version disponible: {latest}{C.END}")
        print(f"{C.YELLOW}   Choisissez option 2 pour mettre à jour{C.END}\n")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Lancer app
            launch_app()
        
        elif choice == '2':
            # Check updates
            print_info("🔍 Vérification des mises à jour...")
            latest, url = check_update()
            
            if latest:
                current = get_version()
                print(f"\n{C.GREEN}✨ Nouvelle version disponible !{C.END}")
                print(f"   Actuelle : {current}")
                print(f"   Nouvelle : {latest}\n")
                
                if input("📥 Ouvrir la page de téléchargement ? (o/n): ").lower() == 'o':
                    webbrowser.open(url)
            else:
                print_success("Vous avez la dernière version !")
        
        elif choice == '3':
            # Documentation
            open_docs()
        
        elif choice == '4':
            # Guide installation
            open_docs("installation")
        
        elif choice == '5':
            # Tutoriels
            open_docs("tutoriels")
        
        elif choice == '6':
            # Support
            open_docs("support")
        
        elif choice == '7':
            # Quitter
            print_info("👋 À bientôt !")
            break
        
        else:
            print_error("Choix invalide")
        
        # Pause avant retour au menu
        if choice not in ['1', '7']:
            input("\n⏸  Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n\n👋 Arrêt du launcher")
        sys.exit(0)
