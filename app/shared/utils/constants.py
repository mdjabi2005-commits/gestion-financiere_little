"""Constants used throughout the application."""

# ==============================
# MONTHS DICTIONARIES
# ==============================

MONTHS_DICT = {
    "janvier": "01",
    "février": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "août": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "décembre": "12"
}

# Reverse mapping for number to month name
MONTHS_REVERSE = {v: k for k, v in MONTHS_DICT.items()}

# ==============================
# FILE EXTENSIONS
# ==============================

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
PDF_EXTENSIONS = ['.pdf']
DOCUMENT_EXTENSIONS = IMAGE_EXTENSIONS + PDF_EXTENSIONS

# ==============================
# OCR PATTERNS
# ==============================

# Common patterns found in receipts
AMOUNT_PATTERNS = [
    r'total\s*:?\s*(\d+[.,]\d{2})',
    r'montant\s*:?\s*(\d+[.,]\d{2})',
    r'prix\s*:?\s*(\d+[.,]\d{2})',
    r'(\d+[.,]\d{2})\s*€',
    r'€\s*(\d+[.,]\d{2})'
]

DATE_PATTERNS = [
    r'(\d{2}[/-]\d{2}[/-]\d{4})',
    r'(\d{4}[/-]\d{2}[/-]\d{2})',
    r'(\d{2}\.\d{2}\.\d{4})'
]

# ==============================
# TRANSACTION DEFAULTS
# ==============================

DEFAULT_CATEGORY = "Autres"
DEFAULT_SOURCE = "Manuel"
DEFAULT_RECURRENCE = "Aucune"

# ==============================
# UI CONSTANTS
# ==============================

ITEMS_PER_PAGE = 20
MAX_FILE_SIZE_MB = 10
MAX_UPLOAD_FILES = 50

# ==============================
# NOTIFICATION DURATIONS
# ==============================

TOAST_DURATION_SUCCESS = 3000  # ms
TOAST_DURATION_WARNING = 5000  # ms
TOAST_DURATION_ERROR = 7000    # ms
