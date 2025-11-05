#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lancer Gestion Financière Little (Version LITE)
--------------------------------------------------
Cette version utilise le Python global de l'utilisateur.
"""

import os
import sys
import subprocess
import webbrowser
import time
import socket
import shutil
from pathlib import Path

# ==============================
#  CONFIGURATION CONSOLE UTF-8
# ==============================
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except:
        pass
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")
    except:
        pass
else:
    os.environ["PYTHONIOENCODING"] = "utf-8"

# ==============================
#  OUTILS DE DEBUG
# ==============================

def safe_print(text):
    """Print sécurisé pour éviter les erreurs d'encodage"""
    try:
        print(text)
    except UnicodeEncodeError:
        text = text.encode("ascii", "replace").decode("ascii")
        print(text)


# ==============================
#  FONCTIONS SYSTEME
# ==============================

def find_free_port(start=8501):
    """Trouve un port libre sur la machine"""
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1

def wait_for_port(port, timeout=30):
    """Attend qu’un port spécifique soit ouvert"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def get_base_path():
    """Retourne le chemin de base (répertoire de l'exécutable ou du script)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ==============================
#  DETECTION DE PYTHON
# ==============================

def find_system_python():
    """Trouve le Python système sur Windows (ou Linux/macOS)"""
    if not getattr(sys, 'frozen', False):
        return sys.executable

    safe_print("[DEBUG] Recherche du Python système...")

    # Cherche python.exe dans le PATH
    python_cmd = shutil.which("python")
    if python_cmd:
        safe_print(f"[DEBUG] Python trouvé dans le PATH : {python_cmd}")
        return python_cmd

    python3_cmd = shutil.which("python3")
    if python3_cmd:
        safe_print(f"[DEBUG] Python3 trouvé dans le PATH : {python3_cmd}")
        return python3_cmd

    # Chemins standards
    common_paths = [
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Python311\python.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
    ]
    for path in common_paths:
        if os.path.exists(path):
            safe_print(f"[DEBUG] Python trouvé : {path}")
            return path

    # Recherche dans le registre Windows
    if sys.platform == "win32":
        try:
            import winreg
            paths = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Python\PythonCore"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python\PythonCore"),
            ]
            for hkey, subkey in paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        for i in range(100):
                            try:
                                version = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, f"{version}\\InstallPath") as sub:
                                    install_path = winreg.QueryValue(sub, "")
                                    exe = os.path.join(install_path, "python.exe")
                                    if os.path.exists(exe):
                                        safe_print(f"[DEBUG] Python trouvé dans le registre : {exe}")
                                        return exe
                            except WindowsError:
                                break
                except WindowsError:
                    continue
        except ImportError:
            pass

    safe_print("[ERREUR] Aucun Python trouvé sur le système.")
    return None


# ==============================
#  VERIFICATION ET INSTALLATION DES DEPENDANCES
# ==============================

def check_and_install_deps():
    """Vérifie si Streamlit et les dépendances sont installées"""
    safe_print("[DEBUG] Vérification de l'environnement Python...")

    python_exe = find_system_python()
    if not python_exe:
        safe_print("[ERREUR] Python non trouvé — lancement de l'installation automatique...")
        ps_script = Path(get_base_path()) / "install_and_run_windows.ps1"
        if ps_script.exists():
            safe_print("[DEBUG] Script PowerShell trouvé, lancement...")
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)],
                check=True
            )
            return True
        else:
            safe_print("[ERREUR] Script install_and_run_windows.ps1 manquant.")
            input("Appuyez sur Entrée pour fermer...")
            sys.exit(1)

    safe_print(f"[DEBUG] Python trouvé : {python_exe}")

    packages = [
        "streamlit", "pandas", "pytesseract", "PIL",
        "dateutil", "cv2",
        "numpy", "matplotlib", "pdfminer.six", "requests"
    ]

    missing = []
    for pkg in packages:
        result = subprocess.run(
            [python_exe, "-c", f"import {pkg.split('.')[0]}"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            missing.append(pkg)

    if not missing:
        safe_print("[DEBUG] Toutes les dépendances sont déjà installées.")
        return True

    safe_print(f"[DEBUG] Installation des dépendances manquantes : {', '.join(missing)}")

    try:
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=False)
        subprocess.run([python_exe, "-m", "pip", "install"] + missing, check=True)
        safe_print("[DEBUG] Installation terminée avec succès.")
        return True
    except Exception as e:
        safe_print(f"[ERREUR] Impossible d'installer les dépendances : {e}")
        return False


# ==============================
#  LANCEMENT DE STREAMLIT
# ==============================

def launch_streamlit(app_path, port):
    """Lance Streamlit et affiche les logs"""
    safe_print("============================================================")
    safe_print("GESTION FINANCIERE LITTLE - MODE LITE")
    safe_print("============================================================")
    safe_print(f"[DEBUG] Application : {app_path}")
    safe_print(f"[DEBUG] Port choisi : {port}")

    python_exe = find_system_python()
    if not python_exe:
        safe_print("[ERREUR] Python non détecté, impossible de lancer Streamlit.")
        sys.exit(1)

    log_dir = Path(get_base_path()) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "streamlit_lite.log"

    cmd = [
        python_exe, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--logger.level", "info"
    ]
    safe_print(f"[DEBUG] Commande : {' '.join(cmd)}")

    with open(log_file, "w", encoding="utf-8") as f:
        process = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=get_base_path(),
            creationflags=0
        )

    safe_print("[DEBUG] Attente du démarrage du serveur Streamlit...")
    if wait_for_port(port, timeout=40):
        url = f"http://localhost:{port}"
        webbrowser.open(url)
        safe_print(f"[DEBUG] Streamlit lancé sur : {url}")
    else:
        safe_print("[ERREUR] Streamlit n'a pas démarré à temps.")
        sys.exit(1)

    process.wait()


# ==============================
#  MAIN
# ==============================

def main():
    safe_print("Démarrage de Gestion Financière Little (Lite)")
    setup_marker = Path(get_base_path()) / "setup.done"
    app_path = Path(get_base_path()) / "gestiolittle.py"

    # Étape 1 : Première installation
    if not setup_marker.exists():
        safe_print("[DEBUG] Première exécution — configuration initiale.")
        if check_and_install_deps():
            setup_marker.touch()
            safe_print("[DEBUG] Configuration terminée, relancez l'application.")
            input("Appuyez sur Entrée pour fermer...")
            sys.exit(0)
        else:
            safe_print("[ERREUR] Impossible de configurer l'environnement.")
            sys.exit(1)

    # Étape 2 : Vérification rapide
    if not check_and_install_deps():
        safe_print("[ERREUR] Échec de la vérification de l'environnement.")
        sys.exit(1)

    # Étape 3 : Lancement Streamlit
    port = find_free_port(8501)
    launch_streamlit(str(app_path), port)


# ==============================
#  EXECUTION
# ==============================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("[DEBUG] Interruption utilisateur.")
        sys.exit(0)
    except Exception as e:
        import traceback
        safe_print(f"[ERREUR] Exception critique : {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
