#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestio V4 - Financial Management Application
Refactored modular version

@author: djabi
@version: 4.0 (Refactored)
@date: 2025-11-17
"""

import streamlit as st

# Initialize logging system FIRST (before any other imports)
from shared.logging_config import setup_logging
setup_logging()

# ==============================
# STREAMLIT CONFIGURATION
# ==============================
st.set_page_config(
    page_title="Gestio V4 - Gestion Financière",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# IMPORTS - Configuration
# ==============================
from config import (
    DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR,
    REVENUS_A_TRAITER, REVENUS_TRAITES
)

# ==============================
# IMPORTS - Database
# ==============================
from shared.database import (
    init_db,
    migrate_database_schema
)
from domains.transactions import TransactionRepository

# ==============================
# IMPORTS - UI
# ==============================
from shared.ui import load_all_styles, refresh_and_rerun, toast_success

# ==============================
# IMPORTS - Pages
# ==============================
from domains.home.pages.home import interface_accueil
from domains.transactions.pages.add import interface_transactions_simplifiee
from domains.transactions.pages.view import interface_voir_transactions
from domains.portfolio.pages.portefeuille import interface_portefeuille
from domains.ocr.pages.ocr_control_center import render_ocr_control_center

# ==============================
# LOGGING CONFIGURATION
# ==============================
from config.logging_config import setup_logging, get_logger

# Initialiser le système de logging
setup_logging(log_dir=DATA_DIR, level="INFO")
logger = get_logger(__name__)

# ==============================
# DATABASE INITIALIZATION
# ==============================
try:
    init_db()
    migrate_database_schema()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    st.error(f"⚠️ Erreur d'initialisation de la base de données : {e}")

# ==============================
# LOAD STYLES
# ==============================
load_all_styles()

# ==============================
# MAIN APPLICATION
# ==============================
def main():
    """Main application router."""
    try:
        # Sidebar navigation
        st.sidebar.title("💰 Gestio V4")
        st.sidebar.markdown("---")

        # Initialize session state for navigation
        if "requested_page" not in st.session_state:
            st.session_state.requested_page = None
        
        # Navigation menu
        pages = [
            "🏠 Accueil",
            "💳 Transactions",
            "📊 Voir Transactions",
            # "🌳 Arbre Financier",  # Removed - functionality moved to edit mode
            "💼 Portefeuille",
            "🔍 Tour de Contrôle OCR",  # Unified OCR page
        ]
        
        
        # Initialize radio state if not exists
        if "nav_radio" not in st.session_state:
            st.session_state.nav_radio = "🏠 Accueil"
        
        # Handle requested page change BEFORE creating widget
        if st.session_state.get("requested_page") and st.session_state.requested_page in pages:
            # Set default value before widget creation
            st.session_state.nav_radio = st.session_state.requested_page
            st.session_state.requested_page = None
        
        page = st.sidebar.radio(
            "Navigation",
            pages,
            key="nav_radio"
        )

        st.sidebar.markdown("---")

        # Info section
        st.sidebar.markdown("### ℹ️ Informations")
        st.sidebar.info(f"""
        **Version:** 4.0 (Refactored)

        **Base de données :**
        `{DB_PATH}`

        **Dossiers :**
        - Tickets : `{TO_SCAN_DIR}`
        - Revenus : `{REVENUS_A_TRAITER}`
        """)

        # Refresh button
        if st.sidebar.button("🔄 Rafraîchir", use_container_width=True):
            refresh_and_rerun()

        # Page routing
        if page == "🏠 Accueil":
            interface_accueil()

        elif page == "💳 Transactions":
            interface_transactions_simplifiee()

        elif page == "📊 Voir Transactions":
            interface_voir_transactions()  # Redirect to main transaction page
        
        # elif page == "🌳 Arbre Financier":
        #     interface_arbre_financier_dynamique()  # Disabled

        elif page == "💼 Portefeuille":
            interface_portefeuille()

        elif page == "🔍 Tour de Contrôle OCR":
            from domains.ocr.pages.tour_controle_simplifie import render_tour_controle_simple
            render_tour_controle_simple()

    except Exception as e:
        logger.critical(f"Application V4 failed: {e}", exc_info=True)
        st.error(f"ERREUR CRITIQUE: L'application V4 a rencontré une erreur: {e}")
        st.exception(e)

# ==============================
# APPLICATION ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
