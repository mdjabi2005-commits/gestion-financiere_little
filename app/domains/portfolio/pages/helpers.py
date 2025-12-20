"""
Portfolio Helper Functions

This module contains utility functions for the portfolio interface:
- normalize_recurrence_column: Normalize recurrence data
- get_period_start_date: Calculate period start dates
- calculate_months_in_period: Calculate number of months in a period
- analyze_exceptional_expenses: Analyze budget metrics
"""

import sqlite3
import pandas as pd
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from config import DB_PATH
from shared.ui import load_transactions

logger = logging.getLogger(__name__)


def normalize_recurrence_column() -> None:
    """Normalize recurrence column by converting 'ponctuelle' to NULL."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Compter avant migration
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE recurrence = 'ponctuelle'")
        count_before = cursor.fetchone()[0]

        if count_before > 0:
            # Remplacer 'ponctuelle' par NULL
            cursor.execute("UPDATE transactions SET recurrence = NULL WHERE recurrence = 'ponctuelle'")
            conn.commit()
            logger.info(f"✅ Normalisation recurrence: {count_before} transactions 'ponctuelle' converties à NULL")

        conn.close()
    except Exception as e:
        logger.warning(f"⚠️ Normalisation recurrence: {str(e)}")


def get_period_start_date(period: str) -> date | None:
    """
    Calculate period start date based on period selection.

    Args:
        period: Period name ("Ce mois", "2 derniers mois", "3 derniers mois", "6 derniers mois", "Depuis le début")

    Returns:
        Date object or None if "Depuis le début"
    """
    today = date.today()

    if period == "Ce mois":
        return today.replace(day=1)
    elif period == "2 derniers mois":
        return (today.replace(day=1) - relativedelta(months=1)).replace(day=1)
    elif period == "3 derniers mois":
        return (today.replace(day=1) - relativedelta(months=2)).replace(day=1)
    elif period == "6 derniers mois":
        return (today.replace(day=1) - relativedelta(months=5)).replace(day=1)
    elif period == "Depuis le début":
        return None
    else:
        return None


def calculate_months_in_period(start_date: date | None, end_date: date | None = None) -> int | None:
    """
    Calculate number of months in a period.

    Args:
        start_date: Start date of the period (None for "since beginning")
        end_date: End date of the period (defaults to today)

    Returns:
        Number of months or None if start_date is None
    """
    if start_date is None:
        # Si pas de date de début (depuis le début), on ne peut pas calculer
        # On retournera le nombre de mois depuis la première transaction
        return None

    if end_date is None:
        end_date = date.today()

    # Calculer la différence en mois
    # On utilise relativedelta pour une différence précise en mois
    delta = relativedelta(end_date, start_date)
    months = delta.years * 12 + delta.months + 1  # +1 pour inclure le mois de début

    return max(1, months)  # Au minimum 1 mois


def analyze_exceptional_expenses(period_start_date: date | None = None) -> dict:
    """
    Analyze budget metrics and exceptional expenses.

    Metrics calculated:
    - SRR: Solde Revenus Réelle (Total revenues)
    - SBT: Solde Budget Théorique (Total budgets * months)
    - SRB: Solde Réel Budget (Real expenses for budgeted categories)
    - SE: Solde Exceptionnel (Exceptional expenses without budget)
    - SDR: Solde Dépense Réelle (Total real expenses)
    - ecart_budgets: Budget variance (SRB - SBT)
    - capacite_theorique: Theoretical capacity (SRR - SBT)
    - realite: Reality (SRR - SDR)

    Args:
        period_start_date: Start date for analysis (None for all time)

    Returns:
        Dictionary with budget metrics
    """
    df_transactions = load_transactions()

    # Filtrer par période si fournie
    if period_start_date is not None:
        df_transactions["date"] = pd.to_datetime(df_transactions["date"])
        df_transactions = df_transactions[df_transactions["date"].dt.date >= period_start_date]

    conn = sqlite3.connect(DB_PATH)
    df_budgets = pd.read_sql_query("SELECT categorie, budget_mensuel FROM budgets_categories", conn)
    conn.close()

    if df_transactions.empty:
        return {
            "SRR": 0.0,  # Solde Revenus Réelle
            "SBT": 0.0,  # Solde Budget Théorique
            "SRB": 0.0,  # Solde Réel Budget
            "SE": 0.0,   # Solde Exceptionnel
            "SDR": 0.0,  # Solde Dépense Réelle
            "ecart_budgets": 0.0,
            "capacite_theorique": 0.0,
            "realite": 0.0
        }

    # Calculer le nombre de mois dans la période
    if period_start_date is None:
        # "Depuis le début" - calculer depuis la première transaction
        first_transaction_date = pd.to_datetime(df_transactions["date"]).min().date()
        nb_mois = calculate_months_in_period(first_transaction_date)
        if nb_mois is None:
            nb_mois = 1
    else:
        nb_mois = calculate_months_in_period(period_start_date)
        if nb_mois is None:
            nb_mois = 1

    # SRR: Total revenus
    SRR = df_transactions[df_transactions["type"] == "revenu"]["montant"].sum()

    # SBT: Total budgets théoriques (multiplié par le nombre de mois)
    SBT_mensuel = df_budgets["budget_mensuel"].sum() if not df_budgets.empty else 0.0
    SBT = SBT_mensuel * nb_mois

    # Récupérer les catégories avec budget
    categories_avec_budget = set(df_budgets["categorie"].tolist()) if not df_budgets.empty else set()

    # SRB: Dépenses réelles pour catégories avec budget
    if categories_avec_budget:
        SRB = df_transactions[
            (df_transactions["type"] == "dépense") &
            (df_transactions["categorie"].isin(categories_avec_budget))
        ]["montant"].sum()
    else:
        SRB = 0.0

    # SE: Dépenses exceptionnelles (sans budget)
    SE = df_transactions[
        (df_transactions["type"] == "dépense") &
        (~df_transactions["categorie"].isin(categories_avec_budget))
    ]["montant"].sum()

    # SDR: Total dépenses réelles = SRB + SE
    SDR = SRB + SE

    # Écart budgets = SRB - SBT
    ecart_budgets = SRB - SBT

    # Capacité théorique = SRR - SBT
    capacite_theorique = SRR - SBT

    # Réalité = SRR - SDR
    realite = SRR - SDR

    return {
        "SRR": SRR,
        "SBT": SBT,
        "SRB": SRB,
        "SE": SE,
        "SDR": SDR,
        "ecart_budgets": ecart_budgets,
        "capacite_theorique": capacite_theorique,
        "realite": realite
    }
