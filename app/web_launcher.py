"""
Gestio V4 - Web Launcher
Interface web customisable pour lancer l'application
"""

import os
import sys
import json
import subprocess
import webbrowser
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import requests

# Helper pour PyInstaller
def get_base_path():
    """Retourne le chemin de base (gère PyInstaller frozen apps)"""
    if getattr(sys, 'frozen', False):
        # Mode PyInstaller : utiliser _MEIPASS pour les fichiers internes
        return Path(sys._MEIPASS)
    else:
        # Mode normal : utiliser le dossier du script
        return Path(__file__).parent

app = Flask(__name__, 
            template_folder=str(get_base_path() / "templates"))

# Configuration
SCRIPT_DIR = get_base_path()
CONFIG_FILE = SCRIPT_DIR / "launcher_config.json"
GITHUB_REPO = "mdjabi2005-commits/gestion-financiere_little"

def load_config():
    """Charge la configuration du launcher"""
    default_config = {
        "title": "Gestio V4",
        "subtitle": "Gestion Financière Personnelle",
        "primary_color": "#4F46E5",
        "secondary_color": "#818CF8",
        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "logo_url": "",
        "docs_url": "https://mdjabi2005-commits.github.io/gestion-financiere_little",
        "github_url": f"https://github.com/{GITHUB_REPO}"
    }
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            default_config.update(config)
    
    return default_config

def get_version():
    """Lit la version actuelle"""
    version_file = SCRIPT_DIR.parent / "version.txt"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.4.0"

@app.route('/')
def index():
    """Page principale"""
    config = load_config()
    version = get_version()
    return render_template('launcher.html', config=config, version=version)

@app.route('/api/launch', methods=['POST'])
def launch_app():
    """Lance l'application Streamlit"""
    try:
        main_path = SCRIPT_DIR / "main.py"
        subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", str(main_path),
            "--server.port=8501"
        ])
        return jsonify({"success": True, "url": "http://localhost:8501"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/check-update', methods=['GET'])
def check_update():
    """Vérifie les mises à jour"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip('v')
            current_version = get_version()
            
            return jsonify({
                "has_update": latest_version != current_version,
                "latest_version": latest_version,
                "current_version": current_version,
                "download_url": data.get("html_url")
            })
    except:
        pass
    
    return jsonify({"has_update": False})

@app.route('/api/open-url', methods=['POST'])
def open_url():
    """Ouvre une URL dans le navigateur"""
    data = request.json
    url = data.get('url')
    if url:
        webbrowser.open(url)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

if __name__ == '__main__':
    # Ouvrir le navigateur automatiquement
    webbrowser.open('http://localhost:5555')
    
    # Lancer le serveur Flask
    print("🚀 Gestio V4 Launcher - http://localhost:5555")
    print("⚠️  Appuyez sur Ctrl+C pour arrêter")
    app.run(host='localhost', port=5555, debug=False)
