"""
Manage Tab - Hub de Gestion

Ce module implémente l'onglet "Gérer" du Portefeuille avec 4 quadrants:
- Quadrant 1: Échéances ponctuelles
- Quadrant 2: Budgets mensuels
- Quadrant 3: Récurrences (abonnements/salaires)
- Quadrant 4: Objectifs financiers
"""

import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from shared.ui import refresh_and_rerun
from shared.ui import toast_success, toast_warning, toast_error


def render_echeances_form(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Formulaire de gestion des échéances ponctuelles"""
    
    # Formulaire d'ajout
    with st.form("form_echeance", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            type_ech = st.selectbox(
                "Type",
                ["revenu", "dépense"],
                key="type_ech"
            )
            categorie_ech = st.text_input(
                "Catégorie",
                key="cat_ech",
                placeholder="Ex: Loyer, Facture EDF..."
            )
        
        with col2:
            montant_ech = st.number_input(
                "Montant (€)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                key="montant_ech"
            )
            date_ech = st.date_input(
                "Date échéance",
                value=date.today(),
                key="date_ech"
            )
        
        description_ech = st.text_input(
            "Description (optionnel)",
            key="desc_ech"
        )
        
        submitted = st.form_submit_button("➕ Ajouter l'échéance", type="primary")
        
        if submitted:
            if categorie_ech and categorie_ech.strip() and montant_ech > 0:
                try:
                    cursor.execute("""
                        INSERT INTO echeances 
                        (type, categorie, montant, date_echeance, type_echeance, description, statut, date_creation)
                        VALUES (?, ?, ?, ?, 'prévue', ?, 'active', ?)
                    """, (
                        type_ech,
                        categorie_ech.strip(),
                        montant_ech,
                        date_ech.isoformat(),
                        description_ech.strip() if description_ech else None,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    toast_success(f"Échéance '{categorie_ech}' ajoutée")
                    refresh_and_rerun()
                except Exception as e:
                    toast_error(f"Erreur: {e}")
            else:
                toast_warning("Veuillez remplir tous les champs obligatoires")
    
    # Liste des échéances existantes
    st.markdown("##### Échéances actives")
    echeances = cursor.execute("""
        SELECT id, type, categorie, montant, date_echeance, description
        FROM echeances
        WHERE statut = 'active' AND type_echeance = 'prévue'
        ORDER BY date_echeance
        LIMIT 10
    """).fetchall()
    
    if echeances:
        for ech in echeances:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                emoji = "💰" if ech[1] == "revenu" else "💸"
                st.write(f"{emoji} **{ech[2]}** - {ech[3]:.2f} € - {ech[4]}")
                if ech[5]:
                    st.caption(ech[5])
            with col2:
                if st.button("✅", key=f"valid_ech_{ech[0]}", help="Marquer comme réalisée"):
                    cursor.execute("UPDATE echeances SET statut = 'realisee' WHERE id = ?", (ech[0],))
                    conn.commit()
                    toast_success("Échéance marquée comme réalisée")
                    refresh_and_rerun()
            with col3:
                if st.button("🗑️", key=f"del_ech_{ech[0]}", help="Supprimer"):
                    cursor.execute("DELETE FROM echeances WHERE id = ?", (ech[0],))
                    conn.commit()
                    toast_success("Échéance supprimée")
                    refresh_and_rerun()
    else:
        st.info("Aucune échéance active")


def render_budgets_form(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Formulaire de gestion des budgets mensuels"""
    
    # Formulaire d'ajout/modification
    with st.form("form_budget", clear_on_submit=True):
        categorie_budget = st.text_input(
            "Catégorie",
            key="cat_budget",
            placeholder="Ex: Alimentation, Transport..."
        )
        
        montant_budget = st.number_input(
            "Budget mensuel (€)",
            min_value=0.0,
            step=10.0,
            value=100.0,
            key="montant_budget"
        )
        
        submitted = st.form_submit_button("💾 Enregistrer le budget", type="primary")
        
        if submitted:
            if categorie_budget and categorie_budget.strip():
                try:
                    cursor.execute("""
                        INSERT INTO budgets_categories (categorie, budget_mensuel, date_creation, date_modification)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(categorie) DO UPDATE SET
                            budget_mensuel = excluded.budget_mensuel,
                            date_modification = excluded.date_modification
                    """, (
                        categorie_budget.strip(),
                        montant_budget,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    toast_success(f"Budget '{categorie_budget}' enregistré")
                    refresh_and_rerun()
                except Exception as e:
                    toast_error(f"Erreur: {e}")
            else:
                toast_warning("Veuillez saisir une catégorie")
    
    # Liste des budgets existants
    st.markdown("##### Budgets actuels")
    budgets = cursor.execute("""
        SELECT id, categorie, budget_mensuel
        FROM budgets_categories
        ORDER BY categorie
    """).fetchall()
    
    if budgets:
        for budget in budgets:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"💰 **{budget[1]}** : {budget[2]:.2f} €/mois")
            with col2:
                if st.button("🗑️", key=f"del_budget_{budget[0]}", help="Supprimer"):
                    cursor.execute("DELETE FROM budgets_categories WHERE id = ?", (budget[0],))
                    conn.commit()
                    toast_success(f"Budget '{budget[1]}' supprimé")
                    refresh_and_rerun()
    else:
        st.info("Aucun budget défini")


def render_recurrences_form(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Formulaire de gestion des récurrences (abonnements/salaires)"""
    
    # Formulaire d'ajout
    with st.form("form_recurrence", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            type_rec = st.selectbox(
                "Type",
                ["revenu", "dépense"],
                key="type_rec"
            )
            categorie_rec = st.text_input(
                "Catégorie",
                key="cat_rec",
                placeholder="Ex: Salaire, Netflix..."
            )
            sous_categorie_rec = st.text_input(
                "Sous-catégorie",
                key="sous_cat_rec",
                placeholder="Ex: Freelance, Streaming..."
            )
        
        with col2:
            montant_rec = st.number_input(
                "Montant (€)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                key="montant_rec"
            )
            frequence_rec = st.selectbox(
                "Fréquence",
                ["mensuelle", "hebdomadaire", "annuelle"],
                key="freq_rec"
            )
        
        date_debut = st.date_input(
            "Date de début",
            value=date.today(),
            key="date_debut_rec"
        )
        
        date_fin = st.date_input(
            "Date de fin (optionnel)",
            value=None,
            key="date_fin_rec",
            help="Laissez vide pour récurrence illimitée"
        )
        
        description_rec = st.text_input(
            "Description (optionnel)",
            key="desc_rec"
        )
        
        submitted = st.form_submit_button("➕ Ajouter la récurrence", type="primary")
        
        if submitted:
            if categorie_rec and categorie_rec.strip() and montant_rec > 0:
                try:
                    cursor.execute("""
                        INSERT INTO recurrences 
                        (type, categorie, sous_categorie, montant, date_debut, date_fin, frequence, description, statut, date_creation, date_modification)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    """, (
                        type_rec,
                        categorie_rec.strip(),
                        sous_categorie_rec.strip() if sous_categorie_rec else '',
                        montant_rec,
                        date_debut.isoformat(),
                        date_fin.isoformat() if date_fin else None,
                        frequence_rec,
                        description_rec.strip() if description_rec else None,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    
                    # Récupérer l'ID de la récurrence créée
                    recurrence_id = cursor.lastrowid
                    conn.commit()
                    
                    # Générer les occurrences passées SEULEMENT (pas futures)
                    from shared.services.recurrence_generation import generate_occurrences_for_recurrence
                    
                    today = date.today()
                    start_gen = date_debut
                    end_gen = today  # IMPORTANT : Seulement jusqu'à aujourd'hui
                    
                    occurrences = generate_occurrences_for_recurrence(recurrence_id, start_gen, end_gen)
                    
                    # Insérer les transactions
                    nb_created = 0
                    for occ in occurrences:
                        cursor.execute("""
                            INSERT INTO transactions
                            (type, categorie, sous_categorie, montant, date, source, description)
                            VALUES (?, ?, ?, ?, ?, 'récurrente_auto', ?)
                        """, (
                            occ['type'],
                            occ['categorie'],
                            occ.get('sous_categorie', ''),
                            occ['montant'],
                            occ['date'],
                            occ.get('description', '')
                        ))
                        nb_created += 1
                    
                    conn.commit()
                    
                    toast_success(f"Récurrence '{categorie_rec}' ajoutée - {nb_created} occurrence(s) passée(s) générée(s)")
                    refresh_and_rerun()
                except Exception as e:
                    toast_error(f"Erreur: {e}")
            else:
                toast_warning("Veuillez remplir tous les champs obligatoires")
    
    # Liste des récurrences existantes
    st.markdown("##### Récurrences actives")
    recurrences = cursor.execute("""
        SELECT id, type, categorie, montant, frequence, date_debut, date_fin, description
        FROM recurrences
        WHERE statut = 'active'
        ORDER BY categorie
        LIMIT 10
    """).fetchall()
    
    if recurrences:
        for rec in recurrences:
            col1, col2 = st.columns([3, 1])
            with col1:
                emoji = "💰" if rec[1] == "revenu" else "💸"
                st.write(f"{emoji} **{rec[2]}** - {rec[3]:.2f} € ({rec[4]})")
                info_parts = []
                if rec[5]:
                    date_debut_str = datetime.fromisoformat(rec[5]).strftime('%d/%m/%Y')
                    info_parts.append(f"Début: {date_debut_str}")
                if rec[6]:
                    date_fin_str = datetime.fromisoformat(rec[6]).strftime('%d/%m/%Y')
                    info_parts.append(f"Fin: {date_fin_str}")
                if rec[7]:
                    info_parts.append(rec[7])
                if info_parts:
                    st.caption(" | ".join(info_parts))
            with col2:
                if st.button("🗑️", key=f"del_rec_{rec[0]}", help="Supprimer"):
                    # Supprimer la récurrence ET ses transactions
                    cursor.execute("""
                        DELETE FROM transactions 
                        WHERE source = 'récurrente_auto' 
                        AND categorie = ?
                    """, (rec[2],))
                    cursor.execute("DELETE FROM recurrences WHERE id = ?", (rec[0],))
                    conn.commit()
                    toast_success("Récurrence et transactions associées supprimées")
                    refresh_and_rerun()
    else:
        st.info("Aucune récurrence active")


def render_objectifs_form(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Formulaire de gestion des objectifs financiers"""
    
    # Formulaire d'ajout
    with st.form("form_objectif", clear_on_submit=True):
        type_obj = st.selectbox(
            "Type d'objectif",
            ["💰 Solde minimum mensuel", "📊 Respect des budgets", "🏦 Épargne cible", "✨ Personnalisé"],
            key="type_obj"
        )
        
        titre_obj = st.text_input(
            "Titre",
            key="titre_obj",
            placeholder="Ex: Économiser pour les vacances"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            montant_obj = st.number_input(
                "Montant cible (€)",
                min_value=0.0,
                step=100.0,
                value=0.0,
                key="montant_obj",
                help="Laisser à 0 si non applicable"
            )
        
        with col2:
            date_limite_obj = st.date_input(
                "Date limite (optionnel)",
                value=None,
                key="date_obj"
            )
        
        submitted = st.form_submit_button("➕ Créer l'objectif", type="primary")
        
        if submitted:
            if titre_obj and titre_obj.strip():
                # Déterminer le type simplifié
                if "Solde minimum" in type_obj:
                    type_simple = "solde_minimum"
                    periodicite = "mensuel"
                elif "Respect" in type_obj:
                    type_simple = "respect_budgets"
                    periodicite = "mensuel"
                elif "Épargne" in type_obj:
                    type_simple = "epargne_cible"
                    periodicite = "unique"
                else:
                    type_simple = "personnalise"
                    periodicite = "unique"
                
                try:
                    cursor.execute("""
                        INSERT INTO objectifs_financiers
                        (type_objectif, titre, montant_cible, date_limite, periodicite, statut, date_creation, date_modification)
                        VALUES (?, ?, ?, ?, ?, 'en_cours', ?, ?)
                    """, (
                        type_simple,
                        titre_obj.strip(),
                        montant_obj if montant_obj > 0 else None,
                        date_limite_obj.isoformat() if date_limite_obj else None,
                        periodicite,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    toast_success(f"Objectif '{titre_obj}' créé")
                    refresh_and_rerun()
                except Exception as e:
                    toast_error(f"Erreur: {e}")
            else:
                toast_warning("Veuillez saisir un titre")
    
    # Liste des objectifs existants
    st.markdown("##### Objectifs actifs")
    objectifs = cursor.execute("""
        SELECT id, titre, montant_cible, date_limite, statut
        FROM objectifs_financiers
        WHERE statut = 'en_cours'
        ORDER BY date_creation DESC
        LIMIT 10
    """).fetchall()
    
    if objectifs:
        for obj in objectifs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🎯 **{obj[1]}**")
                if obj[2]:
                    st.caption(f"Cible: {obj[2]:.2f} €")
                if obj[3]:
                    st.caption(f"Échéance: {obj[3]}")
            with col2:
                if st.button("🗑️", key=f"del_obj_{obj[0]}", help="Supprimer"):
                    cursor.execute("DELETE FROM objectifs_financiers WHERE id = ?", (obj[0],))
                    conn.commit()
                    toast_success("Objectif supprimé")
                    refresh_and_rerun()
    else:
        st.info("Aucun objectif actif")


def render_manage_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the main manage tab with 4 quadrants.
    
    Hub centralisé pour gérer tous les éléments financiers:
    - Échéances ponctuelles
    - Budgets mensuels
    - Récurrences (abonnements/salaires)
    - Objectifs financiers
    
    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("⚙️ Gérer")
    st.caption("Hub centralisé de gestion financière")
    
    # Ligne supérieure: Échéances + Budgets
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("#### 📅 Échéances Ponctuelles")
            render_echeances_form(conn, cursor)
    
    with col2:
        with st.container():
            st.markdown("#### 💰 Budgets Mensuels")
            render_budgets_form(conn, cursor)
    
    st.markdown("---")
    
    # Ligne inférieure: Récurrences + Objectifs
    col3, col4 = st.columns(2)
    
    with col3:
        with st.container():
            st.markdown("#### 🔄 Récurrences")
            st.caption("Abonnements, salaires, revenus fixes...")
            render_recurrences_form(conn, cursor)
    
    with col4:
        with st.container():
            st.markdown("#### 🎯 Objectifs Financiers")
            render_objectifs_form(conn, cursor)
