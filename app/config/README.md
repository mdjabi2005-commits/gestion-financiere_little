# 📁 Dossier `/config`

## 🎯 But du dossier

Ce dossier centralise **toute la configuration de l'application** : chemins de fichiers, paramètres de base de données, configuration OCR, et paramètres d'interface. C'est le point central pour modifier les comportements globaux de l'application.

---

## 📄 Fichiers

### 1. `__init__.py`

**Rôle** : Point d'entrée du module de configuration. Exporte toutes les constantes de configuration pour un accès facile depuis n'importe où dans le projet.

**Exports principaux** :
```python
from .paths import (
    DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR,
    REVENUS_A_TRAITER, REVENUS_TRAITES, PROBLEMATIC_DIR,
    OCR_LOGS_DIR, LOG_PATH, OCR_PERFORMANCE_LOG,
    PATTERN_STATS_LOG, OCR_SCAN_LOG, POTENTIAL_PATTERNS_LOG,
    CSV_EXPORT_DIR, CSV_TRANSACTIONS_SANS_TICKETS
)

from .database_config import (
    DATABASE_PATH, DATABASE_TIMEOUT,
    TRANSACTIONS_SCHEMA, TRANSACTION_TYPES,
    CATEGORIES_DEPENSES, CATEGORIES_REVENUS,
    RECURRENCE_OPTIONS
)

from .ocr_config import (
    UBER_TAX_RATE, UBER_NET_MULTIPLIER, UBER_KEYWORDS,
    OCR_SUCCESS_THRESHOLD, OCR_DETECTION_MINIMUM,
    SUCCESS_LEVELS, PATTERN_RELIABILITY
)

from .ui_config import (
    APP_TITLE, PAGE_ICON, LAYOUT_MODE,
    SIDEBAR_STATE, COLORS
)
```

**Utilisation** :
```python
# Import simple de n'importe où
from config import DB_PATH, CATEGORIES_DEPENSES, UBER_TAX_RATE
```

---

### 2. `paths.py`

**Rôle** : Définit **tous les chemins de fichiers et répertoires** utilisés par l'application.

#### Configuration des chemins

**Répertoire racine** :
```python
DATA_DIR = str(Path.home() / "analyse")
# Emplacement : C:\Users\<user>\analyse (ou /home/<user>/analyse sur Linux)
```

**Base de données** :
```python
DB_PATH = os.path.join(DATA_DIR, "finances.db")
# Fichier SQLite contenant toutes les transactions
```

**Scan de tickets** :
```python
TO_SCAN_DIR = os.path.join(DATA_DIR, "tickets_a_scanner")
# Dossier où déposer les tickets JPG/PNG à scanner

SORTED_DIR = os.path.join(DATA_DIR, "tickets_tries")
# Dossier où les tickets sont archivés par catégorie/sous-catégorie

PROBLEMATIC_DIR = os.path.join(DATA_DIR, "tickets_problematiques")
# Tickets dont l'OCR a échoué
```

**Scan de revenus** :
```python
REVENUS_A_TRAITER = os.path.join(DATA_DIR, "revenus_a_traiter")
# PDFs de fiches de paie à traiter

REVENUS_TRAITES = os.path.join(DATA_DIR, "revenus_traites")
# PDFs traités archivés
```

**Logs OCR** :
```python
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
POTENTIAL_PATTERNS_LOG = os.path.join(OCR_LOGS_DIR, "potential_patterns.jsonl")
```

**Export CSV** :
```python
CSV_EXPORT_DIR = os.path.join(DATA_DIR, "exports")
CSV_TRANSACTIONS_SANS_TICKETS = os.path.join(CSV_EXPORT_DIR, "transactions_sans_tickets.csv")
```

#### Création automatique

Tous les dossiers sont créés automatiquement au démarrage :
```python
for directory in [DATA_DIR, TO_SCAN_DIR, SORTED_DIR, PROBLEMATIC_DIR,
                  REVENUS_A_TRAITER, REVENUS_TRAITES, OCR_LOGS_DIR, CSV_EXPORT_DIR]:
    os.makedirs(directory, exist_ok=True)
```

#### Exemples d'utilisation

