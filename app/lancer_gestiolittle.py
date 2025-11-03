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
    """
    Trouve le fichier gestiolittle.py même s’il est à côté de l’exécutable
    et non pas dans le dossier temporaire _MEIPASS.
    """
    # Dossiers potentiels
    exe_dir = os.path.dirname(sys.executable)  # dossier où se trouve l’exe
    script_dir = os.path.dirname(os.path.abspath(__file__))

    candidates = [
        os.path.join(base_path, "gestiolittle.py"),
        os.path.join(script_dir, "gestiolittle.py"),
        os.path.join(exe_dir, "gestiolittle.py"),
        os.path.join(exe_dir, "app", "gestiolittle.py"),
    ]

    for path in candidates:
        if os.path.exists(path):
            print(f"✅ gestiolittle.py trouvé à : {path}")
            return path

    # En dernier recours, recherche récursive
    for root, dirs, files in os.walk(exe_dir):
        if "gestiolittle.py" in files:
            print(f"✅ gestiolittle.py trouvé dans : {root}")
            return os.path.join(root, "gestiolittle.py")

    print("❌ Impossible de trouver gestiolittle.py.")
    print("🔍 Emplacements testés :")
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
    import select

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

    log_file = os.path.join(os.getcwd(), "streamlit_start.log")
    debug_file = os.path.join(os.getcwd(), "streamlit_start_debug.txt")

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

    print(f"✅ Fichier CLI trouvé : {streamlit_cli}")
    print(f"📁 Application : {app_path}")
    print(f"🌐 Port choisi : {port}")
    print(f"🧾 Log Streamlit : {log_file}")
    print(f"🧩 Fichier debug : {debug_file}")

    # Commande PyInstaller-safe (utilise le python embarqué)
    cmd = [
        sys.executable, "-m", "streamlit.cli", "run", app_path,
        "--server.port", str(port),
        "--logger.level", "debug"
    ]
    print("⚙️ Commande exécutée :", " ".join(cmd))

    # Lancement Streamlit avec affichage en direct + log simultané
    with open(log_file, "w", encoding="utf-8") as lf:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=base_path,
            text=True,
            bufsize=1
        )
        # Lecture en direct dans la console
        for line in process.stdout:
            print(line, end="")
            lf.write(line)

    print("⏳ Démarrage du serveur Streamlit, veuillez patienter...")
    for i in range(6):
        time.sleep(2)
        print(f"   ⏺️  Attente {i * 2 + 2} secondes...")

    if wait_for_port(port, timeout=45):
        print("✅ Serveur prêt ! Ouverture du navigateur…")
        url = f"http://localhost:{port}"
        opened = webbrowser.open(url)

        if opened:
            print("🌐 Le navigateur s'est ouvert automatiquement.")
        else:
            print("⚠️ Impossible d'ouvrir automatiquement le navigateur.")
            print(f"➡️ Ouvrez manuellement : {url}")

        print(f"🔗 Lien local : {url}")
        print("\n💡 Tant que cette fenêtre reste ouverte, l’application reste active.")
        print("   Appuyez sur Entrée pour fermer proprement l’application.\n")

        try:
            # Boucle de maintien du processus
            while True:
                if process.poll() is not None:
                    print("\n✅ Le serveur Streamlit s’est arrêté.")
                    break
                time.sleep(1)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    input("\n🛑 Fermeture manuelle demandée. Appuyez sur Entrée pour confirmer…")
                    process.terminate()
                    print("🧹 Serveur Streamlit arrêté proprement.")
                    break

        except KeyboardInterrupt:
            print("\n🛑 Arrêt manuel via Ctrl+C.")
            process.terminate()
        finally:
            sys.exit(0)

    else:
        print("⚠️ Le serveur Streamlit ne s’est pas lancé correctement.")
        with open(debug_file, "a", encoding="utf-8") as dbg:
            dbg.write("❌ Streamlit n’a pas démarré correctement.\n")
        print("📄 Consultez le fichier debug pour plus d’informations.")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)



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





