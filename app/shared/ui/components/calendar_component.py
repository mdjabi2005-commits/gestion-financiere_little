"""
Calendar Component - Calendrier interactif

Composant calendrier pour filtrer les transactions par date.
Affiche une vue mensuelle avec les jours ayant des transactions marqués.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Set
import calendar


def render_calendar(
    df: pd.DataFrame,
    key: str = "calendar",
    selected_month: Optional[date] = None
) -> Optional[date]:
    """
    Affiche un calendrier interactif mensuel.
    
    Args:
        df: DataFrame avec colonne 'date' et 'type'
        key: Clé unique pour les widgets Streamlit
        selected_month: Mois à afficher (défaut: mois en cours)
    
    Returns:
        Date sélectionnée ou None si aucune sélection
    """
    # Initialiser le mois affiché
    if f"{key}_month" not in st.session_state:
        st.session_state[f"{key}_month"] = selected_month or date.today().replace(day=1)
    
    if f"{key}_selected_date" not in st.session_state:
        st.session_state[f"{key}_selected_date"] = None
    
    current_month = st.session_state[f"{key}_month"]
    
    # Navigation mois
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    
    with col_prev:
        if st.button("◀", key=f"{key}_prev", help="Mois précédent"):
            # Aller au mois précédent
            if current_month.month == 1:
                new_month = current_month.replace(year=current_month.year - 1, month=12)
            else:
                new_month = current_month.replace(month=current_month.month - 1)
            st.session_state[f"{key}_month"] = new_month
            st.session_state[f"{key}_selected_date"] = None  # Reset selection
            st.rerun()
    
    with col_title:
        # Afficher mois et année
        mois_noms = [
            "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        st.markdown(
            f"<h3 style='text-align: center; margin: 0;'>{mois_noms[current_month.month]} {current_month.year}</h3>",
            unsafe_allow_html=True
        )
    
    with col_next:
        if st.button("▶", key=f"{key}_next", help="Mois suivant"):
            # Aller au mois suivant
            if current_month.month == 12:
                new_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                new_month = current_month.replace(month=current_month.month + 1)
            st.session_state[f"{key}_month"] = new_month
            st.session_state[f"{key}_selected_date"] = None  # Reset selection
            st.rerun()
    
    # Calculer les jours avec transactions
    days_with_transactions = _get_days_with_transactions(df, current_month)
    
    # Afficher la grille du calendrier
    _render_calendar_grid(current_month, days_with_transactions, key)
    
    st.markdown("---")
    
    # Sélection de plage de dates
    st.caption("📅 Sélection de plage (optionnel)")
    col_start, col_end = st.columns(2)
    
    with col_start:
        date_start = st.date_input(
            "Début",
            value=None,
            key=f"{key}_date_start",
            help="Laisser vide pour afficher toutes les transactions"
        )
    
    with col_end:
        date_end = st.date_input(
            "Fin",
            value=None,
            key=f"{key}_date_end",
            help="Laisser vide pour afficher toutes les transactions"
        )
    
    # Bouton reset
    if st.session_state[f"{key}_selected_date"] or date_start or date_end:
        if st.button("🔄 Réinitialiser", key=f"{key}_reset", use_container_width=True):
            st.session_state[f"{key}_selected_date"] = None
            st.session_state[f"{key}_date_start"] = None
            st.session_state[f"{key}_date_end"] = None
            st.rerun()
    
    return st.session_state[f"{key}_selected_date"]


def _get_days_with_transactions(df: pd.DataFrame, month: date) -> Dict[int, Dict]:
    """
    Récupère les jours du mois ayant des transactions.
    
    Returns:
        Dict[jour] = {'has_revenue': bool, 'has_expense': bool, 'count': int}
    """
    if df.empty:
        return {}
    
    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["date"])
    
    # Filtrer sur le mois
    mask = (
        (df_copy["date"].dt.year == month.year) &
        (df_copy["date"].dt.month == month.month)
    )
    df_month = df_copy[mask]
    
    if df_month.empty:
        return {}
    
    days_info = {}
    for _, row in df_month.iterrows():
        day = row["date"].day
        if day not in days_info:
            days_info[day] = {"has_revenue": False, "has_expense": False, "count": 0}
        
        days_info[day]["count"] += 1
        if row["type"] == "revenu":
            days_info[day]["has_revenue"] = True
        else:
            days_info[day]["has_expense"] = True
    
    return days_info


def _render_calendar_grid(month: date, days_info: Dict[int, Dict], key: str) -> None:
    """Affiche la grille du calendrier."""
    
    # En-têtes des jours
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    cols = st.columns(7)
    for i, jour in enumerate(jours):
        with cols[i]:
            st.markdown(
                f"<div style='text-align: center; font-weight: bold; color: #888; font-size: 12px;'>{jour}</div>",
                unsafe_allow_html=True
            )
    
    # Obtenir le calendrier du mois
    cal = calendar.monthcalendar(month.year, month.month)
    
    # Jour sélectionné
    selected = st.session_state.get(f"{key}_selected_date")
    selected_day = selected.day if selected else None
    
    # Afficher les semaines
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
                else:
                    _render_day_cell(day, days_info.get(day), selected_day, month, key)


def _render_day_cell(
    day: int,
    day_info: Optional[Dict],
    selected_day: Optional[int],
    month: date,
    key: str
) -> None:
    """Affiche une cellule de jour."""
    
    is_selected = day == selected_day
    has_transactions = day_info is not None
    
    # Déterminer la couleur du badge
    if has_transactions:
        if day_info["has_revenue"] and day_info["has_expense"]:
            badge_color = "#FFD93D"  # Jaune = mixte
            badge = "🟡"
        elif day_info["has_revenue"]:
            badge_color = "#00D4AA"  # Vert = revenus
            badge = "🟢"
        else:
            badge_color = "#FF6B6B"  # Rouge = dépenses
            badge = "🔴"
    else:
        badge_color = "transparent"
        badge = ""
    
    # Style de la cellule
    bg_color = "#4A90E2" if is_selected else ("rgba(255,255,255,0.1)" if has_transactions else "transparent")
    border = "2px solid #4A90E2" if is_selected else "1px solid rgba(255,255,255,0.1)"
    cursor = "pointer" if has_transactions else "default"
    
    # Afficher le jour avec un bouton invisible
    cell_html = f"""
    <div style="
        text-align: center;
        padding: 8px 4px;
        border-radius: 8px;
        background: {bg_color};
        border: {border};
        min-height: 40px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    ">
        <span style="font-size: 14px; font-weight: {'bold' if is_selected else 'normal'};">{day}</span>
        <span style="font-size: 10px;">{badge}</span>
    </div>
    """
    
    st.markdown(cell_html, unsafe_allow_html=True)
    
    # Bouton invisible pour la sélection
    if has_transactions:
        if st.button(
            f"📅",
            key=f"{key}_day_{day}",
            help=f"{day_info['count']} transaction(s)",
            use_container_width=True
        ):
            st.session_state[f"{key}_selected_date"] = month.replace(day=day)
            st.rerun()


def get_calendar_date_range(key: str = "calendar") -> tuple:
    """
    Retourne la plage de dates pour le filtrage.
    
    Returns:
        (date_debut, date_fin) ou (None, None) si aucune sélection (affiche tout)
    """
    # Priorité 1: plage de dates personnalisée
    date_start = st.session_state.get(f"{key}_date_start")
    date_end = st.session_state.get(f"{key}_date_end")
    
    if date_start and date_end:
        return date_start, date_end
    elif date_start:
        # Seulement date de début: afficher depuis cette date
        return date_start, date.today()
    elif date_end:
        # Seulement date de fin: afficher jusqu'à cette date
        return None, date_end
    
    # Priorité 2: jour spécifique cliqué sur le calendrier
    selected_date = st.session_state.get(f"{key}_selected_date")
    if selected_date:
        return selected_date, selected_date
    
    # Par défaut: afficher toutes les transactions
    return None, None

