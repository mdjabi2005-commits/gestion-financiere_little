# Shared Services

Services partagés entre plusieurs domaines métier.

## Structure

```
shared/services/
├── __init__.py
├── recurrence.py       # Gestion récurrences
├── files.py            # Gestion fichiers associés
└── fractal.py          # Construction arbre fractal
```

## Services

### Recurrence (`recurrence.py`)
Gestion des transactions récurrentes.

**Fonctions**:
- `backfill_recurrences_to_today()` - Génère transactions récurrentes jusqu'à aujourd'hui

**Usage**:
```python
from shared.services import backfill_recurrences_to_today

backfill_recurrences_to_today(db_path)
```

### Files (`files.py`)
Gestion des fichiers associés aux transactions (tickets, PDFs).

**Fonctions**:
- `trouver_fichiers_associes()` - Trouve fichiers d'une transaction
- `deplacer_fichiers_associes()` - Déplace fichiers lors changement catégorie
- `supprimer_fichiers_associes()` - Supprime fichiers d'une transaction

**Usage**:
```python
from shared.services import trouver_fichiers_associes

fichiers = trouver_fichiers_associes(transaction)
```

### Fractal (`fractal.py`)
Construction de la hiérarchie fractale pour navigation.

**Fonctions**:
- `build_fractal_hierarchy()` - Construit arbre dynamique des catégories

**Usage**:
```python
from shared.services import build_fractal_hierarchy

hierarchy = build_fractal_hierarchy()
```

## Principe

**Pourquoi shared/ ?**
- Services utilisés par plusieurs domaines
- Logique métier partagée
- Pas spécifique à un domain unique

**Alternative**: Si service devient spécifique à un domaine, le déplacer dans ce domaine.
