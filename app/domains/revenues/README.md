# Revenues Domain

## Structure

```
revenues/
├── service.py            # is_uber_transaction, process_uber_revenue
├── revenues_service.py   # Business logic layer
├── revenues_db.py       # Database layer
└── pages/
    └── revenues.py      # UI layer
```

## Refactoring Accompli

**Avant** : `revenues.py` (297 lignes, 1 fonction monolithique)

**Après** : 3 couches séparées
- `revenues_service.py` - 6 fonctions métier
- `revenues_db.py` - 3 fonctions DB
- `pages/revenues.py` - 2 fonctions UI

## Principe

**Séparation claire** :
1. **Service** : Scan, parse, validate
2. **Database** : Save, move, log
3. **UI** : Render, forms only

Chaque fonction = 1 responsabilité ✅
