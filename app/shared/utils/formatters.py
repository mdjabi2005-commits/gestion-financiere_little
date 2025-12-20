"""Formatting utilities."""

from typing import Optional
from .constants import MONTHS_DICT, MONTHS_REVERSE


def numero_to_mois(num: str) -> str:
    """
    Convert month number to French month name.

    Args:
        num: Month number as string ("01" to "12")

    Returns:
        French month name or "inconnu" if invalid

    Examples:
        >>> numero_to_mois("01")
        'janvier'
        >>> numero_to_mois("12")
        'décembre'
        >>> numero_to_mois("99")
        'inconnu'
    """
    return MONTHS_REVERSE.get(num, "inconnu")


def mois_to_numero(mois: str) -> Optional[str]:
    """
    Convert French month name to month number.

    Args:
        mois: French month name (case-insensitive)

    Returns:
        Month number as string ("01" to "12") or None if invalid

    Examples:
        >>> mois_to_numero("janvier")
        '01'
        >>> mois_to_numero("Décembre")
        '12'
        >>> mois_to_numero("invalid")
        None
    """
    return MONTHS_DICT.get(mois.lower())


def format_amount(amount: float, currency: str = "€") -> str:
    """
    Format amount with currency symbol.

    Args:
        amount: Amount to format
        currency: Currency symbol

    Returns:
        Formatted string

    Examples:
        >>> format_amount(1234.56)
        '1,234.56€'
        >>> format_amount(100, "$")
        '100.00$'
    """
    return f"{amount:,.2f}{currency}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format value as percentage.

    Args:
        value: Value between 0 and 1
        decimals: Number of decimal places

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.215)
        '21.5%'
        >>> format_percentage(0.5, 0)
        '50%'
    """
    return f"{value * 100:.{decimals}f}%"
