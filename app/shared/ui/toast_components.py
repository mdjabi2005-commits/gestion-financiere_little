"""Reusable UI components for the application.

This module contains toast notifications, badges, and transaction display components.
"""

import os
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from PIL import Image

from shared.services import trouver_fichiers_associes

logger = logging.getLogger(__name__)


# ==============================
# 🔔 TOAST NOTIFICATIONS
# ==============================

def show_toast(message: str, toast_type: str = "success", duration: int = 3000) -> None:
    """
    Display a professional toast notification.

    Args:
        message: Message to display
        toast_type: Type of toast - 'success', 'warning', 'error'
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> show_toast("Transaction saved!", "success", 3000)
        >>> show_toast("Warning: duplicate detected", "warning", 5000)
    """
    # Define color and icon based on type
    toast_config = {
        "success": {"color": "#10b981", "icon": "✅", "bg_light": "#d1fae5"},
        "warning": {"color": "#f59e0b", "icon": "⚠️", "bg_light": "#fef3c7"},
        "error": {"color": "#ef4444", "icon": "❌", "bg_light": "#fee2e2"}
    }

    config = toast_config.get(toast_type, toast_config["success"])

    components.html(f"""
        <div style="
            position:fixed;
            bottom:30px;right:30px;
            background:linear-gradient(135deg, {config['color']} 0%, {config['bg_light']} 100%);
            color:#1f2937;
            padding:12px 24px;
            border-radius:12px;
            font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            font-weight:600;
            box-shadow:0 4px 20px rgba(0,0,0,0.15);
            border-left:4px solid {config['color']};
            z-index:9999;
            animation:slideIn 0.3s ease-out, fadeOut {duration/1000}s {(duration-1000)/1000}s forwards;">
            <span style="font-size:18px;margin-right:8px;">{config['icon']}</span>
            {message}
        </div>
        <style>
        @keyframes slideIn {{
          from {{
            transform: translateX(400px);
            opacity: 0;
          }}
          to {{
            transform: translateX(0);
            opacity: 1;
          }}
        }}
        @keyframes fadeOut {{
          0% {{opacity:1;}}
          100% {{opacity:0;visibility:hidden;}}
        }}
        </style>
    """, height=80)


def toast_success(message: str, duration: int = 3000) -> None:
    """
    Display a success toast notification.

    Args:
        message: Success message to display
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> toast_success("Transaction successfully saved!")
    """
    show_toast(message, "success", duration)


def toast_warning(message: str, duration: int = 3000) -> None:
    """
    Display a warning toast notification.

    Args:
        message: Warning message to display
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> toast_warning("Duplicate transaction detected")
    """
    show_toast(message, "warning", duration)


def toast_error(message: str, duration: int = 3000) -> None:
    """
    Display an error toast notification.

    Args:
        message: Error message to display
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> toast_error("Failed to save transaction")
    """
    show_toast(message, "error", duration)


# ==============================
# 🏷️ BADGE COMPONENTS
# ==============================

def get_badge_html(transaction: Dict[str, Any]) -> str:
    """
    Generate HTML badge for a transaction based on its source.

    Args:
        transaction: Transaction dictionary with 'source' and 'type' keys

    Returns:
        HTML string for the badge with appropriate styling

    Example:
        >>> tx = {'source': 'OCR', 'type': 'dépense'}
        >>> badge = get_badge_html(tx)
        >>> '🧾 Ticket' in badge
        True
    """
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")

    if source == "OCR":
        badge = "🧾 Ticket"
        couleur = "#1f77b4"
        emoji = "🧾"
    elif source == "PDF":
        if type_transaction == "revenu":
            badge = "💼 Bulletin"
            couleur = "#2ca02c"
            emoji = "💼"
        else:
            badge = "📄 Facture"
            couleur = "#ff7f0e"
            emoji = "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        badge = "📝 Manuel"
        couleur = "#7f7f7f"
        emoji = "📝"
    else:
        badge = "📎 Autre"
        couleur = "#9467bd"
        emoji = "📎"

    return f"<span style='background-color: {couleur}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: bold;'>{emoji} {badge}</span>"


def get_badge_icon(transaction: Dict[str, Any]) -> str:
    """
    Get the icon emoji for a transaction based on its source.

    Args:
        transaction: Transaction dictionary with 'source' and 'type' keys

    Returns:
        Emoji string representing the transaction source

    Example:
        >>> tx = {'source': 'OCR', 'type': 'dépense'}
        >>> icon = get_badge_icon(tx)
        >>> icon
        '🧾'
    """
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")

    if source == "OCR":
        return "🧾"
    elif source == "PDF":
        return "💼" if type_transaction == "revenu" else "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        return "📝"
    else:
        return "📎"


