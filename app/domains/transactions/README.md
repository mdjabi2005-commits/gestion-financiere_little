# Transactions Domain

## Structure

```
transactions/
├── models.py              # Transaction, Recurrence models
├── repository.py          # TransactionRepository (DB access)
├── service.py            # normalize_category, normalize_subcategory
└── pages/
    ├── add.py            # Add transaction UI
    └── view.py           # View transactions UI
```

## Responsabilités

**Service** : Logique métier (normalisation, validation)
**Repository** : Accès base de données
**Pages** : Interface Streamlit (UI uniquement)

## Usage

```python
from domains.transactions import TransactionRepository, normalize_category

# Service
cat = normalize_category("alimentation")

# Repository  
repo = TransactionRepository()
df = repo.get_all()
```

## Principe

**Séparation des couches** : Chaque fichier a UNE responsabilité.
- `service.py` = Business logic
- `repository.py` = Database
- `pages/*.py` = UI only
