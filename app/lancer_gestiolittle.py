import os
import sys
import subprocess
import webbrowser
import time
import socket
import shutil
import json
from pathlib import Path

# ====================================================
# 🔧 Vérification de Python et Streamlit
# ====================================================

def have_python():
    """Vérifie si 'python' est disponible dans le PATH."""
    return shutil.which("python") is not None

def have_streamlit():
    """Vérifie si Streamlit est installé pour le Python courant."""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def lancer_launcher():
    """Lance le fichier d’installation ou de lancement selon la plateforme."""
    base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    bat_path = os.path.join(base_dir, "Lancer_GFL.bat")
    ps1_path = os.path.join(base_dir, "install_and_run_windows.ps1")

    print("➡️ Python ou Streamlit manquant — lancement du programme d’installation...")
    if os.path.exists(bat_path):
        try:
            os.startfile(bat_path)
            print("✅ Lancement du fichier batch réussi.")
        except Exception as e:
            print(f"❌ Erreur lors du lancement du .bat : {e}")
    elif os.path.exists(ps1_path):
        try:
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps1_path])
            print("✅ Script PowerShell exécuté.")
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution du PowerShell : {e}")
    else:
        print("❌ Aucun fichier d’installation trouvé dans le dossier.")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

# ====================================================
# 📘 Ouverture automatique du guide d’installation
# ====================================================

def ouvrir_guide_installation():
    """Ouvre le guide d'installation si c'est le premier lancement"""
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
        print("🎉 Premier lancement - Ouverture du guide d'installation...")
        ouvrir_guide = True
        config["premier_lancement"] = False
    elif lancements % 10 == 0:
        print("📖 Rappel - Ouverture du guide d'installation...")
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
            print("📚 Guide d'installation ouvert !")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Impossible d'ouvrir le guide: {e}")

# ====================================================
# 🌐 Gestion du lancement Streamlit
# ====================================================

def wait_for_port(port, timeout=20):
    """Attend que le port Streamlit soit ouvert (jusqu'à timeout secondes)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def get_base_path():
    """Retourne le chemin de base, même si le programme est compilé avec PyInstaller."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def find_app_path(base_path):
    """Cherche le fichier gestiolittle.py à partir de l'emplacement courant."""
    candidates = [
        os.path.join(base_path, "gestiolittle.py"),
        os.path.join(os.path.dirname(base_path), "gestiolittle.py"),
        os.path.join(os.getcwd(), "gestiolittle.py")
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    print("❌ Impossible de trouver gestiolittle.py")
    print("Chemins testés :")
    for p in candidates:
        print(f"   - {p}")
    input("\nAppuie sur Entrée pour fermer…")
    sys.exit(1)

def launch_streamlit(app_path, port=8501):
    """Lance Streamlit proprement et ouvre le navigateur quand le serveur est prêt."""
    streamlit_exe = shutil.which("streamlit")
    if not streamlit_exe:
        print("❌ Streamlit introuvable !")
        input("Appuie sur Entrée pour fermer…")
        sys.exit(1)

    if sys.platform == "win32":
        cmd = ["powershell", "-Command", f'& "{streamlit_exe}" run "{app_path}" --server.port {port}']
    else:
        cmd = [streamlit_exe, "run", app_path, "--server.port", str(port)]

    print(f"Lancement de Streamlit à partir de : {streamlit_exe}")
    print(f"Application : {app_path}")

    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if wait_for_port(port, timeout=30):
        print("✅ Serveur prêt ! Ouverture du navigateur…")
        webbrowser.open(f"http://localhost:{port}")
    else:
        print("⚠️ Le serveur Streamlit ne s'est pas lancé correctement.")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

    return process

# ====================================================
# 🚀 Point d’entrée principal unifié
# ====================================================

def main():
    print("🚀 Démarrage de Gestion Financière Little…")
    print("──────────────────────────────────────────────")

    # 1️⃣ Vérifier Python et Streamlit
    if not have_python() or not have_streamlit():
        print("⚠️ Python ou Streamlit non détecté.")
        lancer_launcher()
        sys.exit(0)

    # 2️⃣ Ouvrir le guide d'installation si nécessaire
    ouvrir_guide_installation()

    # 3️⃣ Lancer l'application Streamlit
    base_path = get_base_path()
    app_path = find_app_path(base_path)
    launch_streamlit(app_path)

    print("✅ Application lancée avec succès.")
    print("💡 Ferme cette fenêtre pour arrêter l'application.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application...")
        sys.exit(0)

if __name__ == "__main__":
    main()
