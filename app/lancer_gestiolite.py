#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Lancer Gestion Financière Little (Version LITE)
--------------------------------------------------
Cette version utilise le Python global de l'utilisateur.
"""

import os
import sys
import subprocess
import webbrowser
import time
import socket
from pathlib import Path

# Configuration encodage
os.environ["PYTHONIOENCODING"] = "utf-8"

def find_free_port(start=8501):
    """Trouve un port libre"""
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1

def wait_for_port(port, timeout=30):
    """Attend que le port soit ouvert"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def get_base_path():
    """Retourne le chemin de base"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def find_app_path():
    """Trouve gestiolittle.py"""
    base = get_base_path()
    candidates = [
        os.path.join(base, "gestiolittle.py"),
        os.path.join(base, "app", "gestiolittle.py"),
    ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"✅ gestiolittle.py trouvé : {path}")
            return path
    
    print("❌ gestiolittle.py introuvable")
    input("Appuyez sur Entrée pour fermer...")
    sys.exit(1)

def check_and_install_deps():
    """Vérifie et installe les dépendances si nécessaire"""
    print("\n🔍 Vérification des dépendances Python...")
    
    # Vérifier si streamlit est installé
    try:
        import streamlit
        print("✅ Streamlit déjà installé")
        return True
    except ImportError:
        print("⚠️  Streamlit n'est pas installé")
        
    # Demander confirmation
    response = input("\n❓ Voulez-vous installer Streamlit et les dépendances ? (O/n) : ").strip().lower()
    if response and response not in ['o', 'oui', 'y', 'yes']:
        print("❌ Installation annulée")
        return False
    
    print("\n📦 Installation des dépendances...")
    packages = [
        "streamlit", "pandas", "pytesseract", "Pillow",
        "python-dateutil", "opencv-python-headless",
        "numpy", "matplotlib", "pdfminer.six", "requests"
    ]
    
    try:
        # 🔥 CORRECTION : Utiliser sys.executable au lieu de "python"
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            check=True
        )
        
        print("✅ Toutes les dépendances sont installées")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation : {e}")
        return False

def launch_streamlit(app_path, port):
    """Lance Streamlit en mode LITE (Python global)"""
    print("\n" + "="*60)
    print("🚀 Gestion Financière Little — MODE LITE")
    print("="*60)
    print("\n💡 Ne fermez PAS cette fenêtre")
    print(f"📂 Application : {app_path}")
    print(f"🌐 Port : {port}")
    
    # Créer dossier logs
    log_dir = Path(get_base_path()) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "streamlit.log"
    
    print(f"📝 Logs : {log_file}")
    print("\n⏳ Démarrage du serveur...")
    
    # 🔥 CORRECTION : Utiliser sys.executable + shell=True sur Windows
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--logger.level", "info"
    ]
    
    print(f"🔧 Commande : {' '.join(cmd)}")
    
    try:
        # Lancer le processus avec logs
        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=get_base_path(),
                # 🔥 IMPORTANT : Ne pas utiliser shell=True avec liste de commandes
            )
        
        # Attendre que le serveur démarre
        print("⏳ Attente du démarrage (30 secondes max)...")
        
        if wait_for_port(port, timeout=30):
            print("✅ Serveur prêt !")
            url = f"http://localhost:{port}"
            
            # Ouvrir le navigateur
            time.sleep(2)
            if webbrowser.open(url):
                print(f"🌐 Navigateur ouvert : {url}")
            else:
                print(f"⚠️  Ouvrez manuellement : {url}")
            
            print("\n" + "="*60)
            print("✅ APPLICATION LANCÉE")
            print("="*60)
            print("\n💡 Gardez cette fenêtre ouverte")
            print("🛑 Pour arrêter : Fermez cette fenêtre ou Ctrl+C")
            print(f"📝 Logs en temps réel : {log_file}")
            print()
            
            # Maintenir le processus actif
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Arrêt demandé...")
                process.terminate()
                process.wait(timeout=5)
            
            print("✅ Application arrêtée proprement")
            
        else:
            print("❌ Le serveur n'a pas démarré")
            print(f"📝 Consultez les logs : {log_file}")
            
            # Afficher les dernières lignes du log
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    print("\n📜 Dernières lignes du log :")
                    print("".join(lines[-20:]))
            except Exception:
                pass
            
            input("\nAppuyez sur Entrée pour fermer...")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Erreur lors du lancement : {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)

def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage de Gestion Financière Little (LITE)")
    print("="*60)
    
    # Vérifier Python
    print(f"\n🐍 Python détecté : {sys.version.split()[0]}")
    print(f"📂 Exécutable : {sys.executable}")
    
    # Vérifier/installer dépendances
    if not check_and_install_deps():
        print("\n❌ Impossible de continuer sans les dépendances")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
    
    # Trouver l'application
    app_path = find_app_path()
    
    # Trouver un port libre
    port = find_free_port(8501)
    
    # Lancer Streamlit
    launch_streamlit(app_path, port)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interruption")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)