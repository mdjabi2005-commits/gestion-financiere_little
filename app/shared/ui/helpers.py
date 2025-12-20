"""Helper functions for data loading and batch operations.

This module contains utilities for loading transactions, handling recurrent
transactions, and batch inserting transactions into the database.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import streamlit as st

from config import DB_PATH
from shared.utils import safe_convert, safe_date_convert
from shared.utils import validate_transaction_data
from domains.revenues import process_uber_revenue
from domains.transactions.service import normalize_category, normalize_subcategory
from shared.database import get_db_connection
from .toast_components import toast_success, toast_error

logger = logging.getLogger(__name__)


# ==============================
# 📊 DATA LOADING FUNCTIONS
# ==============================

def get_transaction_count() -> int:
    """
    Get the current number of transactions in database.

    Used for intelligent cache invalidation - recalculates only when
    transaction count changes, not based on arbitrary time limits.

    Returns:
        Count of transactions (uncached)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error counting transactions: {e}")
        return 0


@st.cache_data
def load_transactions(sort_by: str = "date", ascending: bool = False) -> pd.DataFrame:
    """
    Load all transactions from the database with safe conversions.

    Loads transactions, applies safe type conversions, and sorts them.
    Default sorting is by date (most recent first).

    Args:
        sort_by: Column name to sort by (default: "date")
        ascending: Sort order - False for descending (default: False)

    Returns:
        DataFrame containing all transactions with converted types

    Example:
        >>> df = load_transactions()
        >>> df.columns
        Index(['id', 'type', 'categorie', 'sous_categorie', 'description',
               'montant', 'date', 'source', 'recurrence', 'date_fin'], dtype='object')
        >>> df['montant'].dtype
        dtype('float64')
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
        conn.close()

        if df.empty:
            return df

        # Safe conversions
        df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))
        df["date"] = df["date"].apply(lambda x: safe_date_convert(x))

        # Convert for pandas
        df["date"] = pd.to_datetime(df["date"])

        # Default sort: Most recent first
        df = df.sort_values(by=sort_by, ascending=ascending)

        return df

    except Exception as e:
        logger.error(f"Error loading transactions: {e}")
        st.error(f"Erreur lors du chargement des transactions: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_recurrent_transactions() -> pd.DataFrame:
    """
    Load recurrent transactions from the database with caching.

    Loads only transactions marked as automatically recurring
    (source='récurrente_auto') with a 5-minute cache.

    Returns:
        DataFrame containing recurrent transactions, sorted by date (descending)

    Example:
        >>> df = load_recurrent_transactions()
        >>> df['source'].unique()
        array(['récurrente_auto'], dtype=object)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT * FROM transactions WHERE source='récurrente_auto'",
            conn
        )
        conn.close()

        if df.empty:
            return df

        # Safe conversions
        df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))
        df["date"] = df["date"].apply(lambda x: safe_date_convert(x))

        # Convert for pandas
        df["date"] = pd.to_datetime(df["date"])

        # Sort by date descending
        df = df.sort_values(by="date", ascending=False)

        return df

    except Exception as e:
        logger.error(f"Error loading recurrent transactions: {e}")
        st.error(f"Erreur lors du chargement des transactions récurrentes: {e}")
        return pd.DataFrame()


def refresh_and_rerun() -> None:
    """
    Clear Streamlit cache and rerun the application.

    This function clears all cached data and forces a complete
    re-execution of the Streamlit app, useful after database modifications.

    Side effects:
        - Clears st.cache_data
        - Triggers st.rerun()

    Example:
        >>> refresh_and_rerun()  # App will reload
    """
    st.cache_data.clear()
    st.rerun()


# ==============================
# 💾 BATCH OPERATIONS
# ==============================

def insert_transaction_batch(transactions: List[Dict[str, Any]]) -> None:
    """
    Insert multiple transactions into the database with validation and deduplication.

    Processes a batch of transactions by:
    1. Validating each transaction's data
    2. Cleaning and normalizing field values
    3. Applying Uber revenue tax processing for revenue transactions
    4. Checking for duplicates before insertion
    5. Inserting valid, non-duplicate transactions

    Args:
        transactions: List of transaction dictionaries, each containing:
            - type: 'revenu' or 'dépense'
            - categorie: Category name
            - sous_categorie: Subcategory name
            - description: Description text
            - montant: Amount (will be converted to float)
            - date: Date string (will be converted)
            - source: Source identifier (default: 'manuel')
            - recurrence: Recurrence pattern (optional)
            - date_fin: End date for recurring transactions (optional)

    Side effects:
        - Inserts transactions into database
        - Displays toast notifications for results
        - Shows info messages for duplicates and Uber processing
        - Logs warnings and errors

    Example:
        >>> transactions = [
        ...     {
        ...         'type': 'dépense',
        ...         'categorie': 'Alimentation',
        ...         'sous_categorie': 'Restaurant',
        ...         'description': 'Déjeuner',
        ...         'montant': 25.50,
        ...         'date': '2025-01-15',
        ...         'source': 'manuel'
        ...     }
        ... ]
        >>> insert_transaction_batch(transactions)
    """
    if not transactions:
        return

    conn = get_db_connection()
    cur = conn.cursor()

    inserted, skipped, uber_processed = 0, 0, 0
    uber_messages = []

    for t in transactions:
        try:
            # Validate data
            errors = validate_transaction_data(t)
            if errors:
                logger.warning(f"Transaction validation failed: {errors}")
                skipped += 1
                continue

            # Clean data
            clean_t = {
                "type": str(t["type"]).strip().lower(),
                "categorie": normalize_category(str(t.get("categorie", "")).strip()),
                "sous_categorie": normalize_subcategory(str(t.get("sous_categorie", "")).strip()),
                "description": str(t.get("description", "")).strip(),
                "montant": safe_convert(t["montant"]),
                "date": safe_date_convert(t["date"]).isoformat(),
                "source": str(t.get("source", "manuel")).strip(),
                "recurrence": str(t.get("recurrence", "")).strip(),
                "date_fin": safe_date_convert(t.get("date_fin")).isoformat() if t.get("date_fin") else ""
            }

            # Process Uber revenue
            if clean_t["type"] == "revenu":
                clean_t, uber_msg = process_uber_revenue(clean_t)
                if uber_msg:
                    uber_processed += 1
                    uber_messages.append(uber_msg)

            # Check for duplicates
            cur.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE type = ? AND categorie = ? AND sous_categorie = ?
                      AND montant = ? AND date = ?
            """, (
                clean_t["type"],
                clean_t.get("categorie", ""),
                clean_t.get("sous_categorie", ""),
                float(clean_t["montant"]),
                clean_t["date"]
            ))

            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            # Insert transaction
            cur.execute("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_t["type"],
                clean_t.get("categorie", ""),
                clean_t.get("sous_categorie", ""),
                clean_t.get("description", ""),
                float(clean_t["montant"]),
                clean_t["date"],
                clean_t.get("source", "manuel"),
                clean_t.get("recurrence", ""),
                clean_t.get("date_fin", "")
            ))
            inserted += 1

        except Exception as e:
            logger.error(f"Error inserting transaction {t}: {e}")

    conn.commit()
    conn.close()

    # Display results
    if inserted > 0:
        toast_success(f"{inserted} transaction(s) insérée(s).")
        if uber_processed > 0:
            st.info(f"🚗 {uber_processed} revenu(s) Uber traité(s) avec application de la fiscalité (79%)")
            for msg in uber_messages:
                st.success(msg)
    if skipped > 0:
        st.info(f"ℹ️ {skipped} doublon(s) détecté(s) et ignoré(s).")