**Scanner des tickets** :
```python
from config import TO_SCAN_DIR, SORTED_DIR
import os

# Lister les fichiers à scanner
files = os.listdir(TO_SCAN_DIR)

for filename in files:
    input_path = os.path.join(TO_SCAN_DIR, filename)
    # Traitement OCR...
    output_path = os.path.join(SORTED_DIR, "Alimentation/Restaurant", filename)
    shutil.move(input_path, output_path)
```

**Accès à la base de données** :
```python
from config import DB_PATH
import sqlite3

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT * FROM transactions")
```

---

### 3. `database_config.py`

**Rôle** : Configuration de la base de données SQLite et définition des catégories prédéfinies.

#### Paramètres de connexion

```python
DATABASE_PATH = DB_PATH  # Chemin du fichier .db
DATABASE_TIMEOUT = 30.0  # Timeout en secondes pour éviter les locks
```

#### Schéma de la table transactions

```python
TRANSACTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,                    -- 'Dépense' ou 'Revenu'
    categorie TEXT NOT NULL,               -- Catégorie principale
    sous_categorie TEXT,                   -- Sous-catégorie (optionnel)
    description TEXT,                      -- Description libre
    montant REAL NOT NULL,                 -- Montant en euros
    date TEXT NOT NULL,                    -- Format ISO 'YYYY-MM-DD'
    source TEXT DEFAULT 'Manuel',          -- 'OCR', 'Manuel', 'CSV Import', etc.
    recurrence TEXT,                       -- Type de récurrence
    date_fin TEXT                          -- Date de fin pour récurrences
)
"""
```

#### Types de transactions

```python
TRANSACTION_TYPES = ["Dépense", "Revenu"]
```

#### Catégories prédéfinies

**Dépenses** :
```python
CATEGORIES_DEPENSES = {
    "Alimentation": ["Courses", "Restaurant", "Snacks"],
    "Transport": ["Carburant", "Transports publics", "Parking", "Taxi/VTC"],
    "Logement": ["Loyer", "Électricité", "Eau", "Internet", "Assurance habitation"],
    "Santé": ["Médicaments", "Médecin", "Mutuelle"],
    "Loisirs": ["Cinéma", "Sport", "Sorties"],
    "Autres": ["Divers", "Frais bancaires"]
}
```

**Revenus** :
```python
CATEGORIES_REVENUS = {
    "Salaire": ["Salaire net", "Prime", "Heures supplémentaires"],
    "Freelance": ["Mission", "Projet", "Consultation"],
    "Uber": ["Uber Eats", "Uber VTC"],
    "Aide": ["CAF", "Aide familiale"],
    "Autres": ["Divers", "Remboursement"]
}
```

#### Options de récurrence

```python
RECURRENCE_OPTIONS = ["Aucune", "Quotidienne", "Hebdomadaire", "Mensuelle", "Annuelle"]
```

#### Exemples d'utilisation

**Afficher les catégories dans un formulaire** :
```python
from config import CATEGORIES_DEPENSES
import streamlit as st

cat = st.selectbox("Catégorie", list(CATEGORIES_DEPENSES.keys()))
sous_cat = st.selectbox("Sous-catégorie", CATEGORIES_DEPENSES[cat])
```

**Créer la table** :
```python
from config import DB_PATH, TRANSACTIONS_SCHEMA
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.execute(TRANSACTIONS_SCHEMA)
conn.commit()
```

---

### 4. `ocr_config.py`

**Rôle** : Configuration de l'OCR (reconnaissance optique) et des taxes Uber.

#### Configuration des taxes Uber

```python
UBER_TAX_RATE = 0.21              # 21% de prélèvement
UBER_NET_MULTIPLIER = 0.79        # Montant net = brut × 0.79
UBER_KEYWORDS = ['uber']          # Mots-clés pour détecter Uber (case-insensitive)
```

**Utilisation** :
```python
from config import UBER_TAX_RATE, UBER_KEYWORDS

# Détection Uber
if any(keyword in description.lower() for keyword in UBER_KEYWORDS):
    montant_net = montant_brut * (1 - UBER_TAX_RATE)
    # Créer transaction URSSAF automatiquement
    urssaf_amount = montant_brut * UBER_TAX_RATE
```

#### Seuils de performance OCR

```python
OCR_SUCCESS_THRESHOLD = 0.5       # Taux de succès minimum (50%)
OCR_DETECTION_MINIMUM = 3         # Minimum de détections requises

SUCCESS_LEVELS = {
    'excellent': 0.9,  # 90%+
    'good': 0.7,       # 70-89%
    'partial': 0.5,    # 50-69%
    'poor': 0.0        # < 50%
}
```

