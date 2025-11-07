#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lancer Gestion Financière Little (Version PORTABLE)
---------------------------------------------------
Cette version utilise le Python embarqué dans l'exécutable PyInstaller.
Compatible Windows sans support UTF-8 console.
"""

import os
import sys
import webbrowser
import time
import socket
import threading
from pathlib import Path

# Forcer l'encodage console en UTF-8 si possible
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    os.system("chcp 65001 > nul")
except Exception:
    pass


def find_free_port(start=8501):
    """Trouve un port libre"""
    port = start
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        except:
            pass
        port += 1
    return 8501


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
    base = get_base_path()
    exe_dir = get_exe_dir()

    # Principal emplacement (dans le MEIPASS/app/)
    app_path = os.path.join(base, "app", "gestiolittle.py")

    if os.path.exists(app_path):
        print(f"[OK] gestiolittle.py trouvé : {app_path}")
        return app_path

    # Fallback local (pour exécution directe depuis code)
    local_path = os.path.join(exe_dir, "app", "gestiolittle.py")
    if os.path.exists(local_path):
        print(f"[OK] gestiolittle.py trouvé (local) : {local_path}")
        return local_path

    print("[ERREUR] gestiolittle.py introuvable.")
    print("\nChemins testés :")
    print(f"  - {app_path}")
    print(f"  - {local_path}")
    input("\nAppuyez sur Entrée pour fermer...")
    sys.exit(1)


def verify_streamlit():
    """Vérifie que Streamlit est disponible dans l'environnement embarqué"""
    print("\nVérification de Streamlit embarqué...")

    try:
        import streamlit
        print(f"[OK] Streamlit version {streamlit.__version__}")
        return True
    except ImportError as e:
        print(f"[ERREUR] Streamlit non trouvé : {e}")

        print("\nChemins Python (sys.path) :")
        for p in sys.path:
            print(f"  - {p}")

        streamlit_path = os.path.join(get_base_path(), "streamlit")
        if os.path.exists(streamlit_path):
            print(f"\nInfo : Streamlit trouvé dans {streamlit_path}, mais impossible à importer.")
        return False


def open_browser_when_ready(url, port, timeout=40):
    """Thread qui attend que le serveur soit prêt puis ouvre le navigateur"""
    print(f"[INFO] Attente du serveur sur le port {port}...")
    
    if wait_for_port(port, timeout=timeout):
        print("[OK] Serveur détecté ! Ouverture du navigateur...")
        time.sleep(1)  # Petit délai pour que le serveur soit vraiment prêt
        
        try:
            if webbrowser.open(url):
                print(f"[OK] Navigateur ouvert automatiquement : {url}")
            else:
                print("[WARN] Impossible d'ouvrir le navigateur automatiquement")
                print(f"[INFO] Ouvrez manuellement cette URL : {url}")
        except Exception as e:
            print(f"[WARN] Erreur ouverture navigateur : {e}")
            print(f"[INFO] Ouvrez manuellement cette URL : {url}")
    else:
        print(f"[ERREUR] Le serveur n'a pas démarré dans les {timeout} secondes")
        print(f"[INFO] Si le serveur démarre plus tard, utilisez : {url}")


def launch_streamlit_portable(app_path, port):
    """Lance Streamlit en mode PORTABLE (avec Python embarqué dans le .exe PyInstaller)"""
    import streamlit.web.cli as stcli
    
    print("\n" + "=" * 60)
    print(" GESTION FINANCIÈRE LITTLE — MODE PORTABLE ")
    print("=" * 60)
    print("\nNe fermez pas cette fenêtre tant que l'application est ouverte.\n")
    print(f"Application : {app_path}")
    print(f"Port utilisé : {port}")
    print(f"Python embarqué : {sys.executable}")
    
    # ⚠️ IMPORTANT : Configurer le port AVANT de lancer Streamlit
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    
    # Dossier de logs dans le dossier de l'exécutable
    log_dir = Path(get_exe_dir()) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "streamlit_portable.log"
    
    print(f"Fichier log : {log_file}\n")
    print("Démarrage du serveur Streamlit (mode intégré)...")
    print("=" * 60)
    
    # Préparer l'URL
    url = f"http://localhost:{port}"
    
    # Lancer le thread qui va ouvrir le navigateur quand le serveur sera prêt
    # ⚠️ CRITIQUE : Ce thread doit démarrer AVANT l'appel à stcli.main()
    browser_thread = threading.Thread(
        target=open_browser_when_ready,
        args=(url, port, 40),
        daemon=True
    )
    browser_thread.start()
    print("[INFO] Thread d'ouverture du navigateur démarré")
    print(f"[INFO] URL de l'application : {url}")
    print("=" * 60 + "\n")
    
    # On redirige les sorties dans le log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== Démarrage Streamlit Portable ===\n")
        f.write(f"Application : {app_path}\n")
        f.write(f"Port : {port}\n")
        f.write(f"Python embarqué : {sys.executable}\n")
        f.write("=" * 60 + "\n\n")
        f.flush()
        
        # Préparer les arguments pour Streamlit (SANS --server.port)
        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--server.headless", "true",
            "--logger.level", "info"
        ]
        
        # Écriture des infos dans le log
        f.write("Commande équivalente : " + " ".join(sys.argv) + "\n\n")
        f.write("Variables d'environnement :\n")
        f.write(f"  STREAMLIT_SERVER_PORT={port}\n")
        f.write("  STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false\n\n")
        f.flush()
        
        try:
            print("[INFO] Lancement direct du serveur Streamlit...")
            print("[INFO] Cette fenêtre restera ouverte pendant l'exécution")
            print("[INFO] Pour arrêter : fermez cette fenêtre ou appuyez sur Ctrl+C\n")
            
            start_time = time.time()
            
            # ⚠️ BLOQUANT : stcli.main() ne rendra la main que si le serveur s'arrête
            # C'est pourquoi le thread du navigateur doit être lancé AVANT
            stcli.main()
            
            elapsed = int(time.time() - start_time)
            print(f"\n[INFO] Streamlit s'est arrêté (durée d'exécution : {elapsed}s)")
            
        except KeyboardInterrupt:
            print("\n[INFO] Arrêt demandé par l'utilisateur (Ctrl+C)")
        except SystemExit:
            # stcli.main() peut lever SystemExit, c'est normal
            print("\n[INFO] Streamlit s'est terminé normalement")
        except Exception as e:
            print(f"\n[ERREUR] Échec du lancement Streamlit : {e}")
            import traceback
            traceback.print_exc()
            f.write("\n=== ERREUR ===\n")
            f.write(str(e) + "\n")
            traceback.print_exc(file=f)
            input("\nAppuyez sur Entrée pour fermer...")
            sys.exit(1)


def main():
    print("=" * 60)
    print(" DÉMARRAGE DE GESTION FINANCIÈRE LITTLE (PORTABLE) ")
    print("=" * 60)

    print(f"\nPython détecté : {sys.version.split()[0]}")
    print(f"Exécutable : {sys.executable}")
    print(f"Base path  : {get_base_path()}")
    print(f"Exe dir    : {get_exe_dir()}")

    if not verify_streamlit():
        print("\nErreur : Streamlit introuvable dans l'environnement embarqué.")
        print("Vérifiez le build PyInstaller (hidden-imports ou collect-all).")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)

    app_path = find_app_path()
    port = find_free_port(8501)
    launch_streamlit_portable(app_path, port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErreur critique : {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)