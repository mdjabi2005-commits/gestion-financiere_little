"""
Charts Components - Graphiques réutilisables

Ce module contient les fonctions de graphiques partagées
entre différentes pages de l'application.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_evolution_chart(df: pd.DataFrame, height: int = 400) -> None:
    """
    Affiche le graphique d'évolution Revenus/Dépenses/Solde.
    
    Le graphique s'adapte aux données filtrées passées en paramètre.
    Utilisé par: Accueil + Voir Transactions
    
    Args:
        df: DataFrame avec colonnes 'date', 'type', 'montant'
        height: Hauteur du graphique en pixels
    """
    if df.empty:
        st.info("Aucune donnée disponible pour le graphique")
        return
    
    # Préparer les données mensuelles
    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["date"])
    df_copy["mois_str"] = df_copy["date"].dt.strftime("%b %Y")
    
    # Grouper par mois et type
    df_evolution = df_copy.groupby(["mois_str", "type"])["montant"].sum().unstack(fill_value=0)
    df_evolution = df_evolution.reindex(
        sorted(df_evolution.index, key=lambda x: pd.to_datetime(x, format='%b %Y'))
    )
    
    # S'assurer que les colonnes existent
    if "revenu" not in df_evolution.columns:
        df_evolution["revenu"] = 0
    if "dépense" not in df_evolution.columns:
        df_evolution["dépense"] = 0
    
    # Arrondir les valeurs
    df_evolution["dépense"] = df_evolution["dépense"].round(2)
    df_evolution["revenu"] = df_evolution["revenu"].round(2)
    
    # Calculer le solde
    solde = (df_evolution["revenu"] - df_evolution["dépense"]).round(2)
    
    # Créer le graphique
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
    
    # Configuration du layout
    fig.update_layout(
        title=dict(
            text='Évolution Revenus, Dépenses et Solde',
            font=dict(size=16, color='white')
        ),
        xaxis_title='Mois',
        yaxis_title='Montant (€)',
        height=height,
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
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(255,255,255,0.3)',
            color='white'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
