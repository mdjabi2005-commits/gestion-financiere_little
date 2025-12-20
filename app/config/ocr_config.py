"""OCR and tax configuration."""

# ==============================
# TAX CONFIGURATION
# ==============================

# Uber tax rate (21% tax = 79% net)
UBER_TAX_RATE = 0.21
UBER_NET_MULTIPLIER = 1 - UBER_TAX_RATE  # 0.79

# Keywords to identify Uber transactions
# Only "uber" keyword (case-insensitive) to be strict
UBER_KEYWORDS = [
    'uber'
]

# ==============================
# OCR PERFORMANCE THRESHOLDS
# ==============================

# Success rate threshold (50%)
OCR_SUCCESS_THRESHOLD = 0.5

# Minimum number of detections required
OCR_DETECTION_MINIMUM = 3

# Success level thresholds
SUCCESS_LEVELS = {
    'excellent': 0.9,  # 90%+
    'good': 0.7,       # 70-89%
    'partial': 0.5,    # 50-69%
    'poor': 0.0        # Below 50%
}

# Pattern reliability thresholds
PATTERN_RELIABILITY = {
    'high': 50,        # 50+ detections
    'medium': 10,      # 10-49 detections
    'low': 0           # Below 10
}