# ==============================
# 📋 TRANSACTION DISPLAY COMPONENTS
# ==============================

def afficher_carte_transaction(transaction: Dict[str, Any], idx: Optional[int] = None) -> None:
    """
    Display a transaction card with details and associated documents.

    Creates a two-column layout showing transaction details on the left
    and amount/documents on the right.

    Args:
        transaction: Transaction dictionary with keys:
            - categorie: Category name
            - sous_categorie: Subcategory name
            - date: Transaction date
            - description: Optional description
            - recurrence: Optional recurrence pattern
            - type: 'revenu' or 'dépense'
            - montant: Amount
            - source: Transaction source (OCR, PDF, etc.)
        idx: Optional index for the transaction (not used but kept for compatibility)

    Example:
        >>> tx = {
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Restaurant',
        ...     'date': '2025-01-15',
        ...     'type': 'dépense',
        ...     'montant': 45.50,
        ...     'source': 'OCR'
        ... }
        >>> afficher_carte_transaction(tx)
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**Catégorie :** {transaction['categorie']}")
        st.write(f"**Sous-catégorie :** {transaction['sous_categorie']}")
        st.write(f"**Date :** {transaction['date']}")

        if transaction.get('description'):
            st.write(f"**Description :** {transaction['description']}")

        if transaction.get('recurrence'):
            st.write(f"**Récurrence :** {transaction['recurrence']}")

    with col2:
        montant_color = "green" if transaction['type'] == 'revenu' else "red"
        montant_prefix = "+" if transaction['type'] == 'revenu' else "-"
        st.markdown(
            f"<h2 style='color: {montant_color}; text-align: center;'>"
            f"{montant_prefix}{transaction['montant']:.2f} €</h2>",
            unsafe_allow_html=True
        )

        # Display documents automatically if available
        if transaction['source'] in ['OCR', 'PDF']:
            st.markdown("---")
            st.markdown("**📎 Documents :**")
            # Handle both dict and Series
            if hasattr(transaction, 'to_dict'):
                afficher_documents_associes(transaction.to_dict())
            else:
                afficher_documents_associes(transaction)


def afficher_documents_associes(transaction: Dict[str, Any], context: Optional[str] = None) -> None:
    """
    Display documents associated with a transaction in an enhanced format.

    Shows images and PDFs in tabs, with OCR text extraction capabilities
    for images and text preview for PDFs.

    Args:
        transaction: Transaction dictionary with keys:
            - categorie: Category name
            - sous_categorie: Subcategory name
            - date: Transaction date
            - source: Transaction source
            - type: Transaction type

        context: Optional unique context identifier to distinguish between
                multiple renders of the same transaction on the same page.
                Used for generating unique Streamlit widget keys.

    Side effects:
        - Displays images using st.image()
        - Shows PDF download buttons
        - May display expanders with OCR text or PDF content

    Example:
        >>> tx = {
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Restaurant',
        ...     'date': '2025-01-15',
        ...     'source': 'OCR',
        ...     'type': 'dépense'
        ... }
        >>> afficher_documents_associes(tx)
        >>> afficher_documents_associes(tx, context='detail_view')
    """
    fichiers = trouver_fichiers_associes(transaction)

    # If no context provided, generate one from transaction properties
    if not context:
        # Create a unique context from transaction date, category, subcategory, AND amount
        # The amount is crucial to differentiate transactions with same metadata
        tx_date = str(transaction.get("date", ""))
        tx_cat = str(transaction.get("categorie", ""))
        tx_subcat = str(transaction.get("sous_categorie", ""))
        tx_montant = str(transaction.get("montant", "0"))
        context = f"{tx_date}_{tx_cat}_{tx_subcat}_{tx_montant}"

    if not fichiers:
        source = transaction.get("source", "")
        type_transaction = transaction.get("type", "")

        if source == "OCR":
            st.warning("🧾 Aucun ticket de caisse trouvé dans les dossiers")
        elif source == "PDF":
            if type_transaction == "revenu":
                st.warning("💼 Aucun bulletin de paie trouvé")
            else:
                st.warning("📄 Aucune facture trouvée")
        else:
            st.info("📝 Aucun document associé")
        return

    # Display each file in tabs
    tabs = st.tabs([f"Document {i+1}" for i in range(len(fichiers))])

    for i, (tab, fichier) in enumerate(zip(tabs, fichiers)):
        with tab:
            nom_fichier = os.path.basename(fichier)

            if fichier.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Display the image
                try:
                    image = Image.open(fichier)
                    st.image(image, caption=f"🧾 {nom_fichier}", use_column_width=True)

                    # Optional: Re-OCR
                    with st.expander("🔍 Analyser le texte"):
                        # Import here to avoid circular dependency
                        try:
                            from domains.ocr import full_ocr
                            texte_ocr = full_ocr(fichier, show_ticket=False)
                            st.text_area("Texte du ticket:", texte_ocr, height=150)
                        except ImportError:
                            st.warning("OCR module not available")

                except Exception as e:
                    toast_error(f"Impossible d'afficher l'image: {e}")

            elif fichier.lower().endswith('.pdf'):
                # Display PDF info
                st.success(f"📄 **{nom_fichier}**")

                # Extract text automatically
                try:
                    # Import here to avoid circular dependency
                    try:
                        from domains.ocr.parsers_OLD_BACKUP import extract_text_from_pdf
                        texte_pdf = extract_text_from_pdf(fichier)
                        if texte_pdf.strip():
                            with st.expander("📖 Contenu du document"):
                                apercu = texte_pdf[:2000] + "..." if len(texte_pdf) > 2000 else texte_pdf
                                st.text_area("Extrait:", apercu, height=200)
                    except ImportError:
                        st.info("📄 Document PDF (extraction de texte non disponible)")
                except Exception:
                    st.info("📄 Document PDF (contenu non extrait)")

                # Download button
                with open(fichier, "rb") as f:
                    file_hash = hashlib.md5(fichier.encode()).hexdigest()[:8]
                    # Create context-aware key to avoid duplicates
                    context_suffix = f"_{context}" if context else ""
                    # Add timestamp to guarantee absolute uniqueness even if all metadata is identical
                    import time
                    unique_id = str(int(time.time() * 1000000))[-8:]  # Last 8 digits of microsecond timestamp
                    st.download_button(
                        label="⬇️ Télécharger le document",
                        data=f.read(),
                        file_name=nom_fichier,
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"dl_{file_hash}_{i}{context_suffix}_{unique_id}"
                    )


# ==============================
# 💰 CATEGORY VISUALIZATION & FILTERING SYSTEM
# ==============================
# Unified system with proportional bubbles + chips for category management

import pandas as pd
import math
import time
from typing import List, Dict, Any

@st.cache_data(ttl=300)
def calculate_category_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics for each category (amount, percentage, count).

    Args:
        df: Transaction DataFrame

    Returns:
        DataFrame with columns: [categorie, montant, pct, count, type_predominant]
    """
    if df.empty:
        return pd.DataFrame(columns=['categorie', 'montant', 'pct', 'count', 'type_predominant'])

    df_copy = df.copy()
    df_copy['type'] = df_copy['type'].str.lower().str.strip()

    stats = df_copy.groupby('categorie', as_index=False).agg({
        'montant': ['sum', 'count'],
        'type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'dépense'
    }).reset_index(drop=True)

    stats.columns = ['categorie', 'montant', 'count', 'type_predominant']
    stats['montant'] = stats['montant'].round(2)

    total = stats['montant'].sum()
    stats['pct'] = (stats['montant'] / total * 100).round(1)

    return stats.sort_values('montant', ascending=False).reset_index(drop=True)


