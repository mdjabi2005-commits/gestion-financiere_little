"""
Analyze Tab - Analyse Financière

Ce module implémente l'onglet "Analyse" du Portefeuille:
- Solde prévisionnel (graph de projection)
- Métriques détaillées (selon image utilisateur)
- Stratégie de rattrapage
- Conseils personnalisés
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from shared.ui import load_transactions


def render_forecast_chart(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Graphique de projection du solde sur 6-12 mois"""
    
    df_trans = load_transactions()
    
    # Calculer solde actuel
    if not df_trans.empty:
        revenus_total = df_trans[df_trans["type"] == "revenu"]["montant"].sum()
        depenses_total = df_trans[df_trans["type"] == "dépense"]["montant"].sum()
        solde_actuel = revenus_total - depenses_total
    else:
        solde_actuel = 0.0
    
    # Récupérer récurrences actives
    recurrences = cursor.execute("""
        SELECT type, montant, frequence
        FROM recurrences
        WHERE statut = 'active'
    """).fetchall()
    
    # Projection sur 6 mois
    mois = []
    soldes = []
    
    for i in range(7):  # 0 = aujourd'hui + 6 mois futurs
        mois_date = date.today() + timedelta(days=i*30)
        mois.append(mois_date.strftime("%b %Y"))
        
        if i == 0:
            soldes.append(solde_actuel)
        else:
            # Calculer impact des récurrences
            impact = 0.0
            for rec in recurrences:
                type_rec, montant, freq = rec
                
                # Nombre d'occurrences dans le mois
                if freq == "mensuelle":
                    nb_occur = 1
                elif freq == "hebdomadaire":
                    nb_occur = 4
                elif freq == "annuelle":
                    nb_occur = 1/12
                else:
                    nb_occur = 1
                
                if type_rec == "revenu":
                    impact += montant * nb_occur
                else:
                    impact -= montant * nb_occur
            
            soldes.append(soldes[-1] + impact)
    
    # Créer graphique
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=mois,
        y=soldes,
        mode='lines+markers',
        name='Solde projeté',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=8),
        fill='tonexty',
        fillcolor='rgba(33, 150, 243, 0.1)'
    ))
    
    # Ligne zéro
    fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
    
    fig.update_layout(
        title="Projection du solde sur 6 mois",
        height=350,
        margin=dict(t=40, b=30, l=40, r=20),
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#1E1E1E',
        xaxis=dict(showgrid=False, color='white'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white', title="Solde (€)"),
        font=dict(color='white'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Alertes
    if any(s < 0 for s in soldes[1:]):
        st.error("⚠️ Alerte : Solde négatif projeté dans les 6 prochains mois !")


def render_detailed_metrics(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Afficher les métriques détaillées selon l'image fournie"""
    
    # Charger données
    df_trans = load_transactions()
    df_budgets = pd.read_sql_query("SELECT * FROM budgets_categories", conn)
    
    # Calculer période actuelle
    today = date.today()
    premier_jour_mois = today.replace(day=1)
    
    if not df_trans.empty:
        df_mois = df_trans[pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois]
        
        revenus_mois = df_mois[df_mois["type"] == "revenu"]["montant"].sum()
        depenses_mois = df_mois[df_mois["type"] == "dépense"]["montant"].sum()
    else:
        df_mois = pd.DataFrame()
        revenus_mois = depenses_mois = 0.0
    
    # ===== SECTION 1: VOS REVENUS =====
    st.markdown("#### 💰 Vos revenus")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total de vos revenus",
            f"{revenus_mois:.2f} €",
            help="Somme de tous les revenus du mois en cours"
        )
    
    st.markdown("---")
    
    # ===== SECTION 2: COMPARAISON BUDGETS ET DÉPENSES =====
    st.markdown("#### 📊 Comparaison budgets et dépenses")
    
    if not df_budgets.empty:
        budgets_prevus = df_budgets["budget_mensuel"].sum()
        
        # Dépenses dans les budgets
        depenses_budgetees = 0.0
        if not df_mois.empty:
            categories_budgetees = df_budgets["categorie"].tolist()
            depenses_budgetees = df_mois[
                (df_mois["type"] == "dépense") &
                (df_mois["categorie"].isin(categories_budgetees))
            ]["montant"].sum()
        
        economies = budgets_prevus - depenses_budgetees
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Budgets prévus",
                f"{budgets_prevus:.2f} €",
                help="Total des budgets mensuels définis"
            )
        with col2:
            st.metric(
                "Dépenses dans les budgets",
                f"{depenses_budgetees:.2f} €",
                help="Dépenses effectuées dans les catégories budgétées"
            )
        with col3:
            st.metric(
                "Économies réalisées",
                f"{economies:.2f} €",
                delta=f"{economies:.2f} €" if economies >= 0 else None,
                delta_color="normal" if economies >= 0 else "inverse",
                help="Budget restant (économies ou dépassement)"
            )
    else:
        st.info("Définissez des budgets pour voir cette section")
    
    st.markdown("---")
    
    # ===== SECTION 3: DÉPENSES HORS BUDGET =====
    st.markdown("#### 🚨 Dépenses hors budget")
    
    if not df_budgets.empty and not df_mois.empty:
        categories_budgetees = df_budgets["categorie"].tolist()
        depenses_hors_budget = df_mois[
            (df_mois["type"] == "dépense") &
            (~df_mois["categorie"].isin(categories_budgetees))
        ]["montant"].sum()
        
        pct_imprevues = (depenses_hors_budget / depenses_mois * 100) if depenses_mois > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Dépenses non planifiées",
                f"{depenses_hors_budget:.2f} €",
                help="Dépenses dans des catégories sans budget défini"
            )
        with col2:
            st.metric(
                "Total de vos dépenses",
                f"{depenses_mois:.2f} €",
                help="Total de toutes les dépenses du mois"
            )
        with col3:
            st.metric(
                "% de dépenses imprévues",
                f"{pct_imprevues:.1f}%",
                delta=f"{pct_imprevues:.1f}%" if pct_imprevues > 50 else None,
                delta_color="inverse" if pct_imprevues > 50 else "off",
                help="Proportion des dépenses hors budget"
            )
    else:
        st.info("Données insuffisantes pour calculer les dépenses hors budget")
    
    st.markdown("---")
    
    # ===== SECTION 4: VOTRE SITUATION FINANCIÈRE =====
    st.markdown("#### 💼 Votre situation financière")
    
    # Calculer solde total
    if not df_trans.empty:
        rev_total = df_trans[df_trans["type"] == "revenu"]["montant"].sum()
        dep_total = df_trans[df_trans["type"] == "dépense"]["montant"].sum()
        solde_final = rev_total - dep_total
    else:
        solde_final = 0.0
    
    # Déficit prévu (différence revenus - budgets)
    if not df_budgets.empty:
        budgets_prevus = df_budgets["budget_mensuel"].sum()
        deficit_prevu = revenus_mois - budgets_prevus
    else:
        deficit_prevu = revenus_mois
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Déficit prévu" if deficit_prevu < 0 else "Surplus prévu",
            f"{deficit_prevu:.2f} €",
            delta=f"{deficit_prevu:.2f} €",
            delta_color="inverse" if deficit_prevu < 0 else "normal",
            help="Différence entre revenus du mois et budgets prévus"
        )
        if deficit_prevu < 0:
            st.caption("⚠️ Déficit")
        else:
            st.caption("✅ Surplus")
    
    with col2:
        st.metric(
            "Votre solde final",
            f"{solde_final:.2f} €",
            delta=f"{solde_final:.2f} €",
            delta_color="normal" if solde_final >= 0 else "inverse",
            help="Solde total de votre compte"
        )
        if solde_final < 0:
            st.caption("⚠️ Solde négatif")
        else:
            st.caption("✅ Solde positif")


