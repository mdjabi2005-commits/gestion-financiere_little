#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Lancer Gestion Financière Little (Version PORTABLE)
------------------------------------------------------
Cette version utilise le Python embarqué dans l'exécutable PyInstaller.
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
    """Retourne le chemin de base (dossier temporaire PyInstaller)"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_exe_dir():
    """Retourne le dossier de l'exécutable (pas le temp)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def find_app_path():
    """Trouve gestiolittle.py"""
    # Chercher d'abord dans le dossier temp PyInstaller
    base = get_base_path()
    exe_dir = get_exe_dir()
    
    candidates = [
        os.path.join(base, "gestiolittle.py"),
        os.path.join(exe_dir, "gestiolittle.py"),
        os.path.join(exe_dir, "app", "gestiolittle.py"),
    ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"✅ gestiolittle.py trouvé : {path}")
            return path
    
    print("❌ gestiolittle.py introuvable")
    print("\n📂 Chemins testés :")
    for p in candidates:
        print(f"  - {p}")
    input("\nAppuyez sur Entrée pour fermer...")
    sys.exit(1)

def verify_streamlit():
    """Vérifie que Streamlit est disponible dans l'environnement embarqué"""
    print("\n🔍 Vérification de Streamlit embarqué...")
    
    try:
        import streamlit
        print(f"✅ Streamlit trouvé : {streamlit.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Streamlit non trouvé : {e}")
        
        # Afficher le sys.path pour debug
        print("\n📂 Chemins Python (sys.path) :")
        for p in sys.path:
            print(f"  - {p}")
        
        # Vérifier si streamlit est dans site-packages
        base = get_base_path()
        streamlit_path = os.path.join(base, "streamlit")
        if os.path.exists(streamlit_path):
            print(f"\n💡 Streamlit trouvé dans : {streamlit_path}")
            print("   Mais impossible de l'importer...")
        
        return False

def launch_streamlit_portable(app_path, port):
    """Lance Streamlit en mode PORTABLE (Python embarqué)"""
    print("\n" + "="*60)
    print("🚀 Gestion Financière Little — MODE PORTABLE")
    print("="*60)
    print("\n💡 Ne fermez PAS cette fenêtre")
    print(f"📂 Application : {app_path}")
    print(f"🌐 Port : {port}")
    print(f"🐍 Python embarqué : {sys.executable}")
    
    # Créer dossier logs dans le dossier de l'exe (pas dans temp)
    log_dir = Path(get_exe_dir()) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "streamlit_portable.log"
    
    print(f"📝 Logs : {log_file}")
    print("\n⏳ Démarrage du serveur...")
    
    # 🔥 CORRECTION : Commande simple sans pipe
    cmd = [
        sys.executable,  # Python embarqué PyInstaller
        "-m", "streamlit",
        "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--logger.level", "info"
    ]
    
    print(f"🔧 Commande : {' '.join(cmd)}")
    
    try:
        # 🔥 CORRECTION : Redirection simple vers fichier
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Démarrage Streamlit Portable ===\n")
            f.write(f"Commande : {' '.join(cmd)}\n")
            f.write(f"Dossier : {get_base_path()}\n")
            f.write("="*50 + "\n\n")
            f.flush()
            
            # Lancer sans capturer stdout (cause le problème de buffer)
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=get_base_path()
            )
        
        # Attendre le démarrage
        print("⏳ Attente du démarrage (45 secondes max)...")
        
        # Afficher un compteur
        for i in range(15):
            time.sleep(1)
            print(f"  {'.' * (i % 4)}", end="\r")
            
            # Vérifier si le port est ouvert
            try:
                with socket.create_connection(("localhost", port), timeout=0.5):
                    print("\n✅ Port ouvert !")
                    break
            except:
                pass
        else:
            # Timeout : vérifier encore 30 secondes
            if not wait_for_port(port, timeout=30):
                print("\n❌ Le serveur n'a pas démarré dans les temps")
                print(f"📝 Consultez les logs : {log_file}")
                
                # Afficher les logs
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        print("\n📜 Contenu des logs :")
                        print("="*60)
                        print(content[-2000:] if len(content) > 2000 else content)
                        print("="*60)
                except Exception as e:
                    print(f"⚠️  Impossible de lire les logs : {e}")
                
                input("\nAppuyez sur Entrée pour fermer...")
                process.terminate()
                sys.exit(1)
        
        # Serveur démarré
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
        print(f"📝 Logs : {log_file}")
        print()
        
        # Maintenir le processus actif
        try:
            while True:
                # Vérifier si le processus est toujours actif
                if process.poll() is not None:
                    print("\n⚠️  Le serveur s'est arrêté")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ Application arrêtée proprement")
    
    except Exception as e:
        print(f"❌ Erreur lors du lancement : {e}")
        import traceback
        traceback.print_exc()
        
        # Sauvegarder l'erreur dans les logs
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n\n=== ERREUR ===\n")
                f.write(str(e) + "\n")
                traceback.print_exc(file=f)
        except:
            pass
        
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)

def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage de Gestion Financière Little (PORTABLE)")
    print("="*60)
    
    # Informations système
    print(f"\n🐍 Python : {sys.version.split()[0]}")
    print(f"📂 Exécutable : {sys.executable}")
    print(f"📁 Base path : {get_base_path()}")
    print(f"📁 Exe dir : {get_exe_dir()}")
    
    # Vérifier Streamlit
    if not verify_streamlit():
        print("\n❌ Streamlit n'est pas disponible dans l'environnement embarqué")
        print("\n💡 Solutions :")
        print("  1. Vérifiez que PyInstaller a bien inclus Streamlit")
        print("  2. Ajoutez 'streamlit' dans hiddenimports du .spec")
        print("  3. Essayez la version LITE à la place")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)
    
    # Trouver l'application
    app_path = find_app_path()
    
    # Trouver un port libre
    port = find_free_port(8501)
    
    # Lancer Streamlit
    launch_streamlit_portable(app_path, port)

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