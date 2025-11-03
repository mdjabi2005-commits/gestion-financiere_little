# -*- coding: utf-8 -*-
"""
🚀 Lancer Gestion Financière Little (Portable)
---------------------------------------------
Ce script vérifie la configuration Python/Streamlit,
crée le fichier config.toml si nécessaire,
et lance l’application Streamlit embarquée sur un port libre.
"""

import os
import sys
import io
import subprocess
import webbrowser
import time
import socket
from pathlib import Path

# ====================================================
# ⚙️ Configuration globale
# ====================================================
AUTO_OPEN_BROWSER = True   # Ouvrir automatiquement le navigateur
ENABLE_DEBUG = True        # Afficher des messages détaillés dans la console

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
# 🌐 Gestion du lancement Streamlit
# ====================================================
def get_log_paths():
    """Crée le dossier 'logs' dans le répertoire de l’application et renvoie les chemins complets."""
    base_app_dir = Path(get_base_path())        # dossier où se trouve l'exécutable ou le script
    base_log_dir = base_app_dir / "logs"        # sous-dossier 'logs' à créer dans app/
    base_log_dir.mkdir(parents=True, exist_ok=True)

    log_file = base_log_dir / "streamlit_start.log"
    debug_file = base_log_dir / "streamlit_start_debug.txt"

    return str(log_file), str(debug_file)



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
# 🚀 Lancement de Streamlit embarqué
# ====================================================
def launch_embedded_streamlit(app_path, port):
    """Lance le Streamlit embarqué depuis le dossier temporaire PyInstaller."""
    import platform
    import datetime

    print("\n============================================================")
    print("🚀 Gestion Financière Little — MODE PORTABLE (version débogage)")
    print("============================================================")
    print("🪄 Ne fermez PAS cette fenêtre tant que vous utilisez l’application.")
    print("💡 Vous pouvez fermer cette fenêtre SEULEMENT après avoir fermé le navigateur.\n")

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    streamlit_cli = os.path.join(base_path, "Lib", "site-packages", "streamlit", "cli.py")

    sys_info = {
        "OS": platform.system(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Python": sys.version,
        "Executable": sys.executable,
        "App path": app_path,
        "Base path": base_path,
        "Streamlit CLI": streamlit_cli,
        "Port": port,
        "Datetime": datetime.datetime.now().isoformat()
    }

    log_file, debug_file = get_log_paths()


    with open(debug_file, "w", encoding="utf-8") as dbg:
        dbg.write("🧠 STREAMLIT START DEBUG — GESTION FINANCIÈRE LITTLE (PORTABLE)\n")
        dbg.write("=" * 60 + "\n")
        for key, val in sys_info.items():
            dbg.write(f"{key}: {val}\n")
        dbg.write("=" * 60 + "\n\n")

    if not os.path.exists(streamlit_cli):
        print("❌ Fichier CLI Streamlit introuvable.")
        with open(debug_file, "a", encoding="utf-8") as dbg:
            dbg.write("❌ Erreur : Streamlit CLI introuvable.\n")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

    print("✅ Fichier CLI trouvé. Lancement du serveur Streamlit embarqué...")

    cmd = [
        sys.executable, "-m", "streamlit.cli", "run", app_path,
        "--server.port", str(port),
        "--logger.level", "debug"
    ]

    if ENABLE_DEBUG:
        print(f"⚙️ Commande exécutée : {' '.join(cmd)}")

    with open(log_file, "w", encoding="utf-8") as lf:
        process = subprocess.Popen(cmd, stdout=lf, stderr=lf, cwd=base_path)

    print("⏳ Démarrage du serveur interne, veuillez patienter...")
    for i in range(6):
        time.sleep(2)
        if ENABLE_DEBUG:
            print(f"   ⏺️  Attente {i * 2 + 2} secondes...")

    if wait_for_port(port, timeout=45):
        print("✅ Serveur prêt !")
        if AUTO_OPEN_BROWSER:
            webbrowser.open(f"http://localhost:{port}")
            print("🌐 Le navigateur devrait s’ouvrir automatiquement.")
        else:
            print(f"🌐 Ouvre manuellement ton navigateur à l’adresse : http://localhost:{port}")
        print("🔒 Tant que cette fenêtre reste ouverte, l’application reste active.")
    else:
        print("⚠️ Le serveur Streamlit ne s’est pas lancé correctement.")
        with open(debug_file, "a", encoding="utf-8") as dbg:
            dbg.write("❌ Streamlit n’a pas démarré correctement.\n")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

    return process


# ====================================================
# 🧠 Vérification d’environnement avant lancement
# ====================================================
def check_environment(mode="portable"):
    """Vérifie la présence des dossiers et modules essentiels."""
    import importlib
    import platform

    log_path = os.path.join(get_base_path(), "logs", "check_environment.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    print("\n🔍 Vérification de l’environnement...")
    results = []
    errors = []

    def log(msg, status="INFO"):
        line = f"[{status}] {msg}"
        print(line)
        results.append(line)

    log("Système : " + platform.system())
    log("Python : " + sys.version)
    log(f"Mode : {mode}")

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    log(f"Base path : {base_path}")

    streamlit_cli = os.path.join(base_path, "Lib", "site-packages", "streamlit", "cli.py")
    if os.path.exists(streamlit_cli):
        log("✅ Streamlit CLI trouvé", "OK")
    else:
        log("❌ Streamlit CLI introuvable", "FAIL")
        errors.append("Streamlit CLI not found")

    for m in ["streamlit", "pandas", "numpy", "pytesseract", "cv2", "PIL"]:
        try:
            importlib.import_module(m)
            log(f"Module {m} importé avec succès", "OK")
        except Exception as e:
            log(f"Module {m} introuvable : {e}", "FAIL")
            errors.append(f"{m}: {e}")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    if errors:
        print("❌ Problèmes détectés ! Consulte le log pour les détails.")
        print(f"📂 Les fichiers de log se trouvent ici : {Path(get_base_path()) / 'logs'}")
        input("Appuie sur Entrée pour quitter…")
        sys.exit(1)
    else:
        print("✅ Environnement vérifié : tout est prêt.")


# ====================================================
# 🧠 Point d’entrée principal unifié
# ====================================================
def main():
    print("🚀 Démarrage de Gestion Financière Little")
    print("──────────────────────────────────────────────")

    check_environment(mode="portable")
    port = find_free_port(8501)
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    print(f"🌍 Streamlit démarrera sur le port {port}")

    base_path = get_base_path()
    app_path = find_app_path(base_path)
    launch_embedded_streamlit(app_path, port)

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





