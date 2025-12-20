"""
Portfolio Page Module

Main portfolio interface with tabs for management, analysis, and overview.

Refactored structure (V2):
- interface_portefeuille(): Main router creating 3 tabs
- portfolio/overview.py: Dashboard (read-only)
- portfolio/manage.py: Management hub (4 quadrants)
- portfolio/analyze.py: Analysis and forecasts
"""

import streamlit as st
import sqlite3
from config import DB_PATH
from shared.database import get_db_connection
from shared.services import backfill_recurrences_to_today
from domains.portfolio.pages.helpers import normalize_recurrence_column
from domains.portfolio.pages.overview import render_overview_tab
from domains.portfolio.pages.manage import render_manage_tab
from domains.portfolio.pages.analyze import render_analyze_tab


def interface_portefeuille() -> None:
    """
    Main portfolio interface - router function creating 3 tabs.

    Features:
    - Dashboard overview (read-only)
    - Centralized management hub
    - Financial analysis and forecasts

    Structure:
    - Tab 1: Vue d'ensemble (Dashboard)
    - Tab 2: Gérer (Management hub)
    - Tab 3: Analyse (Insights)

    Returns:
        None

    Note:
        This is the V2 refactored version with simplified navigation.
    """
    st.title("💼 Mon Portefeuille")

    # Initialiser les tables si elles n'existent pas
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table budgets par catégorie
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categorie TEXT UNIQUE NOT NULL,
            budget_mensuel REAL NOT NULL,
            date_creation TEXT,
            date_modification TEXT
        )
    """)

    # Table objectifs financiers (remplace les notes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objectifs_financiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_objectif TEXT NOT NULL,
            titre TEXT NOT NULL,
            montant_cible REAL,
            date_limite TEXT,
            periodicite TEXT,
            statut TEXT DEFAULT 'en_cours',
            date_creation TEXT,
            date_modification TEXT,
            date_atteint TEXT
        )
    """)

    # Table échéances pour gérer les prévisions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS echeances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            montant REAL NOT NULL,
            date_echeance TEXT NOT NULL,
            recurrence TEXT,
            statut TEXT DEFAULT 'active',
            type_echeance TEXT DEFAULT 'prévue',
            description TEXT,
            recurrence_id INTEGER,
            date_creation TEXT,
            date_modification TEXT
        )
    """)
    
    # Table récurrences (nouvelle)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            montant REAL NOT NULL,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            frequence TEXT NOT NULL,
            description TEXT,
            statut TEXT DEFAULT 'active',
            date_creation TEXT,
            date_modification TEXT
        )
    """)

    # Migration : Ajouter la colonne type_echeance si elle n'existe pas
    try:
        cursor.execute("SELECT type_echeance FROM echeances LIMIT 1")
    except:
        cursor.execute("ALTER TABLE echeances ADD COLUMN type_echeance TEXT DEFAULT 'prévue'")
        conn.commit()
    
    # Migration : Ajouter la colonne recurrence_id si elle n'existe pas
    try:
        cursor.execute("SELECT recurrence_id FROM echeances LIMIT 1")
    except:
        cursor.execute("ALTER TABLE echeances ADD COLUMN recurrence_id INTEGER")
        conn.commit()

    conn.commit()

    # Normaliser la colonne recurrence pour la cohérence des données
    normalize_recurrence_column()

    # Fermer la connexion avant les opérations qui ouvrent leur propre connexion
    conn.close()

    # Backfill les transactions récurrentes jusqu'à aujourd'hui
    # IMPORTANT: Cela doit être fait AVANT de charger les transactions
    backfill_recurrences_to_today(DB_PATH)
    
    # Synchroniser les récurrences vers les échéances futures
    from shared.services.recurrence_generation import refresh_echeances
    refresh_echeances()
    
    # Rouvrir la connexion pour les onglets
    conn = get_db_connection()
    cursor = conn.cursor()

    # Initialiser session state pour navigation
    if "portfolio_active_tab" not in st.session_state:
        st.session_state.portfolio_active_tab = 0

    # Navigation par boutons radio
    tab_options = ["📊 Vue d'ensemble", "⚙️ Gérer", "📈 Analyse"]
    
    # Utiliser on_change pour détecter les changements
    def on_tab_change():
        selected = st.session_state.portfolio_tab_selector
        st.session_state.portfolio_active_tab = tab_options.index(selected)
    
    selected_tab = st.radio(
        "Navigation",
        options=tab_options,
        index=st.session_state.portfolio_active_tab,
        horizontal=True,
        key="portfolio_tab_selector",
        label_visibility="collapsed",
        on_change=on_tab_change
    )
    
    st.markdown("---")

    # Afficher le contenu selon l'onglet sélectionné
    if st.session_state.portfolio_active_tab == 0:
        render_overview_tab(conn, cursor)
    elif st.session_state.portfolio_active_tab == 1:
        render_manage_tab(conn, cursor)
    elif st.session_state.portfolio_active_tab == 2:
        render_analyze_tab(conn, cursor)

    conn.close()