**Utilisation** :
```python
from config import OCR_SUCCESS_THRESHOLD, SUCCESS_LEVELS

success_rate = detections_reussies / total_detections

if success_rate >= SUCCESS_LEVELS['excellent']:
    status = "Excellent"
elif success_rate >= SUCCESS_LEVELS['good']:
    status = "Bon"
elif success_rate >= OCR_SUCCESS_THRESHOLD:
    status = "Partiel"
else:
    status = "Mauvais"
```

#### Fiabilité des patterns

```python
PATTERN_RELIABILITY = {
    'high': 50,        # 50+ détections
    'medium': 10,      # 10-49 détections
    'low': 0           # < 10 détections
}
```

**Utilisation** :
```python
from config import PATTERN_RELIABILITY

if pattern_count >= PATTERN_RELIABILITY['high']:
    reliability = "Haute fiabilité"
elif pattern_count >= PATTERN_RELIABILITY['medium']:
    reliability = "Fiabilité moyenne"
else:
    reliability = "Fiabilité faible"
```

---

### 5. `ui_config.py`

**Rôle** : Configuration de l'interface Streamlit (titre, couleurs, layout).

**Contenu typique** :
```python
APP_TITLE = "Gestio V4 - Gestion Financière"
PAGE_ICON = "💰"
LAYOUT_MODE = "wide"
SIDEBAR_STATE = "expanded"

COLORS = {
    'revenue': '#00D4AA',      # Vert pour revenus
    'expense': '#FF6B6B',      # Rouge pour dépenses
    'balance_positive': '#00D4AA',
    'balance_negative': '#FF6B6B',
    'warning': '#FFD93D'       # Jaune pour avertissements
}
```

**Utilisation** :
```python
from config import APP_TITLE, PAGE_ICON, LAYOUT_MODE

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT_MODE
)
```

---

## 🔗 Dépendances

- `os` : Manipulation de chemins
- `pathlib.Path` : Chemins cross-platform
- Aucune dépendance externe requise

---

## ⚠️ Points clés

1. **Centralisation totale** : Modifier un paramètre ici affecte toute l'application
2. **Création automatique** : Les dossiers sont créés au démarrage
3. **Import simplifié** : `from config import VAR` depuis n'importe où
4. **Chemins absolus** : Utilise `Path.home()` pour compatibilité multi-OS

---

## 🔄 Workflow typique

```python
# 1. Import de la config
from config import (
    TO_SCAN_DIR,
    SORTED_DIR,
    DB_PATH,
    CATEGORIES_DEPENSES,
    UBER_TAX_RATE
)

# 2. Utilisation dans l'application
import os
import sqlite3

# Scanner un dossier
tickets = os.listdir(TO_SCAN_DIR)

# Connexion DB
conn = sqlite3.connect(DB_PATH)

# Utiliser les catégories
for cat, subcats in CATEGORIES_DEPENSES.items():
    print(f"{cat}: {subcats}")

# Calculer taxe Uber
net_amount = brut_amount * (1 - UBER_TAX_RATE)
```

---

## 💡 Modifications futures possibles

### Chemins cloud
```python
# Ajouter support cloud
CLOUD_BACKUP_DIR = "s3://mon-bucket/finances/"
ENABLE_CLOUD_SYNC = True
```

### Nouvelles catégories
```python
# Ajouter à database_config.py
CATEGORIES_DEPENSES["Éducation"] = ["Livres", "Cours", "Formation"]
```

### Configuration API
```python
# Ajouter un nouveau fichier api_config.py
API_KEYS = {
    'ocr_service': os.getenv('OCR_API_KEY'),
    'backup_service': os.getenv('BACKUP_API_KEY')
}
```

---

## 📊 Impact de la configuration

| Fichier | Impact sur | Exemple de changement |
|---------|-----------|----------------------|
| `paths.py` | Localisation des données | Changer `DATA_DIR` pour utiliser un autre disque |
| `database_config.py` | Structure des données | Ajouter une nouvelle catégorie |
| `ocr_config.py` | Précision OCR | Ajuster les seuils de confiance |
| `ui_config.py` | Apparence | Modifier les couleurs du thème |
