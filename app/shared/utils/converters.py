"""Type conversion utilities with format detection."""

import re
import logging
import pandas as pd
from datetime import datetime
from dateutil import parser
from typing import Any, Type, Optional, Union

logger = logging.getLogger(__name__)


def safe_convert(
    value: Any,
    convert_type: Type = float,
    default: Union[float, int, str] = 0.0
) -> Union[float, int, str]:
    """
    Safely convert a value to the specified type with automatic format detection.

    For float conversion, automatically detects European (1.234,56) vs American (1,234.56) format.

    Args:
        value: Value to convert
        convert_type: Target type (float, int, or str)
        default: Default value if conversion fails

    Returns:
        Converted value or default if conversion fails

    Examples:
        >>> safe_convert("1.234,56", float)
        1234.56
        >>> safe_convert("1,234.56", float)
        1234.56
        >>> safe_convert("invalid", float, 0.0)
        0.0
    """
    try:
        if pd.isna(value) or value is None or str(value).strip() == "":
            return default

        value_str = str(value).strip()

        if convert_type == float:
            # Clean the value: remove spaces, currency symbols, quotes
            value_str = value_str.replace(' ', '').replace('€', '').replace('"', '').replace("'", "")

            # === AUTOMATIC FORMAT DETECTION ===
            # Rule: The LAST symbol (. or ,) is the decimal separator

            last_comma = value_str.rfind(',')
            last_dot = value_str.rfind('.')

            if last_comma > last_dot:
                # European format: 1.234,56 or 1234,56
                # Comma is the decimal separator
                value_str = value_str.replace('.', '')  # Remove thousand separators
                value_str = value_str.replace(',', '.')  # Comma → dot for Python
            elif last_dot > last_comma:
                # American format: 1,234.56 or 1234.56
                # Dot is the decimal separator
                value_str = value_str.replace(',', '')  # Remove thousand separators
                # Keep dot as is
            else:
                # Single symbol or none
                # If it's a comma, assume European format
                if ',' in value_str:
                    value_str = value_str.replace(',', '.')

            # Clean everything that's not a digit, dot, or minus sign
            value_str = re.sub(r'[^\d.-]', '', value_str)

            result = float(value_str)
            return round(result, 2)

        elif convert_type == int:
            return int(float(value_str))
        elif convert_type == str:
            return value_str
        else:
            return convert_type(value)

    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Conversion failed for value '{value}': {e}")
        return default


def safe_date_convert(
    date_str: Any,
    default: Optional[datetime] = None
) -> datetime:
    """
    Safely convert a date string to datetime.date with multiple format support.

    Supports formats:
        - ISO: 2025-01-15
        - European: 15/01/2025, 15/01/25, 15-01-2025, 15.01.2025
        - American: 2025/01/15

    Args:
        date_str: Date string to convert
        default: Default date if conversion fails (defaults to today)

    Returns:
        Converted date or default

    Examples:
        >>> safe_date_convert("15/01/2025")
        datetime.date(2025, 1, 15)
        >>> safe_date_convert("2025-01-15")
        datetime.date(2025, 1, 15)
    """
    if default is None:
        default = datetime.now().date()

    if pd.isna(date_str) or date_str is None or str(date_str).strip() == "":
        return default

    date_str = str(date_str).strip()

    # Try common formats first
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y",
        "%Y/%m/%d", "%d-%m-%Y", "%d-%m-%y",
        "%d.%m.%Y", "%d.%m.%y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # Fallback to fuzzy parsing
    try:
        return parser.parse(date_str, dayfirst=True, fuzzy=True).date()
    except Exception:
        logger.warning(f"Date conversion failed for '{date_str}', using default")
        return default