# ==============================
# ==============================
# 🫧 BUBBLE NAVIGATION COMPONENT - Compact & Fluide
# ==============================

def render_category_management(df: pd.DataFrame) -> pd.DataFrame:
    """
    Navigation fractal avec Sierpinski triangles interactifs.

    Remplace le système de bulles par une visualisation Sierpinski triangle.
    Les utilisateurs cliquent sur les nœuds pour filtrer les transactions.
    """
    from shared.services import build_fractal_hierarchy

    # État de navigation fractal
    if 'fractal_nav_level' not in st.session_state:
        st.session_state.fractal_nav_level = 'root'  # root, type, category
    if 'fractal_selected_type' not in st.session_state:
        st.session_state.fractal_selected_type = None
    if 'fractal_selected_category' not in st.session_state:
        st.session_state.fractal_selected_category = None

    st.subheader("🔺 Explorez par Triangles Fractals")

    # Construire la hiérarchie fractal
    """Display filtered transactions with sunburst navigation."""
    from shared.services import build_fractal_hierarchy
    from shared.ui.sunburst_navigation import sunburst_navigation
    
    hierarchy = build_fractal_hierarchy()
    
    if hierarchy:
        sunburst_navigation(hierarchy, key="sunburst_transactions_view", height=600)

    st.info("💡 Cliquez sur les triangles pour zoomer. Les transactions se filtrent selon votre sélection.")
    st.markdown("---")

    # === NAVIGATION MANUELLE PAR NIVEAUX ===
    # Afficher les niveaux de sélection pour permettre le filtrage

    # NIVEAU 1: Sélection du type (Revenus / Dépenses)
    if st.session_state.fractal_nav_level == 'root':
        st.markdown("### 🔍 Étape 1 : Choisir le type")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💼 Revenus", use_container_width=True, key="btn_type_revenus"):
                st.session_state.fractal_selected_type = 'revenu'
                st.session_state.fractal_nav_level = 'type'
                st.rerun()

        with col2:
            if st.button("🛒 Dépenses", use_container_width=True, key="btn_type_depenses"):
                st.session_state.fractal_selected_type = 'dépense'
                st.session_state.fractal_nav_level = 'type'
                st.rerun()

        return df

    # NIVEAU 2: Sélection de la catégorie
    elif st.session_state.fractal_nav_level == 'type':
        col1, col2 = st.columns([1, 10])
        with col1:
            if st.button("← Retour", key="fractal_back_to_root"):
                st.session_state.fractal_nav_level = 'root'
                st.session_state.fractal_selected_type = None
                st.session_state.fractal_selected_category = None
                st.rerun()

        type_label = "Revenus" if st.session_state.fractal_selected_type == 'revenu' else "Dépenses"
        st.markdown(f"### 🔍 Étape 2 : Choisir une catégorie dans {type_label}")

        # Récupérer les catégories pour ce type
        df_filtered = df[df['type'] == st.session_state.fractal_selected_type]
        categories = df_filtered['categorie'].unique()

        # Afficher les catégories en grille
        cols = st.columns(3)
        for idx, category in enumerate(sorted(categories)):
            with cols[idx % 3]:
                cat_total = df_filtered[df_filtered['categorie'] == category]['montant'].sum()
                cat_count = len(df_filtered[df_filtered['categorie'] == category])

                if st.button(f"{category}\n{cat_total:.0f}€ ({cat_count})",
                            use_container_width=True,
                            key=f"btn_cat_{category}"):
                    st.session_state.fractal_selected_category = category
                    st.session_state.fractal_nav_level = 'category'
                    st.rerun()

        return df_filtered

    # NIVEAU 3: Affichage des transactions pour la catégorie sélectionnée
    elif st.session_state.fractal_nav_level == 'category':
        col1, col2 = st.columns([1, 10])
        with col1:
            if st.button("← Retour", key="fractal_back_to_type"):
                st.session_state.fractal_nav_level = 'type'
                st.session_state.fractal_selected_category = None
                st.rerun()

        type_label = "Revenus" if st.session_state.fractal_selected_type == 'revenu' else "Dépenses"
        st.markdown(f"### 🔍 Transactions : {type_label} → {st.session_state.fractal_selected_category}")

        # Filtrer par type et catégorie
        df_filtered = df[
            (df['type'] == st.session_state.fractal_selected_type) &
            (df['categorie'] == st.session_state.fractal_selected_category)
        ]

        if not df_filtered.empty:
            # Afficher les métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Montant", f"{df_filtered['montant'].sum():.0f}€")
            with col2:
                st.metric("Transactions", len(df_filtered))
            with col3:
                st.metric("Sous-catégories", df_filtered['sous_categorie'].nunique())

            st.markdown("---")
            return df_filtered
        else:
            st.warning("Aucune transaction trouvée")
            return df_filtered

    return df



def _get_category_emoji(category: str) -> str:
    """Retourne l'emoji approprié pour une catégorie."""
    category_emojis = {
        'Alimentation': '🍽️',
        'Transport': '🚗',
        'Loisirs': '🎮',
        'Logement': '🏠',
        'Santé': '⚕️',
        'Shopping': '🛍️',
        'Éducation': '📚',
        'Assurances': '🛡️',
        'Abonnements': '📱',
        'Divertissement': '🎬',
        'Utilities': '⚡',
        'Autre': '📎',
    }
    return category_emojis.get(category, '📌')
