import os
import sys
import subprocess
import webbrowser
import time
import socket
import shutil

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
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_app_path(base_path):
    """Cherche le fichier gestiolittle.py à partir de l’emplacement courant."""
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
        print("   -", p)
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

    cmd = [
        "powershell", "-Command",
        f'& "{streamlit_exe}" run "{app_path}" --server.port {port}'
    ]

    print(f"Lancement de Streamlit à partir de : {streamlit_exe}")
    print(f"Application : {app_path}")

    # Lance Streamlit en tâche de fond
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Attendre que le serveur démarre
    if wait_for_port(port, timeout=30):
        print("✅ Serveur prêt ! Ouverture du navigateur…")
        webbrowser.open(f"http://localhost:{port}")
    else:
        print("⚠️ Le serveur Streamlit ne s’est pas lancé correctement.")
        print("Essaye de lancer depuis le terminal pour voir les logs :")
        print(f"   streamlit run \"{app_path}\" --server.port {port}")
        input("\nAppuie sur Entrée pour fermer…")
        sys.exit(1)

    return process


def main():
    print("🚀 Démarrage de Gestion Financière Little…")

    base_path = get_base_path()
    app_path = find_app_path(base_path)
    launch_streamlit(app_path)

    print("✅ Application lancée avec succès.")
    time.sleep(2)


if __name__ == "__main__":
    main()