def render_strategy(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Stratégie de rattrapage en cas d'écarts"""
    
    df_trans = load_transactions()
    df_budgets = pd.read_sql_query("SELECT * FROM budgets_categories", conn)
    
    today = date.today()
    premier_jour_mois = today.replace(day=1)
    
    if df_trans.empty or df_budgets.empty:
        st.info("Données insuffisantes pour générer une stratégie")
        return
    
    df_mois = df_trans[pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois]
    
    # Détecter budgets dépassés
    budgets_depasses = []
    for _, budget in df_budgets.iterrows():
        if not df_mois.empty:
            depenses_cat = df_mois[
                (df_mois["type"] == "dépense") &
                (df_mois["categorie"] == budget["categorie"])
            ]["montant"].sum()
        else:
            depenses_cat = 0.0
        
        if depenses_cat > budget["budget_mensuel"]:
            ecart = depenses_cat - budget["budget_mensuel"]
            budgets_depasses.append((budget["categorie"], ecart))
    
    if budgets_depasses:
        st.warning(f"⚠️ {len(budgets_depasses)} budget(s) dépassé(s)")
        for cat, ecart in budgets_depasses[:3]:
            st.write(f"• **{cat}** : +{ecart:.2f} € de dépassement")
        
        st.markdown("**Recommandations :**")
        st.write("• Réduire les dépenses dans ces catégories le mois prochain")
        st.write("• Augmenter les budgets si nécessaire")
    else:
        st.success("✅ Tous les budgets sont respectés !")


def render_advice(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Conseils personnalisés basés sur l'analyse"""
    
    df_trans = load_transactions()
    
    if df_trans.empty:
        st.info("Pas encore assez de données pour générer des conseils")
        return
    
    today = date.today()
    premier_jour_mois = today.replace(day=1)
    premier_jour_mois_dernier = (premier_jour_mois - timedelta(days=1)).replace(day=1)
    
    # Comparer avec mois précédent
    df_mois_actuel = df_trans[pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois]
    df_mois_dernier = df_trans[
        (pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois_dernier) &
        (pd.to_datetime(df_trans["date"]).dt.date < premier_jour_mois)
    ]
    
    if not df_mois_actuel.empty and not df_mois_dernier.empty:
        dep_actuel = df_mois_actuel[df_mois_actuel["type"] == "dépense"]["montant"].sum()
        dep_dernier = df_mois_dernier[df_mois_dernier["type"] == "dépense"]["montant"].sum()
        
        variation = ((dep_actuel - dep_dernier) / dep_dernier * 100) if dep_dernier > 0 else 0
        
        st.markdown("**📊 Analyse des tendances**")
        if variation > 10:
            st.warning(f"⚠️ Vos dépenses ont augmenté de {variation:.1f}% par rapport au mois dernier")
        elif variation < -10:
            st.success(f"✅ Vos dépenses ont diminué de {abs(variation):.1f}% par rapport au mois dernier")
        else:
            st.info(f"➡️ Vos dépenses sont stables ({variation:+.1f}%)")
    
    # Top catégorie coûteuse
    if not df_mois_actuel.empty:
        top_cat = df_mois_actuel[df_mois_actuel["type"] == "dépense"].groupby("categorie")["montant"].sum().idxmax()
        top_montant = df_mois_actuel[df_mois_actuel["type"] == "dépense"].groupby("categorie")["montant"].sum().max()
        
        st.markdown(f"**💰 Catégorie la plus coûteuse :** {top_cat} ({top_montant:.2f} €)")


def render_analyze_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the analyze tab (insights and forecasts).
    
    4 sections according to user sketch:
    - Solde prévisionnel (top full width)
    - Métriques détaillées (middle left)
    - Stratégie de rattrapage (middle right)
    - Conseils (bottom full width)
    
    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("📈 Analyse Financière Détaillée")
    
    # Section 1: Graphique de projection (pleine largeur)
    render_forecast_chart(conn, cursor)
    
    st.markdown("---")
    
    # Section 2 & 3: Métriques + Stratégie (2 colonnes)
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        render_detailed_metrics(conn, cursor)
    
    with col2:
        st.markdown("### 🎯 Stratégie de Rattrapage")
        render_strategy(conn, cursor)
    
    st.markdown("---")
    
    # Section 4: Conseils (pleine largeur)
    st.markdown("### 💡 Conseils Personnalisés")
    render_advice(conn, cursor)
