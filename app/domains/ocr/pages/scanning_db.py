"""
Scanning Database Operations

Handles database persistence for scanning operations.
Separated from service and UI layers.
"""

import logging
import os
import shutil
from typing import Dict, Any

from shared.database import get_db_connection
from domains.transactions.service import normalize_category, normalize_subcategory
from domains.ocr.parsers_OLD_BACKUP import move_ticket_to_sorted
from domains.ocr.logging import log_ocr_scan, determine_success_level

logger = logging.getLogger(__name__)


def save_ticket_to_database(transaction_data: Dict[str, Any]) -> int:
    """
    Save ticket transaction to database.
    
    Args:
        transaction_data: Transaction data dictionary
    
    Returns:
        Transaction ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO transactions (type, categorie, sous_categorie, description, montant, date, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_data["type"],
            normalize_category(transaction_data["categorie"]),
            normalize_subcategory(transaction_data["sous_categorie"]),
            transaction_data.get("description", ""),
            transaction_data["montant"],
            transaction_data["date"],
            transaction_data["source"]
        ))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Saved ticket transaction ID {transaction_id}: {transaction_data['montant']}€")
        return transaction_id
        
    except Exception as e:
        logger.error(f"Database save failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def move_ticket_file(
    ticket_path: str,
    categorie: str,
    sous_categorie: str,
    transaction_id: int
) -> str:
    """
    Move ticket file to sorted directory.
    
    Args:
        ticket_path: Current ticket path
        categorie: Category for organization
        sous_categorie: Subcategory
        transaction_id: Transaction ID for filename
    
    Returns:
        New file path
    """
    try:
        new_path = move_ticket_to_sorted(
            ticket_path,
            categorie,
            sous_categorie,
            transaction_id
        )
        logger.info(f"Moved ticket {os.path.basename(ticket_path)} to {new_path}")
        return new_path
    except Exception as e:
        logger.error(f"File move failed: {e}")
        raise


def log_ticket_scan(
    filename: str,
    montants_detectes: list,
    montant_choisi: float,
    categorie: str,
    sous_categorie: str,
    methode_detection: str,
    ocr_text: str
) -> None:
    """
    Log OCR scan statistics.
    
    Args:
        filename: Ticket filename
        montants_detectes: List of detected amounts
        montant_choisi: Final chosen amount
        categorie: Category
        sous_categorie: Subcategory
        methode_detection: Detection method used
        ocr_text: OCR text for pattern extraction
    """
    # Determine success level
    success_level = determine_success_level(montants_detectes, montant_choisi)
    
    # Extract patterns from text
    patterns_detectes = []
    text_lower = ocr_text.lower()
    ticket_patterns = ['total', 'montant', 'ttc', 'cb', 'carte', 'espèces', 'esp']
    for pattern in ticket_patterns:
        if pattern in text_lower:
            patterns_detectes.append(pattern)
    
    # Log scan
    log_ocr_scan(
        document_type="ticket",
        filename=filename,
        montants_detectes=montants_detectes,
        montant_choisi=montant_choisi,
        categorie=categorie,
        sous_categorie=sous_categorie,
        patterns_detectes=patterns_detectes,
        success_level=success_level,
        methode_detection=methode_detection
    )
    
    logger.debug(f"Logged scan for {filename}: {success_level}")
