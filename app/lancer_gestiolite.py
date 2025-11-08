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
    
    # Configuration de la page de code Windows
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except:
        pass
    
    # Configuration critique pour PyInstaller - FIX CONSOLE NOIRE
    try:
        # Si stdout/stderr sont None (cas PyInstaller avec --console)
        if sys.stdout is None or not hasattr(sys.stdout, 'write'):
            import io
            sys.stdout = io.TextIOWrapper(
                open('CONOUT$', 'wb', buffering=0),
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
        elif hasattr(sys.stdout, 'buffer'):
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
        
        if sys.stderr is None or not hasattr(sys.stderr, 'write'):
            import io
            sys.stderr = io.TextIOWrapper(
                open('CONOUT$', 'wb', buffering=0),
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
        elif hasattr(sys.stderr, 'buffer'):
            import codecs
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
    except Exception as e:
        # En dernier recours, créer un fichier de log
        try:
            log_file = os.path.join(
                os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__),
                "startup_error.log"
            )
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"Erreur configuration stdout: {e}\n")
                import traceback
                traceback.print_exc(file=f)
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
    
    # Symboles simples compatibles ASCII
    symbols = {
        "INFO": "[i]",
        "OK": "[+]",
        "ERROR": "[X]",
        "DEBUG": "[.]",
        "WARN": "[!]"
    }
    
    prefix = symbols.get(level, "[?]")
    formatted = f"[{timestamp}] {prefix} {text}"
    
    try:
        print(formatted, flush=True)
    except Exception as e:
        # Fallback absolu : fichier de log
        try:
            log_file = os.path.join(get_base_path(), "console.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{formatted}\n")
        except:
            pass

def show_system_info():
    """Affiche les informations système utiles"""
    print("\n" + "-"*60)
    print(" INFORMATIONS SYSTEME ".center(60))
    print("-"*60)
    safe_print(f"OS : {platform.system()} {platform.release()}", "INFO")
    safe_print(f"Machine : {platform.machine()}", "INFO")
    safe_print(f"Python : {sys.version.split()[0]}", "INFO")
    safe_print(f"Encodage : {sys.getdefaultencoding()}", "INFO")
    safe_print(f"Mode : {'Compile' if getattr(sys, 'frozen', False) else 'Script'}", "INFO")
    print("-"*60 + "\n")

# ==============================
#  FONCTIONS SYSTEME
# ==============================
def run_powershell_script(script_path):
    """Lance un script PowerShell"""
    try:
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"Erreur lors de l'exécution du script PowerShell : {e}", "ERROR")
        safe_print(f"Sortie : {e.stdout}", "ERROR")
        safe_print(f"Erreur : {e.stderr}", "ERROR")
        return False
    
    
