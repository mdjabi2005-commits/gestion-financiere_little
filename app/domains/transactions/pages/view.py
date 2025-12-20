"""
Transactions Page Module

This module contains all transaction-related interface functions including:
- Simplified transaction interface (main menu)
- View/Edit transactions interface
- Add expenses interface (manual + CSV import)
"""

import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime, date, timedelta
from typing import Optional, Dict
from config import DB_PATH, TO_SCAN_DIR , REVENUS_A_TRAITER
from shared.database import get_db_connection
from domains.transactions import TransactionRepository
from shared.ui import (
    load_transactions,
    insert_transaction_batch,
    refresh_and_rerun
)

from shared.ui import (
    toast_success, toast_error, toast_warning,
    afficher_documents_associes, get_badge_icon
)
from shared.utils import safe_convert, safe_date_convert
from domains.revenues import is_uber_transaction, process_uber_revenue
from shared.services import backfill_recurrences_to_today
from domains.transactions.service import normalize_category, normalize_subcategory
from shared.services import (
    deplacer_fichiers_associes,
    supprimer_fichiers_associes,
    trouver_fichiers_associes
)
from shared.services import build_fractal_hierarchy
from shared.ui.sunburst_navigation import sunburst_navigation
from shared.ui.components.charts import render_evolution_chart
from shared.ui.components.calendar_component import render_calendar, get_calendar_date_range


from domains.transactions.pages.helpers import get_transactions_for_fractal_code



from domains.transactions.pages.add import interface_transactions_simplifiee



from domains.transactions.pages.add import interface_ajouter_depenses_fusionnee



