"""
Revenue Database Operations

Handles persistence for revenue processing.
"""

import os
import shutil
from typing import Dict, Any

from config import REVENUS_TRAITES
from shared.database import get_db_connection
from domains.transactions.service import normalize_category, normalize_subcategory
from domains.ocr.logging import log_ocr_scan, determine_success_level
from shared.logging_config import get_logger
from shared.exceptions import DatabaseError

logger = get_logger(__name__)


def save_revenue_to_database(transaction_data: Dict[str, Any]) -> int:
    """Save revenue transaction to database."""
    logger.info(f"Saving revenue: {transaction_data.get('categorie', 'N/A')}/{transaction_data.get('sous_categorie', 'N/A')} - {transaction_data.get('montant', 0)}€")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "revenu",
            normalize_category(transaction_data["categorie"]),
            normalize_subcategory(transaction_data["sous_categorie"]),
            transaction_data["montant"],
            transaction_data["date"],
            transaction_data["source"],
            transaction_data.get("description", "")
        ))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Saved revenue ID {transaction_id}: {transaction_data['montant']}€")
        return transaction_id
        
    except Exception as e:
        logger.error(f"Database save failed: {e}", exc_info=True)
        conn.rollback()
        raise DatabaseError(f"Failed to save revenue: {e}") from e
    finally:
        conn.close()


def move_revenue_file(
    file_path: str,
    categorie: str,
    sous_categorie: str,
    transaction_id: int
) -> str:
    """Move revenue file to processed directory."""
    target_dir = os.path.join(REVENUS_TRAITES, categorie, sous_categorie)
    os.makedirs(target_dir, exist_ok=True)
    
    _, ext = os.path.splitext(file_path)
    new_filename = f"{transaction_id}{ext}"
    target_path = os.path.join(target_dir, new_filename)
    
    shutil.move(file_path, target_path)
    logger.info(f"Moved revenue to {target_path}")
    return target_path


def log_revenue_scan(
    filename: str,
    montant_initial: float,
    montant_final: float,
    categorie: str,
    sous_categorie: str
) -> None:
    """Log revenue OCR scan."""
    success_level = determine_success_level([montant_initial], montant_final)
    
    patterns = []
    if categorie.lower() == "uber":
        patterns = ["uber", "revenu", "pdf"]
    else:
        patterns = ["salaire", "revenu", "pdf"]
    
    log_ocr_scan(
        document_type="revenu",
        filename=filename,
        montants_detectes=[montant_initial],
        montant_choisi=montant_final,
        categorie=categorie,
        sous_categorie=sous_categorie,
        patterns_detectes=patterns,
        success_level=success_level
    )
