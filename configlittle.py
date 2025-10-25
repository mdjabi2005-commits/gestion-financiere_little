# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 19:59:08 2025

@author: djabi
"""

import os
import sqlite3
import platform

def get_desktop_path():
    """
    Retourne le chemin du Bureau selon l'OS et la langue du système.
    Compatible Windows, Linux (plusieurs langues), macOS.
    """
    home = os.path.expanduser("~")
    system = platform.system()
    
    if system == "Windows":
        # Sur Windows, c'est toujours "Desktop"
        return os.path.join(home, "Desktop")
    
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Desktop")
    
    else:  # Linux
        # Essaye plusieurs noms possibles selon la langue
        possible_names = [
            "Desktop",    # Anglais
            "Bureau",     # Français
            "Escritorio", # Espagnol
            "Área de Trabalho",  # Portugais
            "Skrivbord",  # Suédois
            "Schreibtisch",  # Allemand
            "デスクトップ"  # Japonais
        ]
        
        for name in possible_names:
            desktop = os.path.join(home, name)
            if os.path.exists(desktop):
                return desktop
        
        # Fallback : utilise xdg-user-dir si disponible (standard Linux)
        try:
            import subprocess
            result = subprocess.run(
                ["xdg-user-dir", "DESKTOP"],
                capture_output=True,
                text=True,
                check=True
            )
            desktop = result.stdout.strip()
            if desktop and os.path.exists(desktop):
                return desktop
        except Exception:
            pass
        
        # Dernier fallback : retourne le home (au pire)
        print(f"⚠️ Bureau introuvable, utilisation du dossier personnel : {home}")
        return home


def initialiser_dossiers():
    """Crée automatiquement tous les dossiers nécessaires sur le Bureau et initialise la base SQLite."""
    # 📁 Chemin principal sur le Bureau (compatible multi-OS)
    desktop = get_desktop_path()
    bureau = os.path.join(desktop, "Gestion_Financiere_Little")

    # 📂 Sous-dossiers
    dossiers = {
        "data": os.path.join(bureau, "data"),
        "tickets_a_scanner": os.path.join(bureau, "tickets_a_scanner"),
        "tickets_scannes": os.path.join(bureau, "tickets_scannes"),
        "revenus_a_traiter": os.path.join(bureau, "revenus_a_traiter"),
        "revenus_traités": os.path.join(bureau, "revenus_traités"),
    }

    # 🧱 Création automatique des dossiers
    for nom, chemin in dossiers.items():
        os.makedirs(chemin, exist_ok=True)
        print(f"✅ Dossier créé : {chemin}")

    # 💾 Base de données SQLite
    db_path = os.path.join(dossiers["data"], "finances.db")

    # 🛠️ Création automatique de la base si elle n'existe pas
    if not os.path.exists(db_path):
        print("📊 Création de la base de données SQLite...")

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Table transactions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                categorie TEXT,
                sous_categorie TEXT,
                description TEXT,
                montant REAL,
                date TEXT,
                source TEXT,
                recurrence TEXT,
                date_fin TEXT
            )
        """)

        # Table revenus
        cur.execute("""
            CREATE TABLE IF NOT EXISTS revenus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                montant REAL,
                date TEXT,
                source TEXT
            )
        """)

        conn.commit()
        conn.close()
        print(f"✅ Base de données créée : {db_path}")
    else:
        print(f"✅ Base de données existante : {db_path}")

    return dossiers, db_path


# ✅ Ces variables globales seront accessibles depuis le reste du projet
DOSSIERS, DB_PATH = initialiser_dossiers()

DATA_DIR = DOSSIERS["data"]
TO_SCAN_DIR = DOSSIERS["tickets_a_scanner"]
SORTED_DIR = DOSSIERS["tickets_scannes"]
REVENUS_A_TRAITER = DOSSIERS["revenus_a_traiter"]
REVENUS_TRAITES = DOSSIERS["revenus_traités"]

# Afficher le chemin pour debug
print(f"📁 Dossier principal : {os.path.dirname(DATA_DIR)}")
