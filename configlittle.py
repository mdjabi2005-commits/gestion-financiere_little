# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 19:59:08 2025

@author: djabi
"""

import os
import sqlite3

def initialiser_dossiers():
    """Crée automatiquement tous les dossiers nécessaires sur le Bureau et initialise la base SQLite."""
    # 📁 Chemin principal sur le Bureau
    bureau = os.path.join(os.path.expanduser("~"), "Desktop", "Gestion_Financiere_Little")

    # 📂 Sous-dossiers
    dossiers = {
        "data": os.path.join(bureau, "data"),
        "tickets_a_scanner": os.path.join(bureau, "tickets_a_scanner"),
        "tickets_scannes": os.path.join(bureau, "tickets_scannes"),
        "revenus_a_traiter": os.path.join(bureau, "revenus_a_traiter"),
        "revenus_traités": os.path.join(bureau, "revenus_traités"),
    }

    # 🧱 Création automatique des dossiers
    for chemin in dossiers.values():
        os.makedirs(chemin, exist_ok=True)

    # 💾 Base de données SQLite
    db_path = os.path.join(dossiers["data"], "finances.db")

    # 🛠️ Création automatique de la base si elle n’existe pas
    if not os.path.exists(db_path):
        print("Création de la base de données SQLite...")

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Exemple minimal de tables (à adapter à ton schéma existant
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
            );
        """)

        conn.commit()
        conn.close()
        

    return dossiers, db_path


# ✅ Ces variables globales seront accessibles depuis le reste du projet
DOSSIERS, DB_PATH = initialiser_dossiers()

DATA_DIR = DOSSIERS["data"]
TO_SCAN_DIR = DOSSIERS["tickets_a_scanner"]
SORTED_DIR = DOSSIERS["tickets_scannes"]
REVENUS_A_TRAITER = DOSSIERS["revenus_a_traiter"]
REVENUS_TRAITES = DOSSIERS["revenus_traités"]

