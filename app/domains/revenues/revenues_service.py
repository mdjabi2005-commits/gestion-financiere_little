"""
Revenue Processing Service - Business Logic Layer

Handles revenue file scanning, PDF parsing, and data validation.
Separated from UI for testability.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import REVENUS_A_TRAITER
from domains.ocr import parse_uber_pdf, parse_fiche_paie
from shared.utils import safe_convert, safe_date_convert, numero_to_mois
from domains.revenues import is_uber_transaction, process_uber_revenue

logger = logging.getLogger(__name__)


class RevenueData:
    """Data class for revenue information."""
    def __init__(
        self,
        filename: str,
        path: str,
        categorie: str,
        sous_categorie: str,
        montant: float,
        montant_initial: float,
        date: datetime.date,
        source: str = "PDF",
        description: str = "",
        preview_text: str = ""
    ):
        self.filename = filename
        self.path = path
        self.categorie = categorie
        self.sous_categorie = sous_categorie
        self.montant = montant
        self.montant_initial = montant_initial
        self.date = date
        self.source = source
        self.description = description
        self.preview_text = preview_text


def scan_revenue_files(folder_path: str = REVENUS_A_TRAITER) -> List[str]:
    """Scan folder for revenue PDF files."""
    if not os.path.exists(folder_path):
        logger.warning(f"Revenue folder not found: {folder_path}")
        return []
    
    pdf_files = []
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, filename))
    
    logger.info(f"Found {len(pdf_files)} revenue PDFs")
    return pdf_files


def process_single_revenue(file_path: str) -> Optional[RevenueData]:
    """Process a single revenue PDF file."""
    filename = os.path.basename(file_path)
    parent_folder = os.path.basename(os.path.dirname(file_path))
    
    # Determine category from folder
    if parent_folder.lower() in ["revenus_a_traiter", "revenus_traité", "revenus_traités"]:
        sous_categorie = "Revenus"
    else:
        sous_categorie = parent_folder
    
    try:
        # Parse PDF based on type
        if sous_categorie.lower() == "uber":
            parsed = parse_uber_pdf(file_path)
            logger.info(f"Uber PDF: {parsed.get('montant_brut', 0):.2f}€ → {parsed['montant']:.2f}€ net")
        else:
            parsed = parse_fiche_paie(file_path)
        
        # Extract date
        date_val = parsed.get("date", datetime.today().date())
        if isinstance(date_val, str):
            date_val = safe_date_convert(date_val)
        
        mois_nom = numero_to_mois(f"{date_val.month:02d}")
        
        return RevenueData(
            filename=filename,
            path=file_path,
            categorie=sous_categorie,
            sous_categorie=mois_nom,
            montant=parsed.get("montant", 0.0),
            montant_initial=parsed.get("montant", 0.0),
            date=date_val,
            source="PDF",
            preview_text=parsed.get("preview_text", "")
        )
        
    except Exception as e:
        logger.error(f"Revenue parsing failed for {filename}: {e}")
        return RevenueData(
            filename=filename,
            path=file_path,
            categorie="Revenus",
            sous_categorie="Autre",
            montant=0.0,
            montant_initial=0.0,
            date=datetime.today().date(),
            source="PDF Auto"
        )


def validate_revenue_data(revenue: RevenueData) -> tuple[bool, List[str]]:
    """Validate revenue data."""
    errors = []
    
    if revenue.montant <= 0:
        errors.append("Le montant doit être supérieur à 0")
    
    if not revenue.categorie:
        errors.append("La catégorie est requise")
    
    return len(errors) == 0, errors


def prepare_revenue_for_db(revenue: RevenueData, apply_uber_tax: bool = False) -> Dict[str, Any]:
    """Prepare revenue for database insertion."""
    transaction_data = {
        "type": "revenu",
        "categorie": revenue.categorie,
        "sous_categorie": revenue.sous_categorie,
        "montant": revenue.montant,
        "date": revenue.date.isoformat(),
        "source": revenue.source,
        "description": revenue.description
    }
    
    # Apply Uber tax if needed
    if is_uber_transaction(revenue.categorie, ""):
        transaction_data, _ = process_uber_revenue(transaction_data, apply_tax=apply_uber_tax)
    
    return transaction_data
