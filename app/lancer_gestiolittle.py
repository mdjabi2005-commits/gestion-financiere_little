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
import subprocess
import webbrowser
import time
import socket
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


def launch_streamlit_portable(app_path, port):
    """Lance Streamlit en mode PORTABLE"""
    print("\n" + "=" * 60)
    print(" GESTION FINANCIÈRE LITTLE — MODE PORTABLE ")
    print("=" * 60)
    print("\nNe fermez pas cette fenêtre tant que l'application est ouverte.\n")
    print(f"Application : {app_path}")
    print(f"Port utilisé : {port}")
    print(f"Python embarqué : {sys.executable}")

    # Dossier de logs dans le dossier de l'exécutable
    log_dir = Path(get_exe_dir()) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "streamlit_portable.log"

    print(f"Fichier log : {log_file}\n")

    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--logger.level", "info"
    ]

    print("Commande exécutée :")
    print(" ".join(cmd))
    print("\nDémarrage du serveur Streamlit...")

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=== Démarrage Streamlit Portable ===\n")
            f.write(f"Commande : {' '.join(cmd)}\n")
            f.write(f"Dossier : {get_base_path()}\n")
            f.write("=" * 50 + "\n\n")
            f.flush()

            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=get_base_path()
            )

        print("Attente du démarrage (45 secondes max)...")

        for i in range(15):
            time.sleep(1)
            print(f"  ... {i + 1}s", end="\r")

            try:
                with socket.create_connection(("localhost", port), timeout=0.5):
                    print("\n[OK] Port ouvert, Streamlit en cours d'exécution.")
                    break
            except Exception:
                pass
        else:
            if not wait_for_port(port, timeout=30):
                print("\n[ERREUR] Le serveur ne s'est pas lancé dans les temps.")
                print(f"Consultez le log : {log_file}")
                input("\nAppuyez sur Entrée pour fermer...")
                process.terminate()
                sys.exit(1)

        print("\nServeur prêt !")
        url = f"http://localhost:{port}"

        time.sleep(2)
        if webbrowser.open(url):
            print(f"Navigateur ouvert automatiquement : {url}")
        else:
            print(f"Ouvrez manuellement : {url}")

        print("\nL'application est maintenant en cours d'exécution.")
        print("Gardez cette fenêtre ouverte pour la garder active.")
        print("Pour arrêter : fermez cette fenêtre ou utilisez Ctrl+C.\n")

        try:
            while True:
                if process.poll() is not None:
                    print("\n[INFO] Le serveur s'est arrêté.")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt demandé...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        print("Application arrêtée proprement.")

    except Exception as e:
        print(f"\n[ERREUR] Exception lors du lancement : {e}")
        import traceback
        traceback.print_exc()
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n=== ERREUR ===\n")
                f.write(str(e) + "\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
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
