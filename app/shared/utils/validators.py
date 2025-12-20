"""Data validation utilities."""

import logging
from datetime import datetime
from typing import Dict, List, Any
from .converters import safe_convert, safe_date_convert

logger = logging.getLogger(__name__)


def validate_transaction_data(transaction: Dict[str, Any]) -> List[str]:
    """
    Validate transaction data and return list of errors.

    Args:
        transaction: Transaction dictionary with keys:
            - type: 'revenu' or 'dépense'
            - categorie: Category name
            - montant: Amount (positive number)
            - date: Date string

    Returns:
        List of error messages (empty if valid)

    Examples:
        >>> validate_transaction_data({'type': 'revenu', 'categorie': 'Salaire', 'montant': 100, 'date': '2025-01-15'})
        []
        >>> validate_transaction_data({'type': 'invalid', 'categorie': '', 'montant': -10, 'date': '2030-01-01'})
        ["Type must be 'revenu' or 'dépense'", "Catégorie is required", "Montant must be positive", "Date cannot be in the future"]
    """
    errors = []

    # Validate type
    transaction_type = transaction.get('type', '').lower()
    if transaction_type not in ['revenu', 'dépense']:
        errors.append("Type must be 'revenu' or 'dépense'")

    # Validate category
    categorie = transaction.get('categorie', '')
    if not categorie or not str(categorie).strip():
        errors.append("Catégorie is required")

    # Validate amount
    montant = safe_convert(transaction.get('montant', 0), float, 0.0)
    if montant <= 0:
        errors.append("Montant must be positive")

    # Validate date
    date_val = safe_date_convert(transaction.get('date'))
    if date_val > datetime.now().date():
        errors.append("Date cannot be in the future")

    return errors


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string

    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_amount(amount: Any) -> bool:
    """
    Check if amount is valid (positive number).

    Args:
        amount: Amount to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        value = safe_convert(amount, float, 0.0)
        return value > 0
    except Exception:
        return False
