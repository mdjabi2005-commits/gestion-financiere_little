"""
Overview Tab - Vue d'ensemble (Dashboard)

Ce module implémente l'onglet "Vue d'ensemble" du Portefeuille:
- Lecture seule (pas de formulaires)
- 3 sections: Échéances à venir, Budget du mois, Objectifs
- Boutons de navigation vers l'onglet "Gérer"
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.graph_objects as go
from shared.ui import load_transactions


def render_upcoming_deadlines(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Afficher les 5 prochaines échéances"""
    
    today = date.today()
    
    echeances = cursor.execute("""
        SELECT type, categorie, montant, date_echeance, description
        FROM echeances
        WHERE statut = 'active' 
          AND date_echeance >= ?
          AND type_echeance = 'prévue'
        ORDER BY date_echeance
        LIMIT 5
    """, (today.isoformat(),)).fetchall()
    
    if echeances:
        for ech in echeances:
            emoji = "💰" if ech[0] == "revenu" else "💸"
            date_ech = pd.to_datetime(ech[3]).strftime("%d/%m")
            st.write(f"{emoji} **{ech[1]}** - {ech[2]:.2f} € - {date_ech}")
            if ech[4]:
                st.caption(ech[4])
    else:
        st.info("Aucune échéance à venir")


def render_budget_overview_chart(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Graphique Budget vs Dépenses du mois"""
    
    df_budgets = pd.read_sql_query("SELECT * FROM budgets_categories", conn)
    df_trans = load_transactions()
    
    if df_budgets.empty:
        st.info("Définissez des budgets pour voir le graphique")
        return
    
    # Calculer dépenses du mois
    today = datetime.now()
    premier_jour_mois = today.replace(day=1).date()
    
    if not df_trans.empty:
        df_mois = df_trans[pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois]
    else:
        df_mois = pd.DataFrame()
    
    # Préparer données
    data = []
    for _, budget in df_budgets.iterrows():
        if not df_mois.empty:
            depenses = df_mois[
                (df_mois["type"] == "dépense") &
                (df_mois["categorie"] == budget["categorie"])
            ]["montant"].sum()
        else:
            depenses = 0.0
        
        data.append({
            "Catégorie": budget["categorie"],
            "Budget": budget["budget_mensuel"],
            "Dépensé": depenses
        })
    
    df = pd.DataFrame(data)
    
    # Graphique
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Budget',
        x=df['Catégorie'],
        y=df['Budget'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Dépensé',
        x=df['Catégorie'],
        y=df['Dépensé'],
        marker_color='salmon'
    ))
    
    fig.update_layout(
        barmode='group',
        height=300,
        margin=dict(t=10, b=30, l=30, r=10),
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',
        xaxis=dict(showgrid=False, color='white'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
        font=dict(color='white'),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_objectives_progress(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Liste des objectifs avec barres de progression"""
    
    objectifs = cursor.execute("""
        SELECT id, type_objectif, titre, montant_cible
        FROM objectifs_financiers
        WHERE statut = 'en_cours'
        ORDER BY date_creation DESC
        LIMIT 5
    """).fetchall()
    
    if not objectifs:
        st.info("Aucun objectif défini")
        return
    
    df_trans = load_transactions()
    
    # Calculer solde actuel
    if not df_trans.empty:
        revenus = df_trans[df_trans["type"] == "revenu"]["montant"].sum()
        depenses = df_trans[df_trans["type"] == "dépense"]["montant"].sum()
        solde = revenus - depenses
    else:
        solde = 0.0
    
    for obj in objectifs:
        type_obj, titre, cible = obj[1], obj[2], obj[3]
        
        # Icône selon type
        if type_obj == "solde_minimum":
            emoji = "💰"
            if cible:
                progression = (solde / cible * 100) if cible > 0 else 0
            else:
                progression = 0
        elif type_obj == "respect_budgets":
            emoji = "📊"
            progression = 0  # Simplifié ici
        elif type_obj == "epargne_cible":
            emoji = "🏦"
            if cible:
                progression = (max(solde, 0) / cible * 100) if cible > 0 else 0
            else:
                progression = 0
        else:
            emoji = "✨"
            progression = 0
        
        st.write(f"{emoji} **{titre}**")
        if cible and cible > 0:
            st.progress(max(0.0, min(progression / 100, 1.0)))
            st.caption(f"{progression:.0f}% - {cible:.0f} €")
        else:
            st.caption("Objectif sans cible monétaire")
        st.markdown("")


def render_overview_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the overview tab (dashboard in read-only mode).
    
    Dashboard de consultation rapide avec 3 sections selon croquis:
    - Échéances à venir (haut - pleine largeur)
    - Budget du mois (bas gauche)
    - Objectifs (bas droite)
    
    Chaque section a un bouton pour aller vers l'onglet "Gérer".
    
    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("📊 Vue d'ensemble")
    st.caption("Dashboard de consultation rapide")
    
    # ===== SECTION 1 : ÉCHÉANCES À VENIR (Pleine largeur) =====
    with st.container():
        col_title, col_btn = st.columns([4, 1])
        with col_title:
            st.markdown("### 📅 Échéances à venir")
        with col_btn:
            if st.button("➡️ Gérer", key="btn_ech", help="Gérer les échéances", use_container_width=True):
                st.session_state.portfolio_active_tab = 1
                st.rerun()
        
        render_upcoming_deadlines(conn, cursor)
    
    st.markdown("---")
    
    # ===== SECTION 2 & 3 : BUDGET + OBJECTIFS (2 colonnes) =====
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Budget du mois
        with st.container():
            col_title, col_btn = st.columns([3, 1])
            with col_title:
                st.markdown("### 💰 Budget")
                st.caption("Le graphique")
            with col_btn:
                if st.button("➡️", key="btn_budget", help="Gérer les budgets"):
                    st.session_state.portfolio_active_tab = 1
                    st.rerun()
            
            render_budget_overview_chart(conn, cursor)
    
    with col2:
        # Objectifs
        with st.container():
            col_title, col_btn = st.columns([3, 1])
            with col_title:
                st.markdown("### 🎯 Objectifs")
            with col_btn:
                if st.button("➡️", key="btn_obj", help="Gérer les objectifs"):
                    st.session_state.portfolio_active_tab = 1
                    st.rerun()
            
            render_objectives_progress(conn, cursor)
