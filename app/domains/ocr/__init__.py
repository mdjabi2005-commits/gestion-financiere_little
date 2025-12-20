# OCR Domain

# Import only what's needed, avoid circular imports
from .scanner import full_ocr
from .parsers import parse_ticket_metadata_v2
from .parsers_OLD_BACKUP import parse_uber_pdf, parse_fiche_paie

# pattern_manager will be imported directly when needed to avoid circular imports

__all__ = [
    'full_ocr',
    'parse_ticket_metadata_v2',
    'parse_uber_pdf',
    'parse_fiche_paie'
]
