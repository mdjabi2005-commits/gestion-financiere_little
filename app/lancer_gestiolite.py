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
import platform
import threading

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

def safe_print(text, level="INFO"):
    """Print sécurisé avec niveaux et formatage"""
    timestamp = time.strftime("%H:%M:%S")
    
    # Couleurs pour Windows (si supporté)
    colors = {
        "INFO": "",
        "OK": "[✓]",
        "ERROR": "[✗]",
        "DEBUG": "[•]",
        "WARN": "[!]"
    }
    
    prefix = colors.get(level, "")
    formatted = f"[{timestamp}] {prefix} {text}"
    
    try:
        print(formatted)
    except UnicodeEncodeError:
        text = formatted.encode("ascii", "replace").decode("ascii")
        print(text)
        
def show_system_info():
    """Affiche les informations système utiles"""
    print("\n" + "-"*60)
    print(" INFORMATIONS SYSTÈME ".center(60))
    print("-"*60)
    safe_print(f"OS : {platform.system()} {platform.release()}", "INFO")
    safe_print(f"Machine : {platform.machine()}", "INFO")
    safe_print(f"Python : {sys.version.split()[0]}", "INFO")
    safe_print(f"Encodage : {sys.getdefaultencoding()}", "INFO")
    print("-"*60 + "\n")

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
    print("\n" + "-"*60)
    safe_print("Vérification des dépendances...", "INFO")
    
    python_exe = find_system_python()
    if not python_exe:
        safe_print("Python non trouvé, installation requise", "ERROR")
        # ... reste du code
    
    packages = [
        "streamlit", "pandas", "pytesseract", "PIL",
        "dateutil", "cv2", "numpy", "matplotlib", 
        "pdfminer.six", "requests","platform","threading"
    ]
    
    missing = []
    for pkg in packages:
        result = subprocess.run(
            [python_exe, "-c", f"import {pkg.split('.')[0]}"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            safe_print(f"✗ {pkg} manquant", "WARN")
            missing.append(pkg)
        else:
            safe_print(f"✓ {pkg} installé", "OK")
    
    if not missing:
        safe_print("Toutes les dépendances sont installées", "OK")
        print("-"*60 + "\n")
        return True
    
    # Installation des manquants...

# ==============================
#  LANCEMENT DE STREAMLIT
# ==============================

def launch_streamlit_lite(app_path, port):
    """Lance Streamlit avec affichage informatif dans la console"""
    
    # En-tête clair
    print("\n" + "="*60)
    print(" GESTION FINANCIERE LITTLE - MODE LITE ".center(60))
    print("="*60)
    
    safe_print(f"Application : {os.path.basename(app_path)}", "INFO")
    safe_print(f"Port réseau : {port}", "INFO")
    safe_print(f"Répertoire : {get_base_path()}", "INFO")
    
    python_exe = find_system_python()
    if not python_exe:
        safe_print("Python non détecté sur le système", "ERROR")
        sys.exit(1)
    
    safe_print(f"Python utilisé : {python_exe}", "OK")
    
    log_dir = Path(get_base_path()) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "streamlit_lite.log"

    cmd = [
        python_exe, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--logger.level", "warning"
    ]
    
    print("\n" + "-"*60)
    safe_print("Démarrage du serveur Streamlit...", "INFO")
    
    # Ouvrir le fichier log en mode append
    log_handle = open(log_file, "w", encoding="utf-8")
    
    # Lancer le processus
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=get_base_path(),
        creationflags=0,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # Thread pour afficher les logs importants
    def monitor_output():
        try:
            for line in process.stdout:
                # Écrire dans le fichier si toujours ouvert
                try:
                    log_handle.write(line)
                    log_handle.flush()
                except (ValueError, OSError):
                    # Le fichier a été fermé, on arrête
                    break
                
                # Filtrer et afficher les lignes importantes
                if "Running on" in line or "Network URL" in line:
                    safe_print(line.strip(), "OK")
                elif "Warning" in line:
                    safe_print(line.strip(), "WARN")
                elif "Error" in line or "Exception" in line:
                    safe_print(line.strip(), "ERROR")
                elif "Stopping" in line or "Shutdown" in line:
                    safe_print(line.strip(), "INFO")
        except Exception as e:
            safe_print(f"Erreur monitoring : {e}", "WARN")
    
    monitor_thread = threading.Thread(target=monitor_output, daemon=True)
    monitor_thread.start()
    
    # Attendre que le port soit ouvert
    safe_print("Attente du serveur...", "INFO")
    if wait_for_port(port, timeout=40):
        url = f"http://localhost:{port}"
        print("\n" + "="*60)
        safe_print("✓ APPLICATION PRÊTE", "OK")
        print("="*60)
        print(f"\n  URL locale    : {url}")
        try:
            print(f"  URL réseau    : http://{socket.gethostbyname(socket.gethostname())}:{port}")
        except:
            pass
        print(f"  Logs          : {log_file}")
        print("  État          : En cours d'exécution")
        
        print("\n" + "-"*60)
        print("  Actions disponibles :")
        print("  • Minimiser cette fenêtre (l'app continue)")
        print("  • Ctrl+C pour arrêter proprement")
        print("  • Fermer pour forcer l'arrêt")
        print("-"*60 + "\n")
        
        webbrowser.open(url)
        safe_print("Navigateur ouvert automatiquement", "OK")
        
        # Afficher le statut périodiquement
        def status_monitor():
            while True:
                time.sleep(60)  # Toutes les minutes
                if process.poll() is None:
                    safe_print("Application toujours active", "OK")
                else:
                    break
        
        status_thread = threading.Thread(target=status_monitor, daemon=True)
        status_thread.start()
        
    else:
        safe_print("Le serveur n'a pas démarré à temps", "ERROR")
        safe_print(f"Consultez les logs : {log_file}", "INFO")
        log_handle.close()
        sys.exit(1)
    
    # Attendre la fin
    try:
        process.wait()
        safe_print("Application fermée normalement", "INFO")
    except KeyboardInterrupt:
        print("\n" + "-"*60)
        safe_print("Arrêt demandé par l'utilisateur...", "WARN")
        process.terminate()
        safe_print("Application arrêtée", "OK")
        print("-"*60)
    finally:
        # Fermer le fichier log proprement
        try:
            log_handle.close()
        except:
            pass

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
    launch_streamlit_lite(str(app_path), port)


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
