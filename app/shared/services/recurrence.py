"""
Recurrence Service - Simplified wrapper for recurrence operations
"""

import sqlite3
from datetime import date, datetime
from typing import Optional

from config import DB_PATH
from shared.database import get_db_connection
from shared.services.recurrence_generation import backfill_all_recurrences
from shared.logging_config import get_logger

logger = get_logger(__name__)


def backfill_recurrences_to_today(db_path: Optional[str] = None) -> None:
    """
    Génère automatiquement toutes les transactions récurrentes jusqu'à aujourd'hui.
    
    Utilise la nouvelle table recurrences et génère des transactions avec
    source='recurrence_auto'.
    
    Args:
        db_path: Chemin optionnel de la base de données

    Returns:
        None

    Side effects:
        - Insère de nouveaux enregistrements de transactions
        - Logs toutes les transactions insérées
    """
    # Utiliser la nouvelle fonction backfill
    count = backfill_all_recurrences()
    logger.info(f"Recurrence backfill completed: {count} transactions created")
