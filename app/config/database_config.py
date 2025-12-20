"""Database configuration."""

from .paths import DB_PATH

# ==============================
# DATABASE SETTINGS
# ==============================

DATABASE_PATH = DB_PATH
DATABASE_TIMEOUT = 30.0  # seconds

# ==============================
# TABLE SCHEMAS
# ==============================

TRANSACTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    categorie TEXT NOT NULL,
    sous_categorie TEXT,
    description TEXT,
    montant REAL NOT NULL,
    date TEXT NOT NULL,
    source TEXT DEFAULT 'Manuel',
    recurrence TEXT,
    date_fin TEXT
)
"""

# ==============================
# TRANSACTION TYPES
# ==============================

TRANSACTION_TYPES = ["Dépense", "Revenu"]

# ==============================
# CATEGORIES
# ==============================

CATEGORIES_DEPENSES = {
    "Alimentation": ["Courses", "Restaurant", "Snacks"],
    "Transport": ["Carburant", "Transports publics", "Parking", "Taxi/VTC"],
    "Logement": ["Loyer", "Électricité", "Eau", "Internet", "Assurance habitation"],
    "Santé": ["Médicaments", "Médecin", "Mutuelle"],
    "Loisirs": ["Cinéma", "Sport", "Sorties"],
    "Autres": ["Divers", "Frais bancaires"]
}

CATEGORIES_REVENUS = {
    "Salaire": ["Salaire net", "Prime", "Heures supplémentaires"],
    "Freelance": ["Mission", "Projet", "Consultation"],
    "Uber": ["Uber Eats", "Uber VTC"],
    "Aide": ["CAF", "Aide familiale"],
    "Autres": ["Divers", "Remboursement"]
}

# ==============================
# RECURRENCE OPTIONS
# ==============================

RECURRENCE_OPTIONS = ["Aucune", "Quotidienne", "Hebdomadaire", "Mensuelle", "Annuelle"]
