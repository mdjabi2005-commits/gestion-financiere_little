"""
Gestio V4 - GUI Launcher (Tkinter)
Interface native sans navigateur
"""

import os
import sys
import json
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import requests
import threading

# Helper pour PyInstaller
def get_base_path():
    """Retourne le chemin de base (gère PyInstaller frozen apps)"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent

def get_exe_directory():
    """Retourne le dossier de l'exécutable (pour fichiers externes)"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent

# Configuration
SCRIPT_DIR = get_base_path()
CONFIG_FILE = SCRIPT_DIR / "launcher_config.json"
GITHUB_REPO = "mdjabi2005-commits/gestion-financiere_little"

def load_config():
    """Charge la configuration du launcher"""
    default_config = {
        "title": "Gestio V4",
        "subtitle": "Gestion Financière Personnelle",
        "docs_url": "https://mdjabi2005-commits.github.io/gestion-financiere_little",
        "github_url": f"https://github.com/{GITHUB_REPO}"
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
        except:
            pass
    
    return default_config

def get_version():
    """Lit la version actuelle"""
    version_file = SCRIPT_DIR.parent / "version.txt"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.4.0"

class LauncherGUI:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.version = get_version()
        
        # Configuration fenêtre
        self.root.title(f"{self.config['title']} - Launcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs modernes
        bg_color = "#667eea"
        fg_color = "white"
        
        self.root.configure(bg=bg_color)
        
        # Header
        header = tk.Frame(root, bg=bg_color)
        header.pack(pady=30, fill='x')
        
        title = tk.Label(
            header, 
            text=f"💰 {self.config['title']}", 
            font=("Segoe UI", 24, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        title.pack()
        
        subtitle = tk.Label(
            header,
            text=self.config['subtitle'],
            font=("Segoe UI", 12),
            bg=bg_color,
            fg=fg_color
        )
        subtitle.pack()
        
        version_label = tk.Label(
            header,
            text=f"Version {self.version}",
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=fg_color
        )
        version_label.pack(pady=5)
        
        # Update banner (caché par défaut)
        self.update_frame = tk.Frame(root, bg="#FCD34D", height=50)
        self.update_label = tk.Label(
            self.update_frame,
            text="🎉 Nouvelle version disponible !",
            font=("Segoe UI", 10, "bold"),
            bg="#FCD34D",
            fg="#78350F"
        )
        self.update_label.pack(side='left', padx=20, pady=10)
        
        self.update_btn = tk.Button(
            self.update_frame,
            text="Télécharger",
            command=self.open_update,
            bg="#78350F",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            cursor='hand2'
        )
        self.update_btn.pack(side='right', padx=20, pady=10)
        
        # Boutons principaux
        button_frame = tk.Frame(root, bg=bg_color)
        button_frame.pack(pady=20)
        
        self.launch_btn = tk.Button(
            button_frame,
            text="🚀 Lancer l'application",
            command=self.launch_app,
            bg="#4F46E5",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=25,
            height=2,
            relief='flat',
            cursor='hand2'
        )
        self.launch_btn.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(
            root,
            text="",
            font=("Segoe UI", 9),
            bg=bg_color,
            fg=fg_color
        )
        self.status_label.pack(pady=10)
        
        # Liens en bas
        links_frame = tk.Frame(root, bg=bg_color)
        links_frame.pack(side='bottom', pady=20)
        
        links = [
            ("📖 Documentation", lambda: webbrowser.open(self.config['docs_url'])),
            ("🔍 Vérifier MAJ", self.check_update),
            ("💬 GitHub", lambda: webbrowser.open(self.config['github_url']))
        ]
        
        for text, command in links:
            btn = tk.Button(
                links_frame,
                text=text,
                command=command,
                bg=bg_color,
                fg=fg_color,
                font=("Segoe UI", 9, "underline"),
                relief='flat',
                cursor='hand2',
                borderwidth=0
            )
            btn.pack(side='left', padx=10)
        
        # Vérifier updates au démarrage (en arrière-plan)
        threading.Thread(target=self.check_update, daemon=True).start()
    
    def launch_app(self):
        """Lance l'application Streamlit"""
        try:
            self.status_label.config(text="⏳ Lancement de l'application...")
            self.launch_btn.config(state='disabled')
            
            main_path = SCRIPT_DIR / "main.py"
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(main_path),
                "--server.port=8501"
            ])
            
            self.status_label.config(text="✅ Application lancée sur http://localhost:8501")
            
            # Ouvrir navigateur
            webbrowser.open("http://localhost:8501")
            
            # Réactiver bouton après 2s
            self.root.after(2000, lambda: self.launch_btn.config(state='normal'))
            
        except Exception as e:
            self.status_label.config(text=f"❌ Erreur : {str(e)}")
            self.launch_btn.config(state='normal')
            messagebox.showerror("Erreur", f"Impossible de lancer l'application:\n{str(e)}")
    
    def check_update(self):
        """Vérifie les mises à jour sur GitHub"""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip('v')
                
                if latest_version and latest_version != self.version:
                    self.update_url = data.get("html_url")
                    self.update_frame.pack(fill='x', after=self.root.winfo_children()[0])
                    self.update_label.config(text=f"🎉 Version {latest_version} disponible !")
        except:
            pass
    
    def open_update(self):
        """Ouvre la page de téléchargement"""
        if hasattr(self, 'update_url'):
            webbrowser.open(self.update_url)

def main():
    root = tk.Tk()
    app = LauncherGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
