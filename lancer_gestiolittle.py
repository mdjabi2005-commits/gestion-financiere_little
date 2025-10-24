import os
import sys
import subprocess
import webbrowser
import time
import socket
import shutil
import tempfile
import json
from pathlib import Path

def ouvrir_guide_installation():
    """Ouvre le guide d'installation si c'est le premier lancement"""
    
    # Chemin du fichier de configuration
    config_dir = Path.home() / ".gestiolittle"
    config_file = config_dir / "🧪 Guide d'Installation pour Testeurs Beta"
    
    # Créer le dossier de configuration s'il n'existe pas
    config_dir.mkdir(exist_ok=True)
    
    # Charger ou initialiser la configuration
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {"premier_lancement": True, "lancements": 0}
    
    # Incrémenter le compteur de lancements
    config["lancements"] = config.get("lancements", 0) + 1
    
    # Vérifier si c'est le premier lancement ou tous les 10 lancements
    premier_lancement = config.get("premier_lancement", True)
    lancements = config.get("lancements", 0)
    
    # Chemin du guide d'installation
    guide_path = Path(__file__).parent / "GUIDE_INSTALLATION.md"
    
    # Ouvrir le guide dans les cas suivants :
    ouvrir_guide = False
    
    if premier_lancement:
        print("🎉 Premier lancement - Ouverture du guide d'installation...")
        ouvrir_guide = True
        config["premier_lancement"] = False
    
    elif lancements % 10 == 0:  # Tous les 10 lancements
        print("📖 Rappel - Ouverture du guide d'installation...")
        ouvrir_guide = True
    
    # Sauvegarder la configuration
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    # Ouvrir le guide si nécessaire
    if ouvrir_guide and guide_path.exists():
        try:
            if sys.platform == "win32":
                # Windows
                os.startfile(str(guide_path))
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(["open", str(guide_path)])
            else:
                # Linux
                subprocess.run(["xdg-open", str(guide_path)])
            print("📚 Guide d'installation ouvert !")
            # Attendre un peu que le guide s'ouvre
            time.sleep(2)
        except Exception as e:
            print(f"❌ Impossible d'ouvrir le guide: {e}")

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
        # Si compilé avec PyInstaller, utilise le dossier temporaire d'extraction
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
    print("\n💡 Le fichier gestiolittle.py doit être dans le même dossier que l'exécutable.")
    input("\nAppuie sur Entrée pour fermer…")
    sys.exit(1)

def launch_streamlit(app_path, port=8501):
    """Lance Streamlit proprement et ouvre le navigateur quand le serveur est prêt."""
    streamlit_exe = shutil.which("streamlit")

    if not streamlit_exe:
        print("❌ Streamlit introuvable ! Vérifie que Streamlit est bien installé.")
        print("Essaie : pip install streamlit")
        input("Appuie sur Entrée pour fermer…")
        sys.exit(1)

    # Commande adaptée selon l'OS
    if sys.platform == "win32":
        cmd = [
            "powershell", "-Command",
            f'& "{streamlit_exe}" run "{app_path}" --server.port {port}'
        ]
    else:
        cmd = [streamlit_exe, "run", app_path, "--server.port", str(port)]

    print(f"Lancement de Streamlit à partir de : {streamlit_exe}")
    print(f"Application : {app_path}")

    # Lance Streamlit en tâche de fond
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Attendre que le serveur démarre
    if wait_for_port(port, timeout=30):
        print("✅ Serveur prêt ! Ouverture du navigateur…")
        webbrowser.open(f"http://localhost:{port}")
    else:
        print("⚠️ Le serveur Streamlit ne s'est pas lancé correctement.")
        print("Essaye de lancer depuis le terminal pour voir les logs :")
        print(f"   streamlit run \"{app_path}\" --server.port {port}")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

    return process

def main():
    print("🚀 Démarrage de Gestion Financière Little…")

    # 1. Ouvrir le guide d'installation si nécessaire
    ouvrir_guide_installation()

    # 2. Lancer l'application Streamlit normale
    base_path = get_base_path()
    app_path = find_app_path(base_path)
    launch_streamlit(app_path)

    print("✅ Application lancée avec succès.")
    print("💡 Ferme cette fenêtre pour arrêter l'application.")
    
    # Garde la fenêtre ouverte
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application...")
        sys.exit(0)

if __name__ == "__main__":
    main()