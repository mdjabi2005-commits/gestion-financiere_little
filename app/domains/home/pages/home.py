"""
Home Page Module - Page d'Accueil

Structure en 5 sections selon Image 2:
1. Statut Global (gauche haut)
2. Échéances (droite haut) 
3. Catégories (gauche bas)
4. Dernières Transactions (droite bas)
5. Pilotage Financier (bas pleine largeur)
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from shared.ui import load_transactions
from shared.database import get_db_connection


def interface_accueil() -> None:
    """
    Page d'accueil avec dashboard financier en 5 sections.
    
    Affiche une vue d'ensemble complète de la situation financière.
    """
    st.title("🏠 Tableau de Bord Financier")
    
    # Charger les données
    df_trans = load_transactions()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sélecteur de période
    today = date.today()
    
    # Initialiser la période dans session_state si nécessaire
    if "periode_dashboard" not in st.session_state:
        st.session_state.periode_dashboard = "Ce mois"
    if "date_debut_perso" not in st.session_state:
        st.session_state.date_debut_perso = today.replace(day=1)
    if "date_fin_perso" not in st.session_state:
        st.session_state.date_fin_perso = today
    
    # Sélection de la période
    col_select, col_space = st.columns([1, 3])
    with col_select:
        periode_option = st.selectbox(
            "📅 Période",
            ["Ce mois", "2 mois", "3 mois", "Depuis le début", "Personnalisé"],
            key="periode_dashboard",
            label_visibility="visible"
        )
    
    # Calculer les dates selon la période sélectionnée
    # et le multiplicateur de mois pour les budgets
    if periode_option == "Ce mois":
        date_debut = today.replace(day=1)
        date_fin = today
        nb_mois_periode = 1
    elif periode_option == "2 mois":
        from dateutil.relativedelta import relativedelta
        date_debut = (today.replace(day=1) - relativedelta(months=1))
        date_fin = today
        nb_mois_periode = 2
    elif periode_option == "3 mois":
        from dateutil.relativedelta import relativedelta
        date_debut = (today.replace(day=1) - relativedelta(months=2))
        date_fin = today
        nb_mois_periode = 3
    elif periode_option == "Depuis le début":
        if not df_trans.empty:
            date_debut = pd.to_datetime(df_trans["date"]).min().date()
        else:
            date_debut = today.replace(day=1)
        date_fin = today
        # Calculer le nombre de mois depuis le début
        from dateutil.relativedelta import relativedelta
        nb_mois_periode = ((date_fin.year - date_debut.year) * 12 + 
                          (date_fin.month - date_debut.month) + 1)
    else:  # Personnalisé
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            date_debut = st.date_input(
                "Date début",
                value=st.session_state.date_debut_perso,
                key="date_debut_perso"
            )
        with col_d2:
            date_fin = st.date_input(
                "Date fin",
                value=st.session_state.date_fin_perso,
                key="date_fin_perso"
            )
        # Calculer le nombre de mois pour la période personnalisée
        from dateutil.relativedelta import relativedelta
        nb_mois_periode = ((date_fin.year - date_debut.year) * 12 + 
                          (date_fin.month - date_debut.month) + 1)
    
    # Filtrer les données selon la période
    if not df_trans.empty:
        df_mois = df_trans[
            (pd.to_datetime(df_trans["date"]).dt.date >= date_debut) &
            (pd.to_datetime(df_trans["date"]).dt.date <= date_fin)
        ]
        
        revenus_mois = df_mois[df_mois["type"] == "revenu"]["montant"].sum()
        depenses_mois = df_mois[df_mois["type"] == "dépense"]["montant"].sum()
        solde_mois = revenus_mois - depenses_mois
        
        # Solde total
        revenus_total = df_trans[df_trans["type"] == "revenu"]["montant"].sum()
        depenses_total = df_trans[df_trans["type"] == "dépense"]["montant"].sum()
        solde_total = revenus_total - depenses_total
    else:
        df_mois = pd.DataFrame()  # Initialize empty DataFrame
        revenus_mois = depenses_mois = solde_mois = 0.0
        revenus_total = depenses_total = solde_total = 0.0
    
    # ===== SECTION 1 & 2: STATUT GLOBAL + ÉCHÉANCES =====
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 💰 Statut Global")
        
        # Métriques modernes avec cartes colorées
        st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, var(--card-color-light) 0%, var(--card-color-dark) 100%);
            border-left: 5px solid var(--card-color);
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .metric-title {
            color: #A0A0A0;
            font-size: 14px;
            margin: 0;
            font-weight: 500;
        }
        .metric-value {
            color: #00D4AA;
            font-size: 36px;
            font-weight: 900;
            font-family: 'Arial Black', 'Arial Bold', Arial, sans-serif;
            margin: 10px 0 5px 0;
            letter-spacing: -1px;
        }
        .metric-icon {
            font-size: 24px;
            margin-right: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.markdown(f"""
            <div class="metric-card" style="--card-color: #00D4AA; --card-color-light: #00D4AA20; --card-color-dark: #00D4AA10;">
                <p class="metric-title"><span class="metric-icon">💹</span>Revenus</p>
                <h2 style="color: #00D4AA; font-size: 36px; font-weight: 900; font-family: 'Arial Black', 'Arial Bold', Arial, sans-serif; margin: 10px 0 5px 0; letter-spacing: -1px;">{revenus_mois:_.0f} €</h2>
            </div>
            """.replace("_", " "), unsafe_allow_html=True)
            
        with col_m2:
            st.markdown(f"""
            <div class="metric-card" style="--card-color: #FF6B6B; --card-color-light: #FF6B6B20; --card-color-dark: #FF6B6B10;">
                <p class="metric-title"><span class="metric-icon">💸</span>Dépenses</p>
                <h2 style="color: #FF6B6B; font-size: 36px; font-weight: 900; font-family: 'Arial Black', 'Arial Bold', Arial, sans-serif; margin: 10px 0 5px 0; letter-spacing: -1px;">{depenses_mois:_.0f} €</h2>
            </div>
            """.replace("_", " "), unsafe_allow_html=True)
            
        with col_m3:
            # Logique de couleur intelligente pour le solde
            seuil_proche_zero = 50  # Seuil en euros pour considérer "proche de zéro"
            
            if solde_mois > seuil_proche_zero:
                # Solde positif et confortable
                solde_color = "#00D4AA"  # Vert
                solde_icon = "✅"
            elif solde_mois >= -seuil_proche_zero:
                # Proche de zéro (attention)
                solde_color = "#FFD93D"  # Orange/Jaune
                solde_icon = "⚠️"
            else:
                # Négatif significatif
                solde_color = "#FF6B6B"  # Rouge
                solde_icon = "❌"
            
            st.markdown(f"""
            <div class="metric-card" style="--card-color: {solde_color}; --card-color-light: {solde_color}20; --card-color-dark: {solde_color}10;">
                <p class="metric-title"><span class="metric-icon">{solde_icon}</span>Solde</p>
                <h2 style="color: {solde_color}; font-size: 36px; font-weight: 900; font-family: 'Arial Black', 'Arial Bold', Arial, sans-serif; margin: 10px 0 5px 0; letter-spacing: -1px;">{solde_mois:+_.0f} €</h2>
            </div>
            """.replace("_", " "), unsafe_allow_html=True)
        
        # Graphique d'évolution
        st.markdown("**📈 Évolution mensuelle**")
        
        if not df_mois.empty:
            # Créer données mensuelles (utiliser df_mois pour respecter la période)
            df_mois_copy = df_mois.copy()
            df_mois_copy["date"] = pd.to_datetime(df_mois_copy["date"])
            df_mois_copy["mois_str"] = df_mois_copy["date"].dt.strftime("%b %Y")
            
            # Grouper par mois et type
            df_evolution = df_mois_copy.groupby(["mois_str", "type"])["montant"].sum().unstack(fill_value=0)
            df_evolution = df_evolution.reindex(sorted(df_evolution.index, key=lambda x: pd.to_datetime(x, format='%b %Y')))
            
            if "revenu" not in df_evolution.columns:
                df_evolution["revenu"] = 0
            if "dépense" not in df_evolution.columns:
                df_evolution["dépense"] = 0
            
            # Arrondir les valeurs
            df_evolution["dépense"] = df_evolution["dépense"].round(2)
            df_evolution["revenu"] = df_evolution["revenu"].round(2)
            
            # Calculer le solde
            solde = (df_evolution["revenu"] - df_evolution["dépense"]).round(2)
            
            # Graphique avec barres + ligne
            fig = go.Figure()
            
            # Barres de revenus
            fig.add_trace(go.Bar(
                name='Revenus',
                x=df_evolution.index,
                y=df_evolution["revenu"],
                marker_color='#00D4AA',
                marker_line_color='#00A87E',
                marker_line_width=1.5,
                hovertemplate='<b>%{x}</b><br>Revenus: %{y:,.0f} €<extra></extra>'
            ))
            
            # Barres de dépenses
            fig.add_trace(go.Bar(
                name='Dépenses',
                x=df_evolution.index,
                y=df_evolution["dépense"],
                marker_color='#FF6B6B',
                marker_line_color='#CC5555',
                marker_line_width=1.5,
                hovertemplate='<b>%{x}</b><br>Dépenses: %{y:,.0f} €<extra></extra>'
            ))
            
            # Ligne de solde
            fig.add_trace(go.Scatter(
                name='Solde',
                x=df_evolution.index,
                y=solde,
                mode='lines+markers',
                line=dict(color='#4A90E2', width=3),
                marker=dict(size=8, color='#4A90E2', line=dict(color='white', width=2)),
                hovertemplate='<b>%{x}</b><br>Solde: %{y:+,.0f} €<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(
                    text='Évolution Revenus, Dépenses et Solde',
                    font=dict(size=16, color='white')
                ),
                xaxis_title='Mois',
                yaxis_title='Montant (€)',
                height=400,
                hovermode='x unified',
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.25,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12, color="white"),
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor="white",
                    borderwidth=1
                ),
                margin=dict(t=40, b=80, l=40, r=40),
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#1E1E1E',
                font=dict(color='white'),
                xaxis=dict(showgrid=False, color='white'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=True, zerolinewidth=2, zerolinecolor='rgba(255,255,255,0.3)', color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
    
    with col2:
        st.markdown("### 📅 Échéances à venir")
        
        # Fin du mois en cours
        from dateutil.relativedelta import relativedelta
        fin_mois = (today.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)
        
        # Récupérer toutes les échéances (prévues + récurrentes) du mois
        try:
            echeances = cursor.execute("""
                SELECT type, categorie, montant, date_echeance, description, type_echeance
                FROM echeances
                WHERE statut = 'active' 
                  AND date_echeance >= ?
                  AND date_echeance <= ?
                ORDER BY date_echeance
                LIMIT 5
            """, (today.isoformat(), fin_mois.isoformat())).fetchall()
        except sqlite3.OperationalError:
            # Table doesn't exist (test mode or first run)
            echeances = []
        
        if echeances:
            for ech in echeances:
                type_ech, cat, montant, date_str, desc, type_echeance = ech
                
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    emoji = "💰" if type_ech == "revenu" else "💸"
                    icone_source = "🔄" if type_echeance == 'récurrente' else "📌"
                    st.write(f"{emoji} {icone_source}")
                
                with col2:
                    st.write(f"**{cat}**")
                    if desc:
                        st.caption(f"📅 {pd.to_datetime(date_str).strftime('%d/%m/%Y')} • {desc}")
                    else:
                        st.caption(f"📅 {pd.to_datetime(date_str).strftime('%d/%m/%Y')}")
                
                with col3:
                    couleur = "#FF6B6B" if type_ech == "dépense" else "#00D4AA"
                    signe = "-" if type_ech == "dépense" else "+"
                    st.markdown(f"<p style='color: {couleur}; text-align: right; font-weight: bold;'>{signe}{montant:.2f} €</p>", unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("Aucune échéance prévue ce mois")
        
        # Bouton vers Portefeuille
        if st.button("➡️ Voir toutes les échéances", key="btn_recurrences"):
            st.session_state.requested_page = "💼 Portefeuille"
            st.rerun()
    
    st.markdown("---")
    
    # ===== SECTION 3 & 4: CATÉGORIES + DERNIÈRES TRANSACTIONS =====
    col3, col4 = st.columns([1, 1])
    
    with col3:
        st.markdown("### 🥧 Catégories du mois")
        
        if not df_mois.empty:
            # Pie chart dépenses par catégorie
            depenses_cat = df_mois[df_mois["type"] == "dépense"].groupby("categorie")["montant"].sum()
            
            if not depenses_cat.empty:
                fig_pie = go.Figure()
                
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#FFD93D', '#6C5CE7', '#A8E6CF']
                
                fig_pie.add_trace(go.Pie(
                    labels=depenses_cat.index,
                    values=depenses_cat.values,
                    marker=dict(colors=colors[:len(depenses_cat)], line=dict(color='white', width=2)),
                    hovertemplate='<b>%{label}</b><br>Montant: %{value:.2f} €<br>%{percent}<extra></extra>',
                    textinfo='label+percent',
                    textposition='auto'
                ))
                
                fig_pie.update_layout(
                    height=300,
                    showlegend=False,
                    paper_bgcolor='#1E1E1E',
                    font=dict(color='white'),
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Aucune dépense ce mois")
        else:
            st.info("Aucune donnée ce mois")
        
        # Bouton Ajouter Transaction
        if st.button("➕ Ajouter une transaction", key="btn_add_trans", type="primary"):
            st.session_state.requested_page = "💳 Transactions"
            st.rerun()
        
        # Compteur transactions
        if not df_trans.empty:
            nb_trans = len(df_trans)
            nb_trans_mois = len(df_mois) if not df_mois.empty else 0
            st.caption(f"📊 {nb_trans_mois} transactions ce mois ({nb_trans} au total)")
    
    with col4:
        st.markdown("### 🕒 Dernières transactions")
        
        if not df_trans.empty:
            # Initialiser le nombre à afficher
            if "nb_trans_affichees" not in st.session_state:
                st.session_state.nb_trans_affichees = 5
            
            nb_afficher = st.session_state.nb_trans_affichees
            df_recent = df_trans.sort_values("date", ascending=False).head(nb_afficher)
            
            for _, trans in df_recent.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    emoji = "💸" if trans["type"] == "dépense" else "💹"
                    st.write(f"{emoji}")
                
                with col2:
                    st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                    st.caption(f"📅 {pd.to_datetime(trans['date']).strftime('%d/%m/%Y')}")
                
                with col3:
                    couleur = "#FF6B6B" if trans["type"] == "dépense" else "#00D4AA"
                    signe = "-" if trans["type"] == "dépense" else "+"
                    st.markdown(f"<p style='color: {couleur}; text-align: right; font-weight: bold;'>{signe}{trans['montant']:.2f} €</p>", unsafe_allow_html=True)
                
                st.markdown("---")
            
            # Boutons pour afficher plus/moins
            col_plus, col_moins = st.columns(2)
            with col_plus:
                if nb_afficher < len(df_trans) and nb_afficher < 20:
                    if st.button("➕ Afficher plus", key="btn_plus_trans"):
                        st.session_state.nb_trans_affichees = min(nb_afficher + 5, 20, len(df_trans))
                        st.rerun()
            with col_moins:
                if nb_afficher > 5:
                    if st.button("➖ Afficher moins", key="btn_moins_trans"):
                        st.session_state.nb_trans_affichees = max(nb_afficher - 5, 5)
                        st.rerun()
        else:
            st.info("Aucune transaction enregistrée")
        
        # Bouton Voir tout
        if st.button("➡️ Voir toutes les transactions", key="btn_voir_trans"):
            st.session_state.requested_page = "📊 Voir Transactions"
            st.rerun()
    
    st.markdown("---")
    
    # ===== SECTION 5: PILOTAGE FINANCIER =====
    st.markdown("### 🎯 Pilotage Financier")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("#### 💰 Mes Budgets")
        
        # Récupérer budgets
        try:
            df_budgets = pd.read_sql_query("SELECT * FROM budgets_categories", conn)
        except (sqlite3.OperationalError, pd.errors.DatabaseError):
            df_budgets = pd.DataFrame()
        
        if not df_budgets.empty:
            # Afficher top 5 budgets avec barres de progression
            for _, budget in df_budgets.head(5).iterrows():
                if not df_mois.empty:
                    depenses_cat = df_mois[
                        (df_mois["type"] == "dépense") &
                        (df_mois["categorie"] == budget["categorie"])
                    ]["montant"].sum()
                else:
                    depenses_cat = 0.0
                
                # Ajuster le budget cible selon la période (multiplicateur exact)
                budget_ajuste = budget["budget_mensuel"] * nb_mois_periode
                pct = (depenses_cat / budget_ajuste * 100) if budget_ajuste > 0 else 0
                
                st.write(f"**{budget['categorie']}**")
                st.progress(max(0.0, min(pct / 100, 1.0)))
                st.caption(f"{depenses_cat:.0f} € / {budget_ajuste:.0f} € ({pct:.0f}%)")
                st.markdown("")
            
            # Bouton Voir tout
            if st.button("➡️ Gérer mes budgets", key="btn_budgets"):
                st.session_state.requested_page = "💼 Portefeuille"
                st.rerun()
        else:
            st.info("Aucun budget défini")
            if st.button("➕ Créer un budget", key="btn_create_budget"):
                st.session_state.requested_page = "💼 Portefeuille"
                st.rerun()
    
    with col6:
        st.markdown("#### 🎯 Mes Objectifs")
        
        # Récupérer objectifs
        try:
            objectifs = cursor.execute("""
                SELECT id, titre, montant_cible, type_objectif
                FROM objectifs_financiers
                WHERE statut = 'en_cours'
                ORDER BY date_creation DESC
                LIMIT 5
            """).fetchall()
        except sqlite3.OperationalError:
            objectifs = []
        
        if objectifs:
            for obj in objectifs:
                titre, cible, type_obj = obj[1], obj[2], obj[3]
                
                # Icône selon type
                if type_obj == "solde_minimum":
                    emoji = "💰"
                    if cible:
                        progression = (solde_total / cible * 100) if cible > 0 else 0
                    else:
                        progression = 0
                elif type_obj == "epargne_cible":
                    emoji = "🏦"
                    if cible:
                        progression = (max(solde_total, 0) / cible * 100) if cible > 0 else 0
                    else:
                        progression = 0
                else:
                    emoji = "✨"
                    progression = 0
                
                st.write(f"{emoji} **{titre}**")
                if cible and cible > 0:
                    st.progress(max(0.0, min(progression / 100, 1.0)))
                    st.caption(f"{progression:.0f}% - Cible: {cible:.0f} €")
                else:
                    st.caption("Objectif sans cible monétaire")
                st.markdown("")
            
            # Bouton Voir tout
            if st.button("➡️ Gérer mes objectifs", key="btn_objectifs"):
                st.session_state.requested_page = "💼 Portefeuille"
                st.rerun()
        else:
            st.info("Aucun objectif défini")
            if st.button("➕ Créer un objectif", key="btn_create_obj"):
                st.session_state.requested_page = "💼 Portefeuille"
                st.rerun()
    
    conn.close()
