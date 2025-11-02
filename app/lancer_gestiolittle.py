# -*- coding: utf-8 -*-
"""
🚀 Lancer Gestion Financière Little
-----------------------------------
Ce script vérifie la configuration Python/Streamlit,
crée le fichier config.toml si nécessaire,
et lance l’application Streamlit sur un port libre.
"""

import os
import sys
import io
import subprocess
import webbrowser
import time
import socket
import shutil
import json
from pathlib import Path

# ====================================================
# ⚙️ Correction d'encodage console (Windows / PyInstaller)
# ====================================================
os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", errors="replace")
except Exception:
    # En mode compilé, les flux peuvent déjà être redirigés
    pass


# ====================================================
# 📘 Ouverture automatique du guide d’installation
# ====================================================
def ouvrir_guide_installation():
    """Ouvre le guide d'installation au premier lancement ou périodiquement."""
    config_dir = Path.home() / ".gestiolittle"
    config_file = config_dir / "config.json"
    config_dir.mkdir(exist_ok=True)

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {"premier_lancement": True, "lancements": 0}

    config["lancements"] = config.get("lancements", 0) + 1
    premier_lancement = config.get("premier_lancement", True)
    lancements = config.get("lancements", 0)

    guide_path = Path(__file__).parent / "GUIDE_INSTALLATION.md"
    ouvrir_guide = False

    if premier_lancement:
        print("📖 Premier lancement – ouverture du guide d’installation...")
        ouvrir_guide = True
        config["premier_lancement"] = False
    elif lancements % 10 == 0:
        print("📖 Rappel – ouverture du guide d’installation...")
        ouvrir_guide = True

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    if ouvrir_guide and guide_path.exists():
        try:
            if sys.platform == "win32":
                os.startfile(str(guide_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(guide_path)])
            else:
                subprocess.run(["xdg-open", str(guide_path)])
            print("✅ Guide d’installation ouvert !")
        except Exception as e:
            print(f"❌ Impossible d'ouvrir le guide : {e}")


# ====================================================
# 🌐 Gestion du lancement Streamlit
# ====================================================
def find_free_port(start=8501):
    """Trouve un port libre à partir du port de base."""
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1


def wait_for_port(port, timeout=30):
    """Attend que le port Streamlit soit ouvert (jusqu’à timeout secondes)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def get_base_path():
    """Retourne le chemin de base, compatible PyInstaller."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def find_app_path(base_path):
    """Localise gestiolittle.py."""
    candidates = [
        os.path.join(base_path, "gestiolittle.py"),
        os.path.join(os.path.dirname(base_path), "gestiolittle.py"),
        os.path.join(os.getcwd(), "gestiolittle.py"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    print("❌ Impossible de trouver gestiolittle.py")
    for p in candidates:
        print(f"   - {p}")
    input("\nAppuie sur Entrée pour fermer…")
    sys.exit(1)


def launch_streamlit(app_path, port=8501):
    """
    Lance Streamlit depuis le CLI embarqué dans le bundle PyInstaller.
    Si cli.py est introuvable, affiche un message d’erreur clair.
    """

    # Vérifie que _MEIPASS existe (donc qu’on est dans un bundle PyInstaller)
    if not hasattr(sys, "_MEIPASS"):
        print("⚠️ Environnement PyInstaller non détecté.")
        print("💡 Utilisez cette fonction uniquement dans la version portable.")
        return

    # Chemin attendu vers le Streamlit embarqué
    streamlit_cli = os.path.join(sys._MEIPASS, "streamlit","web", "cli.py")

    if not os.path.exists(streamlit_cli):
        print("❌ Le module Streamlit n’a pas été trouvé dans le bundle (_MEIPASS).")
        print(f"📂 Emplacement attendu : {streamlit_cli}")
        print("💡 Essayez de reconstruire l’exécutable avec --hidden-import streamlit")
        return

    # Commande de lancement directe
    cmd = [
        sys.executable,          # Python embarqué
        streamlit_cli,           # Le vrai point d’entrée Streamlit
        "run",                   # Commande Streamlit
        app_path,                # Ton application principale
        "--server.port", str(port),
        "--server.headless", "true"
    ]

    print("🚀 Lancement de Streamlit embarqué…")
    print(f"🧩 Commande : {' '.join(cmd)}")

    try:
        # Lancer le serveur Streamlit
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(3)

        # Lecture du log initial (optionnel)
        for i in range(10):
            line = process.stdout.readline()
            if not line:
                break
            print("📄", line.strip())

        print("✅ Streamlit a été lancé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors du lancement de Streamlit : {e}")

# ====================================================
# 🧠 Point d’entrée principal unifié
# ====================================================
def main():
    print("🚀 Démarrage de Gestion Financière Little")
    print("──────────────────────────────────────────────")

    port = find_free_port(8501)
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    print(f"🌍 Streamlit démarrera sur le port {port}")

    base_path = get_base_path()
    app_path = find_app_path(base_path)
    launch_streamlit(app_path, port)

    print("✅ Application lancée avec succès.")
    print("💡 Ferme cette fenêtre pour arrêter l’application.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l’application...")
        sys.exit(0)


if __name__ == "__main__":
    main()

