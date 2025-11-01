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
def run_powershell_script(script_path):
    """Exécute un script PowerShell (install_and_run_windows.ps1)."""
    if not os.path.exists(script_path):
        print(f"❌ Script PowerShell introuvable : {script_path}")
        input("Appuie sur Entrée pour quitter...")
        sys.exit(1)
    print("\n🚀 Lancement de l’installation automatique via PowerShell...")
    subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path
    ], shell=True)
    print("\n✅ Installation terminée.\n")


def install_streamlit_and_deps():
    """Installe Streamlit et toutes les dépendances Python nécessaires."""
    print("\n📦 Installation de Streamlit et des dépendances...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "streamlit", "pandas", "pytesseract", "Pillow",
        "python-dateutil", "opencv-python-headless",
        "numpy", "matplotlib", "pdfminer.six", "requests"
    ])
    print("✅ Modules installés avec succès.\n")


def interactive_installation():
    """Demande à l’utilisateur ce qu’il possède déjà et installe en conséquence."""
    print("🧩 Configuration initiale de Gestion Financière Little\n")
    python_answer = input("Avez-vous déjà Python installé sur votre ordinateur ? (oui/non) : ").strip().lower()

    if python_answer != "oui":
        print("\n📦 Python va être installé automatiquement.")
        ps1_path = os.path.join(os.path.dirname(sys.executable), "install_and_run_windows.ps1")
        run_powershell_script(ps1_path)
        return  # tout sera géré par le script PowerShell

    streamlit_answer = input("Avez-vous déjà le module Streamlit installé (Si vous n'êtes pas sur mettez non) ? (oui/non) : ").strip().lower()

    if streamlit_answer != "oui":
        install_streamlit_and_deps()
    else:
        print("✅ Parfait, Streamlit semble déjà installé.\n")

    print("🎉 Configuration terminée ! Lancement de l’application...")
    time.sleep(1)


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

def find_streamlit_executable():
    """Cherche streamlit.exe ou streamlit.cmd dans le même Python."""
    python_dir = os.path.dirname(sys.executable)
    scripts_dir = os.path.join(python_dir, "Scripts")

    # Essaye plusieurs variantes possibles
    candidates = [
        shutil.which("streamlit"),  # classique
        os.path.join(scripts_dir, "streamlit.exe"),
        os.path.join(scripts_dir, "STREAMLIT.EXE"),
        os.path.join(scripts_dir, "streamlit.cmd"),
        os.path.join(scripts_dir, "STREAMLIT.CMD"),
    ]

    for path in candidates:
        if path and os.path.exists(path):
            return path

    return None


def launch_streamlit(app_path, port=8501):
    """Lance Streamlit proprement et ouvre le navigateur quand le serveur est prêt."""
    streamlit_exe = find_streamlit_executable()
    if not streamlit_exe:
        print("❌ Streamlit introuvable, même dans le dossier Python actuel.")
        input("Appuie sur Entrée pour fermer…")
        sys.exit(1)

    print(f"Lancement de Streamlit à partir de : {streamlit_exe}")
    print(f"Application : {app_path}")

    if sys.platform == "win32":
        cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", str(port)]
    else:
        cmd = [streamlit_exe, "run", app_path, "--server.port", str(port)]

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
    """Point d’entrée principal."""
    print("🚀 Démarrage de Gestion Financière Little")
    print("──────────────────────────────────────────────")

    # Vérifie si on doit configurer au premier lancement
    setup_done_flag = "setup_done.txt"
    if not os.path.exists(setup_done_flag):
        interactive_installation()
        with open(setup_done_flag, "w") as f:
            f.write("done")

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