def interface_voir_transactions() -> None:
    """
    View transactions interface with interactive calendar and chart.
    
    Layout:
    1. Top: Navigation Fractale (gauche) + Calendrier (droite)
    2. Middle: Métriques (pleine largeur)
    3. Bottom: Graphique (gauche) + Tableau (droite)
    
    Mode Consultation uniquement.
    """
    # CSS pour compacter la page
    st.markdown("""
    <style>
        .stMetric { margin-bottom: 0rem !important; gap: 0 !important; }
        hr { margin: 0.2rem 0 !important; padding: 0 !important; }
        [data-testid="stHeading"] { margin-bottom: 0.2rem !important; padding-bottom: 0rem !important; margin-top: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Mes Transactions")

    # Show loading spinner while page loads
    with st.spinner("🔄 Chargement des transactions..."):
        backfill_recurrences_to_today(DB_PATH)
        df = load_transactions()

    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par en ajouter !")
        return

    # =====================================================
    # SECTION 1: ARBRE DYNAMIQUE + CALENDRIER (haut)
    # =====================================================
    col_tree, col_calendar = st.columns([2, 1])
    
    with col_tree:
        st.subheader("🌳 Arbre Dynamique")
        hierarchy = build_fractal_hierarchy()
        
        # Render custom Plotly sunburst component with click detection
        tree_result = sunburst_navigation(
            hierarchy=hierarchy,
            key='tree_transactions',
            height=600
        )
        
        # Debug: show selected filters
        if tree_result and tree_result.get('codes'):
            selected_codes = tree_result['codes']
            labels = [hierarchy.get(code, {}).get('label', code) for code in selected_codes]
            st.caption(f"🎯 Filtres actifs ({len(selected_codes)}): {', '.join(labels)}")
            st.caption("💡 _Cliquez sur le centre (Univers Financier) pour tout réinitialiser_")
        else:
            st.caption("💡 _Cliquez sur des catégories pour filtrer. Cliquez au centre pour réinitialiser._")
    
    with col_calendar:
        st.subheader("📅 Calendrier")
        selected_date = render_calendar(df, key='cal_transactions')

    st.markdown("---")

    # =====================================================
    # APPLIQUER LES FILTRES (Calendrier + Fractale)
    # =====================================================
    df_filtered = df.copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])

    # Filtre calendrier (date ou plage)
    date_debut, date_fin = get_calendar_date_range(key='cal_transactions')
    
    if date_debut and date_fin:
        # Plage complète
        df_filtered = df_filtered[
            (df_filtered["date"].dt.date >= date_debut) &
            (df_filtered["date"].dt.date <= date_fin)
        ]
    elif date_debut:
        # Seulement date de début (depuis cette date)
        df_filtered = df_filtered[df_filtered["date"].dt.date >= date_debut]
    elif date_fin:
        # Seulement date de fin (jusqu'à cette date)
        df_filtered = df_filtered[df_filtered["date"].dt.date <= date_fin]
    # Sinon (None, None) : pas de filtre de date, afficher tout

    # Filtre multi-select de l'arbre dynamique
    if tree_result and tree_result.get('codes'):
        selected_codes = tree_result['codes']
        
        # Filtrer pour chaque code sélectionné
        df_tree_filtered = pd.DataFrame()
        
        for code in selected_codes:
            df_code = get_transactions_for_fractal_code(code, hierarchy, df_filtered)
            df_tree_filtered = pd.concat([df_tree_filtered, df_code], ignore_index=True)
        
        if not df_tree_filtered.empty:
            df_filtered = df_tree_filtered.drop_duplicates(subset=['id'], keep='first')

    # Tri par date (plus récentes en premier)
    df_filtered = df_filtered.sort_values("date", ascending=False).reset_index(drop=True)

    if df_filtered.empty:
        st.warning("🔍 Aucune transaction trouvée avec ces filtres")
        return

    # =====================================================
    # SECTION 2: MÉTRIQUES (milieu)
    # =====================================================
    total_revenus = df_filtered[df_filtered["type"] == "revenu"]["montant"].sum()
    total_depenses = df_filtered[df_filtered["type"] == "dépense"]["montant"].sum()
    solde = total_revenus - total_depenses

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Transactions", len(df_filtered))
    with col2:
        st.metric("💹 Revenus", f"{total_revenus:.0f} €")
    with col3:
        st.metric("💸 Dépenses", f"{total_depenses:.0f} €")
    with col4:
        delta_color = "normal" if solde >= 0 else "inverse"
        st.metric("💰 Solde", f"{solde:+.0f} €", delta_color=delta_color)

    st.markdown("---")

    # =====================================================
    # SECTION 3: GRAPHIQUE + TABLEAU (bas)
    # =====================================================
    col_graph, col_table = st.columns([1, 1.5])

    with col_graph:
        st.subheader("📈 Graphique")
        render_evolution_chart(df_filtered, height=450)

    with col_table:
        # Toggle edit mode
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.subheader("📋 Transactions")
        with col_header2:
            # Initialize edit mode in session state
            if 'transactions_edit_mode' not in st.session_state:
                st.session_state.transactions_edit_mode = False
            
            if st.session_state.transactions_edit_mode:
                if st.button("👁️ Mode Consultation", use_container_width=True, key="toggle_view_mode"):
                    st.session_state.transactions_edit_mode = False
                    st.rerun()
            else:
                if st.button("✏️ Mode Édition", use_container_width=True, key="toggle_edit_mode"):
                    st.session_state.transactions_edit_mode = True
                    st.rerun()
        
        # Préparer l'affichage
        df_display = df_filtered.copy()
        df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))
        
        if st.session_state.transactions_edit_mode:
            # MODE ÉDITION
            st.info("⚠️ **Mode Édition activé** - Modifiez directement les cellules du tableau ci-dessous.")
            
            # Prepare editable dataframe with deletion checkbox
            df_edit = df_display[['id', 'date', 'type', 'categorie', 'sous_categorie', 'description', 'montant']].copy()
            df_edit['date'] = pd.to_datetime(df_edit['date'])
            # Add a checkbox column for deletion
            df_edit.insert(0, '🗑️ Supprimer', False)
            
            # Display editable table
            edited_df = st.data_editor(
                df_edit,
                column_config={
                    "🗑️ Supprimer": st.column_config.CheckboxColumn(
                        "🗑️",
                        help="Cocher pour supprimer cette transaction",
                        default=False,
                        width="small"
                    ),
                    "id": st.column_config.NumberColumn(
                        "ID",
                        disabled=True,
                        width="small"
                    ),
                    "date": st.column_config.DateColumn(
                        "Date",
                        format="DD/MM/YYYY",
                        width="medium"
                    ),
                    "type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["revenu", "dépense"],
                        width="small"
                    ),
                    "categorie": st.column_config.TextColumn(
                        "Catégorie",
                        help="Saisir une catégorie existante ou nouvelle",
                        required=True,
                        width="medium"
                    ),
                    "sous_categorie": st.column_config.TextColumn(
                        "Sous-catégorie",
                        help="Saisir une sous-catégorie existante ou nouvelle",
                        width="medium"
                    ),
                    "description": st.column_config.TextColumn(
                        "Description",
                        width="large"
                    ),
                    "montant": st.column_config.NumberColumn(
                        "Montant (€)",
                        format="%.2f",
                        min_value=0.01,
                        width="small"
                    )
                },
                use_container_width=True,
                height=450,
                hide_index=True,
                num_rows="fixed"  # Prevent adding rows
            )
            
            # Check for deletions
            transactions_to_delete = edited_df[edited_df['🗑️ Supprimer'] == True]['id'].tolist()
            
            # Detect changes (excluding the delete column)
            df_edit_compare = df_edit.drop(columns=['🗑️ Supprimer'])
            edited_df_compare = edited_df.drop(columns=['🗑️ Supprimer'])
            
            has_changes = not edited_df_compare.equals(df_edit_compare)
            has_deletions = len(transactions_to_delete) > 0
            
            if has_changes or has_deletions:
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col2:
                    if st.button("💾 Sauvegarder", use_container_width=True, type="primary"):
                        # Handle modifications
                        modified_count = 0
                        if has_changes:
                            for idx in edited_df_compare.index:
                                if not edited_df_compare.loc[idx].equals(df_edit_compare.loc[idx]):
                                    try:
                                        # Get old and new data
                                        old_row = df_edit_compare.loc[idx]
                                        new_row = edited_df_compare.loc[idx]
                                        
                                        # Get transaction from database
                                        transaction = TransactionRepository.get_by_id(int(new_row['id']))
                                        
                                        if transaction:
                                            # Check if category/subcategory changed (for file movement)
                                            cat_changed = old_row['categorie'] != new_row['categorie']
                                            subcat_changed = old_row['sous_categorie'] != new_row['sous_categorie']
                                            
                                            if cat_changed or subcat_changed:
                                                # Move files if exists
                                                old_trans_dict = old_row.to_dict()
                                                old_trans_dict['source'] = transaction.source
                                                old_trans_dict['type'] = old_row['type']
                                                
                                                new_trans_dict = new_row.to_dict()
                                                new_trans_dict['source'] = transaction.source
                                                new_trans_dict['type'] = new_row['type']
                                                
                                                deplacer_fichiers_associes(old_trans_dict, new_trans_dict)
                                            
                                            # Update transaction
                                            transaction.type = new_row['type']
                                            transaction.categorie = new_row['categorie']
                                            transaction.sous_categorie = new_row['sous_categorie'] if pd.notna(new_row['sous_categorie']) else None
                                            transaction.description = new_row['description'] if pd.notna(new_row['description']) else ""
                                            transaction.montant = float(new_row['montant'])
                                            transaction.date = new_row['date'].date() if pd.notna(new_row['date']) else transaction.date
                                            
                                            if TransactionRepository.update(transaction):
                                                modified_count += 1
                                    
                                    except Exception as e:
                                        st.error(f"❌ Erreur lors de la modification de la transaction #{new_row['id']}: {e}")
                        
                        # Handle deletions
                        deleted_count = 0
                        if has_deletions:
                            for trans_id in transactions_to_delete:
                                if TransactionRepository.delete(int(trans_id), delete_files=True):
                                    deleted_count += 1
                        
                        # Show results
                        messages = []
                        if modified_count > 0:
                            messages.append(f"{modified_count} transaction(s) modifiée(s)")
                        if deleted_count > 0:
                            messages.append(f"{deleted_count} transaction(s) supprimée(s)")
                        
                        if messages:
                            toast_success(f"✅ {', '.join(messages)}")
                            st.rerun()
                        else:
                            st.warning("Aucune modification enregistrée")
                
                with col3:
                    if st.button("❌ Annuler", use_container_width=True):
                        st.rerun()
                
                # Show warning if deletions pending
                if has_deletions:
                    st.warning(f"⚠️ {len(transactions_to_delete)} transaction(s) seront supprimées lors de la sauvegarde")
        
        else:
            # MODE CONSULTATION (existing code)
            df_display["Type"] = df_display["type"].apply(lambda x: "🟢" if x == "revenu" else "🔴")
            df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
            df_display["Montant"] = df_display["montant"].apply(lambda x: f"{x:.2f}")

            st.dataframe(
                df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(columns={
                    "categorie": "Catégorie",
                    "sous_categorie": "Sous-catégorie",
                    "description": "Description"
                }),
                use_container_width=True,
                height=450,
                hide_index=True
            )

            st.caption(f"{len(df_display)} transactions")

    # =====================================================
    # BOUTONS D'ACTION
    # =====================================================
    st.markdown("---")
    
    # Info pour l'utilisateur
    if not tree_result or tree_result.get('code') == 'TR':
        st.info("💡 **Astuce :** Cliquez sur une section de l'arbre dynamique pour filtrer les transactions par catégorie")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("➕ Ajouter une Transaction", use_container_width=True):
            st.session_state.requested_page = "💳 Transactions"
            st.rerun()
    
    with col2:
        # Bouton pour exporter les transactions sans tickets
        if st.button("📤 Exporter transactions sans tickets (CSV)", use_container_width=True, help="Exporte toutes les transactions importées via CSV qui n'ont pas de documents associés"):
            try:
                from domains.transactions.export_service import export_transactions_sans_tickets_to_csv, get_export_path
                
                with st.spinner("Export en cours..."):
                    nb_exported = export_transactions_sans_tickets_to_csv()
                
                if nb_exported > 0:
                    export_path = get_export_path()
                    toast_success(f"✅ {nb_exported} transaction(s) exportée(s) vers {export_path}")
                    st.info(f"📂 Fichier créé : `{export_path}`")
                else:
                    st.info("ℹ️ Aucune transaction sans ticket trouvée (source='import_csv')")
            except Exception as e:
                toast_error(f"❌ Erreur lors de l'export : {e}")

    # =====================================================
    # SECTION 4: DOCUMENTS ASSOCIÉS
    # =====================================================
    st.markdown("---")
    
    # Compter combien de transactions ont des documents
    transactions_avec_docs = []
    for _, trans in df_filtered.iterrows():
        fichiers = trouver_fichiers_associes(trans.to_dict())
        if fichiers:
            transactions_avec_docs.append((trans, fichiers))
    
    if transactions_avec_docs:
        with st.expander(f"📎 Documents associés ({len(transactions_avec_docs)} transaction(s) avec documents)", expanded=False):
            st.markdown("### 📂 Documents des transactions affichées")
            st.caption(f"Affichage des documents pour {len(transactions_avec_docs)} transaction(s) ayant des fichiers associés")
            st.markdown("---")
            
            # Afficher toutes les transactions en lignes (pas d'onglets)
            for trans, fichiers in transactions_avec_docs:
                # Affichage en 3 colonnes comme dans home.py
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    emoji = "💸" if trans["type"] == "dépense" else "💹"
                    st.write(f"{emoji}")
                
                with col2:
                    st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                    st.caption(f"📅 {pd.to_datetime(trans['date']).strftime('%d/%m/%Y')} • Transaction #{trans['id']}")
                    if trans.get('description'):
                        st.caption(f"📝 {trans['description']}")
                
                with col3:
                    couleur = "#FF6B6B" if trans["type"] == "dépense" else "#00D4AA"
                    signe = "-" if trans["type"] == "dépense" else "+"
                    st.markdown(f"<p style='color: {couleur}; text-align: right; font-weight: bold;'>{signe}{trans['montant']:.2f} €</p>", unsafe_allow_html=True)
                
                # Documents dans un expander pour ne pas alourdir la page
                trans_dict = trans.to_dict()
                with st.expander(f"📎 Voir les {len(fichiers)} document(s)", expanded=False):
                    afficher_documents_associes(trans_dict, context=f"view_trans_{trans['id']}")
                
                st.markdown("---")

    
    else:
        st.info("📎 Aucun document associé aux transactions affichées")

    
    # Note: Debug buttons removed after switching to dynamic tree





# Fonctions helper déplacées dans transactions_helpers.py
from domains.transactions.pages.helpers import (
    render_graphique_section_v2,
    render_tableau_transactions_v2
)
