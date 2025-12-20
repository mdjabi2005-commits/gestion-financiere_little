# Shared UI Module

Composants UI réutilisables à travers toute l'application.

## Structure

```
shared/ui/
├── styles.py                    # Styles globaux
├── helpers.py                   # Utilitaires UI
├── error_handler.py             # Gestion d'erreurs UI
├── toast_components.py          # Notifications toast
│
├── components/                  # Composants génériques
│   └── (cards, inputs, etc.)
│
├── financial_tree_component/    # Arbre financier D3.js
│   └── (tree visualization)
│
└── sunburst_navigation/         # Navigation sunburst
    └── (fractal navigation)
```

## Usage

```python
# Styles et helpers
from shared.ui import load_all_styles, refresh_and_rerun

# Notifications
from shared.ui import toast_success, toast_error

# Error handling
from shared.ui import display_error, handle_errors

# Composants spécifiques
from shared.ui.components import ...
from shared.ui.financial_tree_component import ...
from shared.ui.sunburst_navigation import ...
```

## Principe

**Réutilisabilité** : Composants partagés entre domaines
**Indépendance** : Pas de logique métier ici
**UI uniquement** : Display, interactions, styles
