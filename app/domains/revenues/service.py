"""Revenue processing service for Uber and other revenue sources.

This module handles automatic tax calculations and revenue categorization
for various income sources, with special handling for Uber revenue.

IMPORTANT: When Uber tax is applied (21%), do NOT include URSSAF related expenses
as they are already accounted for in the tax deduction.
"""

from typing import Dict, Tuple, Any, Optional

from shared.utils import safe_convert
from config.ocr_config import UBER_TAX_RATE, UBER_NET_MULTIPLIER
from shared.logging_config import get_logger

logger = get_logger(__name__)


def is_uber_transaction(categorie: str, description: str = "") -> bool:
    """
    Check if a transaction is Uber-related (strict word-boundary detection).

    Only detects transactions with "uber" as a complete word (case-insensitive).
    This prevents false positives like "Aubergine" or "Bourse".

    Args:
        categorie: Transaction category name
        description: Transaction description

    Returns:
        True if transaction contains "uber" as a whole word

    Example:
        >>> is_uber_transaction("Uber Eats")
        True
        >>> is_uber_transaction("UBER")
        True
        >>> is_uber_transaction("Aubergine")
        False
        >>> is_uber_transaction("Bourse")
        False
    """
    import re

    categorie_lower = str(categorie).lower().strip()
    description_lower = str(description).lower().strip()

    # Strict detection: "uber" as a whole word (word boundaries)
    # \b ensures "uber" is not part of another word
    pattern = r'\buber\b'

    return (
        bool(re.search(pattern, categorie_lower)) or
        bool(re.search(pattern, description_lower))
    )


def apply_uber_tax(
    categorie: str,
    montant_brut: float,
    description: str = "",
    apply_tax: bool = True
) -> Tuple[float, str]:
    """
    Apply tax calculation for Uber revenue with optional user confirmation.

    Uber drivers in France are subject to a 21% tax deduction on gross revenue.

    IMPORTANT: When applying Uber tax, do NOT add URSSAF expenses separately
    as they are already included in the 21% tax deduction.

    Args:
        categorie: Transaction category name
        montant_brut: Gross amount before tax
        description: Transaction description for additional detection
        apply_tax: If True, apply the tax deduction (default: True)

    Returns:
        Tuple of (montant_net, tax_message) where:
        - montant_net: Amount after tax (79% of gross) or gross if not applied
        - tax_message: Message explaining the tax calculation or empty

    Example:
        >>> montant_net, message = apply_uber_tax("Uber", 100.0)
        >>> montant_net
        79.0
        >>> "21%" in message
        True
    """
    if not is_uber_transaction(categorie, description):
        return montant_brut, ""

    if not apply_tax or montant_brut <= 0:
        return montant_brut, ""

    montant_net = round(montant_brut * UBER_NET_MULTIPLIER, 2)
    tax_amount = round(montant_brut - montant_net, 2)

    message = f"""
    🚗 **Revenu Uber détecté** - Application de la fiscalité ({UBER_TAX_RATE*100:.0f}%) :
    - Montant brut : {montant_brut:.2f}€
    - Prélèvement fiscal ({UBER_TAX_RATE*100:.0f}%) : -{tax_amount:.2f}€
    - **Montant net : {montant_net:.2f}€**

    ⚠️ **Important** : Ne pas ajouter les dépenses URSSAF séparément,
    elles sont déjà incluses dans ce prélèvement de {UBER_TAX_RATE*100:.0f}%.
    """

    logger.info(f"Uber tax applied: {montant_brut}€ → {montant_net}€")
    return montant_net, message


def process_uber_revenue(
    transaction: Dict[str, Any],
    apply_tax: bool = True
) -> Tuple[Dict[str, Any], str]:
    """
    Process a transaction to apply Uber-specific rules.

    Applies optional tax deduction (21%) and ensures proper categorization
    as "Uber" if not already categorized as such.

    Args:
        transaction: Dictionary with keys 'montant', 'categorie', 'description'
        apply_tax: If True, apply the 21% tax deduction (default: True)

    Returns:
        Tuple of (modified_transaction, tax_message) where:
        - modified_transaction: Updated transaction dict with tax applied
        - tax_message: Message explaining any tax deduction

    Example:
        >>> tx = {'montant': 100.0, 'categorie': 'Uber', 'description': ''}
        >>> result_tx, msg = process_uber_revenue(tx)
        >>> result_tx['montant']
        79.0
    """
    montant_initial = safe_convert(transaction.get('montant', 0))
    categorie = transaction.get('categorie', '')

    montant_final, tax_message = apply_uber_tax(
        categorie,
        montant_initial,
        transaction.get('description', ''),
        apply_tax=apply_tax
    )

    transaction['montant'] = montant_final

    # Note: Do NOT rename the category automatically
    # Only apply tax if user explicitly checked the Uber tax box
    # The category name is set by the user and should be respected

    return transaction, tax_message
