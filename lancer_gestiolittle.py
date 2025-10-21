import os
import sys
import webbrowser
import subprocess
import time
import socket
import shutil


def wait_for_port(port, timeout=15):
    """Attend que le port du serveur Streamlit soit ouvert."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


if __name__ == "__main__":
    PORT = 8501

    # Cherche automatiquement streamlit.exe dans le PATH ou l’environnement courant
    streamlit_exe = shutil.which("streamlit")
    if not streamlit_exe:
        print("❌ Impossible de trouver streamlit.exe dans ton système.")
        input("Appuie sur Entrée pour fermer…")
        sys.exit(1)

    # Base du projet selon si c’est un exécutable ou non
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    
    tesseract_path = os.path.join(base_path, "tesseract", "tesseract.exe")

    # 🔍 Détection intelligente du script Streamlit
    possible_paths = [
        os.path.join(base_path, "gestiolittle.py"),                   # pour exécution directe
        os.path.join(os.path.dirname(base_path), "gestiolittle.py")   # pour l'exécutable dans dist/
    ]
    app_path = next((p for p in possible_paths if os.path.exists(p)), None)

    if not app_path:
        print("❌ Impossible de trouver gestiolittle.py")
        print("Cherché dans :", possible_paths)
        input("Appuie sur Entrée pour fermer…")
        sys.exit(1)

    # 🔹 Utilise PowerShell pour exécuter la commande
    cmd = [
        "powershell", "-Command",
        f'& "{streamlit_exe}" run "{app_path}" --server.port {PORT}'
    ]
    print("Lancement de Streamlit à partir de :", streamlit_exe)
    print("Application :", app_path)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Lis ce que renvoie Streamlit pendant quelques secondes
    time.sleep(5)
    try:
        out, err = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        out, err = "", ""
    print("=== SORTIE STDOUT ===")
    print(out)
    print("=== SORTIE ERREUR ===")
    print(err)

    # Attend que le serveur soit prêt avant d’ouvrir le navigateur
    if wait_for_port(PORT, timeout=25):
        print("✅ Serveur prêt ! Ouverture du navigateur…")
        webbrowser.open(f"http://localhost:{PORT}")
    else:
        print("⚠️ Streamlit ne s’est pas lancé correctement.")
        input("Appuie sur Entrée pour fermer…")

