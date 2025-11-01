# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 19:59:08 2025

@author: djabi
"""

import os
import sqlite3
import platform
import json
from pathlib import Path

def get_desktop_path():
    """
    Retourne le chemin du Bureau selon l'OS et la langue du système.
    Compatible Windows, Linux (plusieurs langues), macOS.
    """
    home = os.path.expanduser("~")
    system = platform.system()
    
    if system == "Windows":
        return os.path.join(home, "Desktop")
    
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Desktop")
    
    else:  # Linux
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
        
        print(f"Attention Bureau introuvable, utilisation du dossier personnel : {home}")
        return home

def get_config_path():
    """Retourne le chemin du fichier de configuration"""
    desktop = get_desktop_path()
    app_folder = os.path.join(desktop, "Gestion_Financiere_Little")
    return os.path.join(app_folder, "data", "config.json")

def load_config():
    """Charge la configuration depuis le fichier JSON"""
    config_path = get_config_path()
    default_config = {
        "sorted_dir": None,
        "revenus_traites_dir": None
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Attention Erreur lecture config : {e}")
    
    return default_config

def save_config(config):
    """Sauvegarde la configuration dans le fichier JSON"""
    config_path = get_config_path()
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Attention Erreur sauvegarde config : {e}")

def initialiser_dossiers():
    """Crée automatiquement tous les dossiers nécessaires"""
    desktop = get_desktop_path()
    
    #  Dossiers DIRECTEMENT sur le Bureau (toujours visibles)
    tickets_bureau = os.path.join(desktop, "Tickets à scanner")
    revenus_bureau = os.path.join(desktop, "Revenus à traiter")
    
    #  Dossier principal application
    app_folder = os.path.join(desktop, "Gestion_Financiere_Little")
    
    # Charger la configuration existante
    config = load_config()
    
    #  Dossiers internes (modifiables par l'utilisateur)
    sorted_dir = config.get("sorted_dir") or os.path.join(app_folder, "Tickets scannés")
    revenus_traites_dir = config.get("revenus_traites_dir") or os.path.join(app_folder, "Revenus traités")
    data_dir = os.path.join(app_folder, "data")
    
    #  Création automatique des dossiers
    dossiers = {
        "tickets_a_scanner": tickets_bureau,
        "revenus_a_traiter": revenus_bureau,
        "data": data_dir,
        "tickets_scannes": sorted_dir,
        "revenus_traités": revenus_traites_dir,
        "app_folder": app_folder
    }
    
    for nom, chemin in dossiers.items():
        os.makedirs(chemin, exist_ok=True)
        print(f"OK Dossier créé : {chemin}")
    
    #  Base de données SQLite
    db_path = os.path.join(data_dir, "finances.db")
    
    #  Création automatique de la base si elle n'existe pas
    if not os.path.exists(db_path):
        print(" Création de la base de données SQLite...")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
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
        print(f"OK Base de données créée : {db_path}")
    else:
        print(f"OK Base de données existante : {db_path}")
    
    return dossiers, db_path

# OK Initialisation globale
DOSSIERS, DB_PATH = initialiser_dossiers()

# OK Variables globales accessibles
DATA_DIR = DOSSIERS["data"]
TO_SCAN_DIR = DOSSIERS["tickets_a_scanner"]
SORTED_DIR = DOSSIERS["tickets_scannes"]
REVENUS_A_TRAITER = DOSSIERS["revenus_a_traiter"]
REVENUS_TRAITES = DOSSIERS["revenus_traités"]
APP_FOLDER = DOSSIERS["app_folder"]

print(f" Dossier principal : {APP_FOLDER}")
print(f" Tickets à scanner : {TO_SCAN_DIR}")
print(f" Revenus à traiter : {REVENUS_A_TRAITER}")
