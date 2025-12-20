"""
Transactions Helpers - Fonctions utilitaires pour transactions.py

Ce fichier contient les fonctions helper extraites du gros fichier transactions.py
"""

import pandas as pd
from typing import Dict


def get_transactions_for_fractal_code(code: str, hierarchy: Dict, df: pd.DataFrame) -> pd.DataFrame:
    """
    Get transactions for a specific fractal code (category or subcategory).

    For subcategories (level 3), also filter by parent category to avoid getting
    transactions from other categories that might have the same subcategory name.
    """
    if not code or code not in hierarchy:
        return pd.DataFrame()

    node = hierarchy[code]
    level = node.get('level', 0)

    # Niveau 3 (sous-catégories) - IMPORTANT: filtrer aussi par catégorie parente ET par type
    if level == 3:
        subcategory_name = node.get('label', '')
        parent_code = node.get('parent', '')

        # Récupérer la catégorie parente
        if parent_code and parent_code in hierarchy:
            parent_node = hierarchy[parent_code]
            category_name = parent_node.get('label', '')
            parent_parent_code = parent_node.get('parent', '')

            # Déterminer le type (revenu/dépense) à partir du grand-parent
            transaction_type = 'revenu' if parent_parent_code == 'REVENUS' else 'dépense'

            # Filtrer par type ET catégorie ET sous-catégorie pour éviter tout conflit
            df_filtered = df[
                (df['type'].str.lower() == transaction_type.lower()) &
                (df['categorie'].str.lower() == category_name.lower()) &
                (df['sous_categorie'].str.lower() == subcategory_name.lower())
            ]
            return df_filtered
        else:
            # Fallback si pas de parent (ne devrait pas arriver)
            return df[df['sous_categorie'].str.lower() == subcategory_name.lower()]

    # Niveau 2 (catégories) - afficher toutes les sous-catégories de cette catégorie
    elif level == 2:
        category_name = node.get('label', '')
        parent_code = node.get('parent', '')  # This is REVENUS or DEPENSES (level 1)

        # Déterminer le type (revenu/dépense) directement depuis le parent
        transaction_type = 'revenu' if parent_code == 'REVENUS' else 'dépense'

        # Filtrer par catégorie ET type pour éviter les doublons si une catégorie existe dans les deux
        return df[
            (df['categorie'].str.lower() == category_name.lower()) &
            (df['type'].str.lower() == transaction_type.lower())
        ]

    # Niveau 1 (type: Revenus/Dépenses) - afficher toutes les transactions du type
    elif level == 1:
        transaction_type = 'revenu' if code == 'REVENUS' else 'dépense'
        return df[df['type'].str.lower() == transaction_type.lower()]

    # Niveau 0 (root) - afficher tout
    elif level == 0:
        return df

    return pd.DataFrame()


def render_graphique_section_v2(df: pd.DataFrame) -> None:
    """Section Graphique (droite milieu)."""
    import plotly.graph_objects as go
    import streamlit as st
    
    st.markdown("### Graphique")
    
    # Bar chart mensuel
    if not df.empty:
        df_monthly = df.copy()
        df_monthly["mois"] = df_monthly["date"].dt.to_period("M").astype(str)
        monthly_sum = df_monthly.groupby("mois")["montant"].sum()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_sum.index,
            y=monthly_sum.values,
            marker_color=['#4A90E2', '#00D4AA', '#FFD93D', '#FF6B6B'] * len(monthly_sum),
            text=[f"{v:.0f}" for v in monthly_sum.values],
            textposition='outside'
        ))
        
        fig.update_layout(
            height=500,  # Augmenté de 300 à 500px
            margin=dict(t=10, b=30, l=30, r=10),
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            xaxis=dict(showgrid=False, color='white'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible")


def render_tableau_transactions_v2(df: pd.DataFrame) -> None:
    """Section Tableau des Transactions (bas)."""
    import streamlit as st
    
    # Afficher toutes les transactions
    df_display = df.copy()
    
    # Préparer affichage
    df_display["Type"] = df_display["type"].apply(
        lambda x: "🔴" if x == "dépense" else "🟢"
    )
    df_display["Date"] = df_display["date"].dt.strftime("%d/%m/%Y")
    df_display["Montant"] = df_display["montant"].apply(lambda x: f"{x:.2f}")
    
    # Dataframe
    st.dataframe(
        df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(columns={
            "categorie": "Catégorie",
            "sous_categorie": "Sous-catégorie",
            "description": "Description"
        }),
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    st.caption(f"{len(df_display)} transactions")
