"""
Category and Subcategory Normalization Module

Normalizes category and subcategory names to ensure consistency across the application.
Handles case variations, whitespace, and special characters.

@author: djabi
@version: 1.0
@date: 2025-11-23
"""

import re
from typing import Optional
from shared.logging_config import get_logger

logger = get_logger(__name__)


def normalize_category(category: Optional[str]) -> Optional[str]:
    """
    Normalize a category name.

    Rules:
    - Convert to Title Case (first letter of each word capitalized)
    - Replace underscores with spaces
    - Remove extra whitespace
    - Strip leading/trailing whitespace
    - Handle None values

    Args:
        category: Raw category name (e.g., "UBER", "uber", "Uber")

    Returns:
        Normalized category name (e.g., "Uber")

    Examples:
        >>> normalize_category("UBER")
        'Uber'
        >>> normalize_category("uber")
        'Uber'
        >>> normalize_category("  Uber  ")
        'Uber'
        >>> normalize_category("ALIMENTATION")
        'Alimentation'
        >>> normalize_category(None)
        None
    """
    if not category:
        return None

    # Convert to string and strip whitespace
    category_str = str(category).strip()

    if not category_str:
        return None

    # Replace underscores with spaces
    category_str = category_str.replace('_', ' ')

    # Remove extra spaces between words
    category_str = ' '.join(category_str.split())

    # Convert to Title Case
    category_normalized = category_str.title()

    logger.debug(f"Normalized category: '{category}' -> '{category_normalized}'")
    return category_normalized


def normalize_subcategory(subcategory: Optional[str]) -> Optional[str]:
    """
    Normalize a subcategory name.

    Same rules as normalize_category.

    Args:
        subcategory: Raw subcategory name

    Returns:
        Normalized subcategory name

    Examples:
        >>> normalize_subcategory("SALAIRE NET")
        'Salaire Net'
        >>> normalize_subcategory("essence")
        'Essence'
    """
    return normalize_category(subcategory)


def normalize_both(
    category: Optional[str],
    subcategory: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    """
    Normalize both category and subcategory at once.

    Args:
        category: Raw category name
        subcategory: Raw subcategory name

    Returns:
        Tuple of (normalized_category, normalized_subcategory)

    Example:
        >>> cat, subcat = normalize_both("UBER", "ride")
        >>> cat, subcat
        ('Uber', 'Ride')
    """
    return (
        normalize_category(category),
        normalize_subcategory(subcategory)
    )


def normalize_dict(data: dict) -> dict:
    """
    Normalize category fields in a dictionary (e.g., transaction dict).

    Normalizes these keys if present:
    - 'categorie'
    - 'sous_categorie'
    - 'category'
    - 'subcategory'

    Args:
        data: Dictionary with potential category fields

    Returns:
        New dictionary with normalized categories

    Example:
        >>> tx = {'categorie': 'UBER', 'sous_categorie': 'ride'}
        >>> normalize_dict(tx)
        {'categorie': 'Uber', 'sous_categorie': 'Ride'}
    """
    normalized = data.copy()

    # Normalize French field names
    if 'categorie' in normalized:
        normalized['categorie'] = normalize_category(normalized['categorie'])

    if 'sous_categorie' in normalized:
        normalized['sous_categorie'] = normalize_subcategory(normalized['sous_categorie'])

    # Normalize English field names
    if 'category' in normalized:
        normalized['category'] = normalize_category(normalized['category'])

    if 'subcategory' in normalized:
        normalized['subcategory'] = normalize_subcategory(normalized['subcategory'])

    return normalized


# ============================================================================
# PREDEFINED CATEGORY MAPPINGS (Optional - for future use)
# ============================================================================

# Common category variations that should map to standard names
CATEGORY_ALIASES = {
    'REVENUS': 'Revenus',
    'REVENUE': 'Revenus',
    'INCOME': 'Revenus',
    'DÉPENSES': 'Dépenses',
    'DEPENSES': 'Dépenses',
    'EXPENSE': 'Dépenses',
    'EXPENSES': 'Dépenses',
    'UBER': 'Uber',
    'TAXI': 'Taxi',
    'ALIMENTATION': 'Alimentation',
    'FOOD': 'Alimentation',
    'TRANSPORT': 'Transport',
    'LOGEMENT': 'Logement',
    'HOUSING': 'Logement',
    'SANTÉ': 'Santé',
    'HEALTH': 'Santé',
    'LOISIRS': 'Loisirs',
    'LEISURE': 'Loisirs',
}

# Subcategory variations
SUBCATEGORY_ALIASES = {
    'SALAIRE': 'Salaire',
    'SALARY': 'Salaire',
    'FREELANCE': 'Freelance',
    'FREELANCER': 'Freelance',
    'INVESTISSEMENT': 'Investissement',
    'INVESTMENT': 'Investissement',
    'RESTAURANT': 'Restaurant',
    'COURSES': 'Courses',
    'GROCERY': 'Courses',
    'ESSENCE': 'Essence',
    'GAS': 'Essence',
    'CARBURANT': 'Essence',
    'LOYER': 'Loyer',
    'RENT': 'Loyer',
    'FACTURES': 'Factures',
    'BILLS': 'Factures',
}


def normalize_with_aliases(
    category: Optional[str],
    use_aliases: bool = False
) -> Optional[str]:
    """
    Normalize with optional alias mapping.

    If use_aliases=True, applies predefined mappings for common variations.

    Args:
        category: Raw category name
        use_aliases: Whether to apply alias mappings

    Returns:
        Normalized (and optionally aliased) category name

    Example:
        >>> normalize_with_aliases("UBER", use_aliases=True)
        'Uber'
    """
    normalized = normalize_category(category)

    if not normalized or not use_aliases:
        return normalized

    # Check aliases
    upper_normalized = normalized.upper()

    if upper_normalized in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[upper_normalized]

    return normalized


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def is_valid_category(category: Optional[str]) -> bool:
    """
    Check if a category name is valid (non-empty after normalization).

    Args:
        category: Category name to validate

    Returns:
        True if valid, False otherwise
    """
    normalized = normalize_category(category)
    return normalized is not None and len(normalized) > 0


def validate_categories(
    category: Optional[str],
    subcategory: Optional[str]
) -> tuple[bool, Optional[str]]:
    """
    Validate both category and subcategory.

    Args:
        category: Category name
        subcategory: Subcategory name

    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if both are valid
        error_message: Describes what's invalid, or None if valid

    Example:
        >>> is_valid, error = validate_categories("UBER", "ride")
        >>> is_valid
        True
    """
    if not is_valid_category(category):
        return False, "Category cannot be empty"

    if not is_valid_category(subcategory):
        return False, "Subcategory cannot be empty"

    return True, None
