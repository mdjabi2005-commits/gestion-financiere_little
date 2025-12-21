import os
from pathlib import Path

# Base directories
_home = Path.home()
_desktop = _home / "Desktop"  # Bureau utilisateur

# TEST MODE - Switch between production and test databases
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'


# Folder paths - Production layout
if TEST_MODE:
    # Mode test : tout dans ~/test
    DATA_DIR = str(_home / "test")
    INPUT_DIR = str(_home / "test")
    print("⚠️ MODE TEST ACTIVÉ - Utilisation de ~/test")
else:
    # Mode production : dossiers logiques pour utilisateurs
    INPUT_DIR = str(_desktop)  # Dossiers d'entrée sur le bureau

# Database (dans gestion-financière)
DB_PATH = os.path.join(INPUT_DIR, "finances.db")

# Input directories (sur le Bureau pour faciliter l'accès)
TO_SCAN_DIR = os.path.join(INPUT_DIR, "tickets_a_scanner")
REVENUS_A_TRAITER = os.path.join(INPUT_DIR, "revenus_a_traiter")

# Processing directories (dans gestion-financière)
SORTED_DIR = os.path.join(INPUT_DIR, "tickets_tries")
PROBLEMATIC_DIR = os.path.join(INPUT_DIR, "tickets_problematiques")
REVENUS_TRAITES = os.path.join(INPUT_DIR, "revenus_traites")

# OCR Logs (dans gestion-financière)
OCR_LOGS_DIR = os.path.join(INPUT_DIR, "ocr_logs")
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
POTENTIAL_PATTERNS_LOG = os.path.join(OCR_LOGS_DIR, "potential_patterns.jsonl")

# CSV Export (dans gestion-financière)
CSV_EXPORT_DIR = os.path.join(INPUT_DIR, "exports")
CSV_TRANSACTIONS_SANS_TICKETS = os.path.join(CSV_EXPORT_DIR, "transactions_sans_tickets.csv")

# Create directories
for directory in [INPUT_DIR, TO_SCAN_DIR, SORTED_DIR, PROBLEMATIC_DIR,
                  REVENUS_A_TRAITER, REVENUS_TRAITES, OCR_LOGS_DIR, CSV_EXPORT_DIR]:
    os.makedirs(directory, exist_ok=True)