def find_free_port(start=8501):
    """Trouve un port libre sur la machine"""
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
    """Attend qu'un port spécifique soit ouvert"""
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

    safe_print("Recherche du Python systeme...", "DEBUG")

    # Cherche python.exe dans le PATH
    python_cmd = shutil.which("python")
    if python_cmd:
        safe_print(f"Python trouve dans le PATH : {python_cmd}", "DEBUG")
        return python_cmd

    python3_cmd = shutil.which("python3")
    if python3_cmd:
        safe_print(f"Python3 trouve dans le PATH : {python3_cmd}", "DEBUG")
        return python3_cmd

    # Chemins standards Windows
    if sys.platform == "win32":
        common_paths = [
            r"C:\Python313\python.exe",
            r"C:\Python312\python.exe",
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                safe_print(f"Python trouve : {path}", "DEBUG")
                return path

        # Recherche dans le registre Windows
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
                                        safe_print(f"Python trouve dans le registre : {exe}", "DEBUG")
                                        return exe
                            except WindowsError:
                                break
                except WindowsError:
                    continue
        except ImportError:
            pass

    safe_print("Aucun Python trouve sur le systeme.", "ERROR")
    return None


# ==============================
#  VERIFICATION ET INSTALLATION DES DEPENDANCES
# ==============================
def check_and_install_deps():
    """Vérifie si Streamlit et les dépendances sont installées"""
    print("\n" + "-"*60)
    safe_print("Verification des dependances...", "INFO")
    
    python_exe = find_system_python()
    if not python_exe:
        safe_print("Python non trouve", "WARN")
        
        if sys.platform == "win32":
            install_script = os.path.join(get_base_path(), "install_and_run_windows.ps1")
            if os.path.exists(install_script):
                safe_print("Lancement de l'installation automatique...", "INFO")
                if run_powershell_script(install_script):
                    safe_print("Installation terminee. Veuillez relancer l'application.", "INFO")
                else:
                    safe_print("Erreur lors de l'installation automatique.", "ERROR")
            else:
                safe_print("Script d'installation manquant.", "ERROR")
        else:
            safe_print("Veuillez installer Python depuis python.org", "ERROR")
        
        input("Appuyez sur Entree pour fermer...")
        return False
    
    
    # Modules à vérifier (sans platform et threading qui sont natifs)
    packages = [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
        ("pytesseract", "pytesseract"),
        ("PIL", "Pillow"),
        ("dateutil", "python-dateutil"),
        ("cv2", "opencv-python-headless"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("pdfminer.six", "pdfminer.six"),
        ("requests", "requests")
    ]
    
    missing = []
    for import_name, pip_name in packages:
        result = subprocess.run(
            [python_exe, "-c", f"import {import_name.split('.')[0]}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            safe_print(f"X {pip_name} manquant", "WARN")
            missing.append(pip_name)
        else:
            safe_print(f"+ {pip_name} installe", "OK")
    
    if not missing:
        safe_print("Toutes les dependances sont installees", "OK")
        print("-"*60 + "\n")
        return True
    
    # Installation des paquets manquants
    print("\n" + "-"*60)
    safe_print(f"{len(missing)} dependance(s) a installer", "WARN")
    safe_print("Cela peut prendre quelques minutes...", "INFO")
    
    for pkg in missing:
        safe_print(f"Installation de {pkg}...", "INFO")
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", pkg, "--quiet"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            safe_print(f"+ {pkg} installe avec succes", "OK")
        else:
            safe_print(f"X Echec installation {pkg}", "ERROR")
            safe_print(f"Erreur: {result.stderr[:200]}", "ERROR")
            return False
    
    safe_print("Installation terminee !", "OK")
    print("-"*60 + "\n")
    return True


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
    safe_print(f"Port reseau : {port}", "INFO")
    safe_print(f"Repertoire : {get_base_path()}", "INFO")
    
    python_exe = find_system_python()
    if not python_exe:
        safe_print("Python non detecte sur le systeme", "ERROR")
        input("Appuyez sur Entree pour fermer...")
        sys.exit(1)
    
    safe_print(f"Python utilise : {python_exe}", "OK")
    
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
    safe_print("Demarrage du serveur Streamlit...", "INFO")
    
    # Ouvrir le fichier log en mode append
    log_handle = open(log_file, "w", encoding="utf-8")
    
    # Lancer le processus
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=get_base_path(),
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1  # Line buffered
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
                line_lower = line.lower()
                if "running on" in line_lower or "network url" in line_lower:
                    safe_print(line.strip(), "OK")
                elif "warning" in line_lower:
                    safe_print(line.strip(), "WARN")
                elif "error" in line_lower or "exception" in line_lower:
                    safe_print(line.strip(), "ERROR")
                elif "stopping" in line_lower or "shutdown" in line_lower:
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
        safe_print("APPLICATION PRETE", "OK")
        print("="*60)
        print(f"\n  URL locale    : {url}")
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"  URL reseau    : http://{local_ip}:{port}")
        except:
            pass
        print(f"  Logs          : {log_file}")
        print("  Etat          : En cours d'execution")
        
        print("\n" + "-"*60)
        print("  Actions disponibles :")
        print("  - Minimiser cette fenetre (l'app continue)")
        print("  - Ctrl+C pour arreter proprement")
        print("  - Fermer pour forcer l'arret")
        print("-"*60 + "\n")
        
        try:
            webbrowser.open(url)
            safe_print("Navigateur ouvert automatiquement", "OK")
        except Exception as e:
            safe_print(f"Impossible d'ouvrir le navigateur : {e}", "WARN")
            safe_print(f"Ouvrez manuellement : {url}", "INFO")
        
        # Afficher le statut périodiquement
        def status_monitor():
            count = 0
            while True:
                time.sleep(60)  # Toutes les minutes
                if process.poll() is None:
                    count += 1
                    if count % 5 == 0:  # Toutes les 5 minutes
                        safe_print(f"Application active depuis {count} minute(s)", "OK")
                else:
                    break
        
        status_thread = threading.Thread(target=status_monitor, daemon=True)
        status_thread.start()
        
    else:
        safe_print("Le serveur n'a pas demarre a temps", "ERROR")
        safe_print(f"Consultez les logs : {log_file}", "INFO")
        log_handle.close()
        input("Appuyez sur Entree pour fermer...")
        sys.exit(1)
    
    # Attendre la fin
    try:
        process.wait()
        safe_print("Application fermee normalement", "INFO")
    except KeyboardInterrupt:
        print("\n" + "-"*60)
        safe_print("Arret demande par l'utilisateur...", "WARN")
        process.terminate()
        time.sleep(2)
        if process.poll() is None:
            process.kill()
        safe_print("Application arretee", "OK")
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
    """Point d'entrée principal"""
    # Afficher les infos système dès le début
    show_system_info()
    
    safe_print("Demarrage de Gestion Financiere Little (Lite)", "INFO")
    
    base_path = get_base_path()
    setup_marker = Path(base_path) / "setup.done"
    app_path = Path(base_path) / "gestiolittle.py"
    
    # Vérifier que l'application existe
    if not app_path.exists():
        safe_print(f"ERREUR : Fichier gestiolittle.py introuvable dans {base_path}", "ERROR")
        safe_print("Contenu du repertoire :", "INFO")
        try:
            for item in os.listdir(base_path):
                safe_print(f"  - {item}", "DEBUG")
        except:
            pass
        input("Appuyez sur Entree pour fermer...")
        sys.exit(1)

    # Étape 1 : Première installation
    if not setup_marker.exists():
        safe_print("Premiere execution - configuration initiale.", "INFO")
        if check_and_install_deps():
            setup_marker.touch()
            safe_print("Configuration terminee !", "OK")
            safe_print("Veuillez relancer l'application.", "INFO")
            input("Appuyez sur Entree pour fermer...")
            sys.exit(0)
        else:
            safe_print("ERREUR : Impossible de configurer l'environnement.", "ERROR")
            input("Appuyez sur Entree pour fermer...")
            sys.exit(1)

    # Étape 2 : Vérification rapide
    if not check_and_install_deps():
        safe_print("ERREUR : Echec de la verification de l'environnement.", "ERROR")
        input("Appuyez sur Entree pour fermer...")
        sys.exit(1)

    # Étape 3 : Lancement Streamlit
    port = find_free_port(8501)
    safe_print(f"Port libre trouve : {port}", "OK")
    launch_streamlit_lite(str(app_path), port)


# ==============================
#  EXECUTION
# ==============================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("Interruption utilisateur.", "INFO")
        sys.exit(0)
    except Exception as e:
        import traceback
        safe_print(f"ERREUR CRITIQUE : {e}", "ERROR")
        print("\n" + "="*60)
        print("TRACE COMPLETE :")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        
        # Sauvegarder dans un fichier
        try:
            error_log = os.path.join(get_base_path(), "error.log")
            with open(error_log, "w", encoding="utf-8") as f:
                f.write(f"Erreur critique : {e}\n\n")
                traceback.print_exc(file=f)
            safe_print(f"Details sauvegardes dans : {error_log}", "INFO")
        except:
            pass
        
        input("\nAppuyez sur Entree pour fermer...")
        sys.exit(1)