"""
OCR Scanning Service - Business Logic Layer

Handles ticket scanning, OCR processing, and data validation.
Separated from UI concerns for better testability and maintainability.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from config import TO_SCAN_DIR
from domains.ocr import full_ocr, parse_ticket_metadata_v2
from domains.ocr.parsers_OLD_BACKUP import extract_text_from_pdf
from shared.utils import safe_convert, safe_date_convert
from shared.logging_config import get_logger
from shared.exceptions import OCRError

logger = get_logger(__name__)


class TicketData:
    """Data class for ticket information."""
    def __init__(
        self,
        filename: str,
        path: str,
        ocr_text: str = "",
        montant: float = 0.0,
        date: Optional[str] = None,
        categorie: str = "Divers",
        sous_categorie: str = "Autre",
        fiable: bool = False,
        methode_detection: str = "NONE"
    ):
        self.filename = filename
        self.path = path
        self.ocr_text = ocr_text
        self.montant = montant
        self.date = date or datetime.now().date().isoformat()
        self.categorie = categorie
        self.sous_categorie = sous_categorie
        self.fiable = fiable
        self.methode_detection = methode_detection


def scan_ticket_files(folder_path: str = TO_SCAN_DIR) -> List[str]:
    """
    Scan folder for ticket files.
    
    Args:
        folder_path: Path to scan folder
    
    Returns:
        List of file paths (JPG, PNG, PDF)
    """
    if not os.path.exists(folder_path):
        logger.warning(f"Scan folder does not exist: {folder_path}")
        return []
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.pdf')
    files = []
    
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.lower().endswith(valid_extensions):
                full_path = os.path.join(root, filename)
                files.append(full_path)
    
    logger.info(f"Found {len(files)} ticket files to process")
    return files


def extract_text_from_ticket(file_path: str) -> str:
    """
    Extract OCR text from ticket file.
    
    Args:
        file_path: Path to image or PDF file
    
    Returns:
        Extracted OCR text
    """
    try:
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
            logger.info(f"Extracted text from PDF: {os.path.basename(file_path)}")
        else:
            text = full_ocr(file_path)
            logger.info(f"Extracted text from image: {os.path.basename(file_path)}")
        
        return text
    except Exception as e:
        logger.error(f"OCR extraction failed for {os.path.basename(file_path)}: {e}")
        raise OCRError(f"Failed to extract text from {os.path.basename(file_path)}") from e


def process_single_ticket(file_path: str) -> TicketData:
    """
    Process a single ticket file: OCR + parsing.
    
    Args:
        file_path: Path to ticket file
    
    Returns:
        TicketData with extracted information
    """
    filename = os.path.basename(file_path)
    logger.info(f"Processing ticket: {filename}")
    
    # Step 1: Extract OCR text
    ocr_text = extract_text_from_ticket(file_path)
    
    if not ocr_text:
        logger.warning(f"No OCR text extracted from {filename}")
        return TicketData(filename=filename, path=file_path)
    
    # Step 2: Parse metadata
    try:
        metadata = parse_ticket_metadata_v2(ocr_text)
        
        ticket = TicketData(
            filename=filename,
            path=file_path,
            ocr_text=ocr_text,
            montant=metadata.get('montant', 0.0),
            date=metadata.get('date'),
            fiable=metadata.get('fiable', False),
            methode_detection=metadata.get('methode_detection', 'NONE')
        )
        
        # Deduce category from folder name
        parent_folder = os.path.basename(os.path.dirname(file_path))
        if parent_folder and parent_folder != "tickets_a_scanner":
            ticket.categorie = parent_folder
        
        logger.info(f"Parsed ticket: {filename} → {ticket.montant}€ (method: {ticket.methode_detection})")
        return ticket
        
    except Exception as e:
        logger.error(f"Metadata parsing failed for {filename}: {e}")
        return TicketData(filename=filename, path=file_path, ocr_text=ocr_text)


def validate_ticket_data(ticket: TicketData) -> Tuple[bool, List[str]]:
    """
    Validate ticket data before saving.
    
    Args:
        ticket: TicketData to validate
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if ticket.montant <= 0:
        errors.append("Le montant doit être supérieur à 0")
    
    if not ticket.categorie or ticket.categorie.strip() == "":
        errors.append("La catégorie est requise")
    
    if not ticket.date:
        errors.append("La date est requise")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.debug(f"Ticket validation passed: {ticket.filename}")
    else:
        logger.warning(f"Ticket validation failed: {ticket.filename} - {errors}")
    
    return is_valid, errors


def deduce_subcategory(ticket: TicketData) -> str:
    """
    Deduce subcategory from ticket data.
    
    Args:
        ticket: TicketData
    
    Returns:
        Suggested subcategory
    """
    # Simple deduction based on category
    category_mapping = {
        "alimentation": "courses",
        "restaurant": "restaurant",
        "transport": "carburant",
        "loisirs": "sortie"
    }
    
    cat_lower = ticket.categorie.lower()
    return category_mapping.get(cat_lower, "autre")


def prepare_ticket_for_db(ticket: TicketData) -> Dict[str, Any]:
    """
    Prepare ticket data for database insertion.
    
    Args:
        ticket: TicketData
    
    Returns:
        Dictionary ready for database
    """
    return {
        "type": "dépense",
        "categorie": ticket.categorie.strip(),
        "sous_categorie": ticket.sous_categorie.strip(),
        "montant": ticket.montant,
        "date": ticket.date,
        "source": "OCR-Scan",
        "description": f"Scan: {ticket.filename}"
    }
