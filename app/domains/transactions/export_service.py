"""CSV export service for transactions without tickets.

This module provides functionality to export transactions with source='import_csv'
that have no associated ticket/document files to a CSV file.
"""

"""
Transaction Export Service

Handles exporting transactions to CSV format.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date

from config import CSV_TRANSACTIONS_SANS_TICKETS
from domains.transactions import TransactionRepository
from shared.services import trouver_fichiers_associes
from shared.logging_config import get_logger
from shared.exceptions import ServiceError

logger = get_logger(__name__)


def get_transactions_sans_tickets() -> List[Dict[str, Any]]:
    """
    Get all transactions with source='import_csv' that have no associated tickets.
    
    Returns:
        List of transaction dictionaries without associated files
    """
    # Get all transactions
    df = TransactionRepository.get_all()
    
    if df.empty:
        return []
    
    # Filter only transactions with source='import_csv'
    df_import_csv = df[df['source'] == 'import_csv']
    
    transactions_sans_tickets = []
    
    for _, row in df_import_csv.iterrows():
        transaction = row.to_dict()
        
        # Check if transaction has associated files
        fichiers = trouver_fichiers_associes(transaction)
        
        if not fichiers:  # No files found
            transactions_sans_tickets.append(transaction)
    
    return transactions_sans_tickets


def export_transactions_sans_tickets_to_csv() -> int:
    """
    Export transactions without tickets to a CSV file.
    
def export_to_csv(
    df: pd.DataFrame,
    filepath: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> bool:
    """
    Export transactions DataFrame to CSV.
    
    Args:
        df: DataFrame with transactions
        filepath: Path to save CSV file
        start_date: Start date filter (optional)
        end_date: End date filter (optional)
    
    Returns:
        True if export successful
        
    Raises:
        ServiceError: If export fails or data is empty
    """
    logger.info(f"Exporting transactions to CSV: {filepath}")
    
    # Validate data
    if df is None or df.empty:
        logger.warning("No data to export")
        raise ServiceError("Aucune donnée à exporter. Vérifiez vos filtres de date.")
    
    try:
        # Filter by date if specified
        if start_date or end_date:
            df = df.copy()
            if start_date:
                df = df[pd.to_datetime(df['date']) >= pd.to_datetime(start_date)]
            if end_date:
                df = df[pd.to_datetime(df['date']) <= pd.to_datetime(end_date)]
            
            if df.empty:
                raise ServiceError(f"Aucune transaction trouvée entre {start_date} et {end_date}")
        
        # Export to CSV
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"Successfully exported {len(df)} transactions to {filepath}")
        return True
        
    except ServiceError:
        raise  # Re-raise our own exceptions
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise ServiceError(f"Échec de l'export CSV : {e}") from e


def get_export_path() -> str:
    """
    Get the path where CSV exports are saved.
    
    Returns:
        CSV export file path
    """
    return CSV_TRANSACTIONS_SANS_TICKETS
