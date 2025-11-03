# -*- coding: utf-8 -*-
"""
🚀 Lancer Gestion Financière Little (Version LITE)
--------------------------------------------------
Cette version utilise le Python global de l’utilisateur.
Elle installe automatiquement les dépendances si besoin,
et lance l’application Streamlit sur un port libre.
"""

import os
import sys
import io
import subprocess
import webbrowser
import time
import socket

# ====================================================
# ⚙️ Correction d'encodage console (Windows / PyInstaller)
# ====================================================
os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", errors="replace")
except Exception:
    pass


# ====================================================
# 🔧 Installation automatique de Python et Streamlit
# ====================================================
def run_powershell_script(script_path):
    """Exécute un script PowerShell (install_and_run_windows.ps1)."""
    if not os.path.exists(script_path):
        print(f"⚠️ Script PowerShell introuvable : {script_path}")
        input("Appuie sur Entrée pour quitter...")
        sys.exit(1)
    print("\n🪄 Lancement de l’installation automatique via PowerShell...")
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], shell=True)
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
        print("\n🐍 Python va être installé automatiquement.")
        ps1_path = os.path.join(os.path.dirname(sys.executable), "install_and_run_windows.ps1")
        run_powershell_script(ps1_path)
        return  # tout sera géré par le script PowerShell

    streamlit_answer = input("Avez-vous déjà le module Streamlit installé (si vous ne savez pas, mettez 'non') ? (oui/non) : ").strip().lower()

    if streamlit_answer != "oui":
        install_streamlit_and_deps()
    else:
        print("✅ Parfait, Streamlit semble déjà installé.\n")

    print("🎉 Configuration terminée ! Lancement de l’application...")
    time.sleep(1)


# ====================================================
# 🗂️ Création automatique du dossier .streamlit/config.toml
# ====================================================
def create_streamlit_config():
    """Crée le fichier de configuration Streamlit si manquant."""
    home_dir = os.path.expanduser("~")
    streamlit_dir = os.path.join(home_dir, ".streamlit")
    os.makedirs(streamlit_dir, exist_ok=True)

    config_file = os.path.join(streamlit_dir, "config.toml")
    if not os.path.exists(config_file):
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(
                "[server]\n"
                "headless = true\n"
                "enableCORS = false\n"
                "enableXsrfProtection = false\n"
            )
        print("📝 Fichier config.toml créé avec succès.")


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


# ====================================================
# 🚀 Lancement de Streamlit global
# ====================================================
def launch_streamlit(app_path, port):
    """Lance Streamlit via le Python global et crée un rapport debug complet en cas d’échec."""
    import platform
    import datetime

    print("\n============================================================")
    print("💼 Gestion Financière Little — MODE LITE (version débogage)")
    print("============================================================")
    print("🪄 Ne fermez PAS cette fenêtre tant que vous utilisez l’application.")
    print("💡 Vous pouvez fermer cette fenêtre SEULEMENT après avoir fermé le navigateur.\n")

    sys_info = {
        "OS": platform.system(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Python": sys.version,
        "Executable": sys.executable,
        "App path": app_path,
        "Port": port,
        "Datetime": datetime.datetime.now().isoformat()
    }

    log_file = os.path.join(os.getcwd(), "streamlit_start.log")
    debug_file = os.path.join(os.getcwd(), "streamlit_start_debug.txt")

    with open(debug_file, "w", encoding="utf-8") as dbg:
        dbg.write("🧠 STREAMLIT START DEBUG — GESTION FINANCIÈRE LITTLE (LITE)\n")
        dbg.write("=" * 60 + "\n")
        for key, val in sys_info.items():
            dbg.write(f"{key}: {val}\n")
        dbg.write("=" * 60 + "\n\n")

    print(f"📁 Application : {app_path}")
    print(f"🌐 Port choisi : {port}")
    print(f"🧾 Log Streamlit : {log_file}")
    print(f"🧩 Fichier debug : {debug_file}")

    cmd = [
        "python", "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--logger.level", "debug"
    ]
    print("⚙️ Commande exécutée :", " ".join(cmd))

    with open(log_file, "w", encoding="utf-8") as lf:
        process = subprocess.Popen(cmd, stdout=lf, stderr=lf)

    print("⏳ Démarrage du serveur Streamlit, veuillez patienter...")
    for i in range(6):
        time.sleep(2)
        print(f"   ⏺️  Attente {i * 2 + 2} secondes...")

    if wait_for_port(port, timeout=45):
        print("✅ Serveur prêt ! Ouverture du navigateur…")
        webbrowser.open(f"http://localhost:{port}")
        print("🌐 Le navigateur devrait s’ouvrir automatiquement.")
        print("🔒 Tant que cette fenêtre reste ouverte, l’application reste active.")
        print("🧹 Fermez cette fenêtre uniquement APRÈS avoir fermé le navigateur.\n")
    else:
        print("⚠️ Le serveur Streamlit ne s’est pas lancé correctement.")
        with open(debug_file, "a", encoding="utf-8") as dbg:
            dbg.write("❌ Streamlit n’a pas démarré correctement.\n")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

    return process


# ====================================================
# 🧠 Point d’entrée principal unifié
# ====================================================
def main():
    print("🚀 Démarrage de Gestion Financière Little")
    print("──────────────────────────────────────────────")

    create_streamlit_config()

    setup_done_flag = "setup_done.txt"
    if not os.path.exists(setup_done_flag):
        interactive_installation()
        with open(setup_done_flag, "w") as f:
            f.write("done")

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
