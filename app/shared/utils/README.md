# 📁 Dossier `/modules/utils`

## 🎯 But du dossier

Ce module contient des **fonctions utilitaires réutilisables** utilisées partout dans l'application : conversions, validations, formatage, constantes.

---

## 📄 Fichiers

### 1. `converters.py`
**Rôle** : Conversion sécurisée de données (strings → nombres, dates, etc.)

**Fonctions** :

**`safe_convert(value, target_type, default)`**
Conversion sécurisée avec fallback :
```python
from modules.utils.converters import safe_convert

montant = safe_convert("45.50", float, 0.0)  # 45.5
montant = safe_convert("abc", float, 0.0)    # 0.0 (pas d'erreur)
```

**`safe_date_convert(date_str, default=None)`**
Conversion de string vers date :
```python
from modules.utils.converters import safe_date_convert

date = safe_date_convert("2025-01-15")  # date(2025, 1, 15)
date = safe_date_convert("invalide")    # None
```

**`parse_french_date(date_str)`**
Parse les dates au format français (jj/mm/aaaa) :
```python
date = parse_french_date("15/01/2025")  # date(2025, 1, 15)
```

**`convert_montant_to_float(montant_str)`**
Convertit un montant avec virgule française :
```python
montant = convert_montant_to_float("45,50 €")  # 45.5
montant = convert_montant_to_float("1 234,56") # 1234.56
```

---

###  2. `formatters.py`
**Rôle** : Formatage de données pour affichage.

**Fonctions** :

**`format_currency(amount: float) -> str`**
Formate un montant en euros :
```python
from modules.utils.formatters import format_currency

print(format_currency(1234.56))  # "1 234,56 €"
print(format_currency(45.5))     # "45,50 €"
```

**`format_date(date_obj) -> str`**
Formate une date au format français :
```python
from datetime import date
from modules.utils.formatters import format_date

print(format_date(date(2025, 1, 15)))  # "15/01/2025"
```

**`format_percentage(value: float) -> str`**
Formate un pourcentage :
```python
print(format_percentage(0.2175))  # "21,75 %"
```

---

### 3. `validators.py`
**Rôle** : Validation de données avant insertion/traitement.

**Fonctions** :

**`validate_transaction(transaction: dict) -> tuple[bool, str]`**
Valide une transaction complète :
```python
from modules.utils.validators import validate_transaction

valid, error = validate_transaction({
    'type': 'Dépense',
    'categorie': 'Alimentation',
    'montant': 45.50,
    'date': '2025-01-15'
})

if not valid:
    print(f"Erreur: {error}")
```

**`is_valid_montant(montant: float) -> bool`**
Vérifie si un montant est valide :
```python
is_valid_montant(45.50)   # True
is_valid_montant(-10)     # False
is_valid_montant(0)       # False
```

**`is_valid_date(date_str: str) -> bool`**
Vérifie la validité d'une date :
```python
is_valid_date("2025-01-15")  # True
is_valid_date("invalide")    # False
```

---

### 4. `constants.py`
**Rôle** : Constantes globales utilisées dans l'application.

**Constantes définies** :

```python
# Formats de dates
DATE_FORMAT_ISO = "%Y-%m-%d"
DATE_FORMAT_FR = "%d/%m/%Y"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Limites
MAX_MONTANT = 1000000.0  # 1 million max
MIN_MONTANT = 0.01       # 1 centime min

# Extensions de fichiers
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.pdf']
SUPPORTED_PDF_FORMATS = ['.pdf']

# Sources de transactions
SOURCE_MANUAL = "Manuel"
SOURCE_OCR = "OCR"
SOURCE_CSV = "CSV Import"
SOURCE_RECURRENCE = "recurrence_auto"

# Couleurs (correspondant à ui_config.py)
COLOR_REVENUE = '#00D4AA'
COLOR_EXPENSE = '#FF6B6B'
COLOR_WARNING = '#FFD93D'
```

**Utilisation** :
```python
from modules.utils.constants import MAX_MONTANT, SOURCE_OCR

if montant > MAX_MONTANT:
    raise ValueError("Montant trop élevé")

transaction['source'] = SOURCE_OCR
```

---

## 🔗 Dépendances

**Externes** :
- `datetime` - Manipulation de dates
- `decimal` - Précision monétaire
- `re` - Expressions régulières

**Aucune dépendance interne** - Ce sont des utilitaires bas niveau

---

## 💡 Exemples d'usage courants

**Convertir un montant saisi** :
```python
from modules.utils.converters import safe_convert, convert_montant_to_float

# Input utilisateur
user_input = "45,50 €"

# Conversion sécurisée
montant = convert_montant_to_float(user_input)  # 45.5

# Ou conversion générique
montant = safe_convert(user_input.replace(',', '.'), float, 0.0)
```

**Valider avant d'insérer** :
```python
from modules.utils.validators import validate_transaction

transaction = {...}
valid, error = validate_transaction(transaction)

if valid:
    TransactionRepository.insert(transaction)
else:
    st.error(f"Transaction invalide : {error}")
```

**Afficher formaté** :
```python
from modules.utils.formatters import format_currency, format_date
from datetime import date

montant = 1234.56
date_trans = date(2025, 1, 15)

print(f"{format_date(date_trans)} : {format_currency(montant)}")
# "15/01/2025 : 1 234,56 €"
```

---

## ⚠️ Points clés

1. **Sécurité avant tout** : Les converters ne lèvent jamais d'exceptions
2. **Format français** : Virgules pour décimales, espaces pour milliers
3. **Validation stricte** : Empêche les données invalides en base
4. **Réutilisables** : Aucune dépendance au domaine métier
5. **Testables** : Fonctions pures faciles à tester

---

## 🎯 Bonnes pratiques

**✅ À FAIRE** :
```python
# Toujours valider les inputs utilisateur
montant = safe_convert(user_input, float, 0.0)

# Valider avant insertion
valid, error = validate_transaction(data)
if not valid:
    handle_error(error)
```

**❌ À ÉVITER** :
```python
# Ne PAS convertir sans sécurité
montant = float(user_input)  # ❌ Peut crasher

# Ne PAS insérer sans valider
TransactionRepository.insert(data)  # ❌ Données potentiellement invalides
```
