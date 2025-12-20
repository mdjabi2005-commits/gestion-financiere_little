# 📁 Dossier `/modules/ui/sunburst_navigation`

## 🎯 But du dossier

Ce dossier contient un **composant Streamlit custom complet** - une navigation hiérarchique circulaire (Sunburst) avec communication bidirectionnelle Python ↔ JavaScript.

---

## 🌀 Qu'est-ce qu'un Sunburst ?

Un **graphique Sunburst** est une visualisation circulaire en anneaux concentriques où :
- Le centre = racine (Univers Financier)
- 1er anneau = Types (Revenus, Dépenses)
- 2ème anneau = Catégories  
- 3ème anneau = Sous-catégories

**Interactivité** : Cliquer sur une section filtre les transactions par cette catégorie.

---

## 📄 Structure du composant

```
sunburst_navigation/
├── __init__.py                 # Point d'entrée, fonction principale
├── backend.py                  # Logique Python
├── frontend/
│   ├── index.html             # Structure HTML
│   ├── sunburst.js            # Logique JavaScript principale
│   └── styles.css             # Styles CSS
└── README.md                   # Cette documentation
```

---

## 🔧 Comment ça fonctionne

### Architecture Streamlit Component

Streamlit permet de créer des composants custom avec :
- **Backend Python** : Prépare les données, gère le state
- **Frontend JavaScript** : Affichage et interactions
- **Communication bidirectionnelle** : Python → JS (données), JS → Python (clics)

```
Python (backend.py)
    ↓ (envoie hierarchy)
JavaScript (sunburst.js)
    ↓ (affiche Sunburst)
Utilisateur clique
    ↓ (renvoie node_code)
Python reçoit le clic
    ↓ (filtre les transactions)
```

---

## 📦 Utilisation

### Dans une page Streamlit

```python
from modules.ui.sunburst_navigation import sunburst_navigation
from modules.services.fractal_service import build_fractal_hierarchy

# 1. Construire la hiérarchie
hierarchy = build_fractal_hierarchy()

# 2. Afficher le Sunburst
result = sunburst_navigation(
    hierarchy=hierarchy,
    key="main_sunburst",
    height=600
)

# 3. Utiliser le résultat
if result and result.get('code') != 'TR':
    selected_category = result['label']
    st.write(f"Catégorie sélectionnée : {selected_category}")
    
    # Filtrer les transactions
    df_filtered = df[df['categorie'] == selected_category]
```

---

## 🎨 Fonctionnalités

### 1. Multi-sélection
Possibilité de sélectionner plusieurs catégories en même temps (maintenir Ctrl).

### 2. Réinitialisation
Bouton pour réinitialiser toutes les sélections.

### 3. Couleurs dynamiques
- **Vert** : Revenus
- **Rouge** : Dépenses
- **Surbrillance** : Catégorie sélectionnée

### 4. Tooltips
Au survol, affiche :
- Nom de la catégorie
- Montant total
- Pourcentage du parent

---

## 📋 Format de données (hierarchy)

Le composant attend une hiérarchie au format suivant :

```python
hierarchy = {
    'TR': {
        'code': 'TR',
        'label': 'Univers Financier',
        'total': 5650.00,
        'color': '#ffffff',
        'children': ['REVENUS', 'DEPENSES'],
        'level': 0
    },
    'REVENUS': {
        'code': 'REVENUS',
        'label': 'Revenus',
        'total': 3200.00,
        'color': '#00D4AA',
        'parent': 'TR',
        'children': ['CAT_SALAIRE', ...],
        'level': 1
    },
    'CAT_SALAIRE': {
        'code': 'CAT_SALAIRE',
        'label': 'Salaire',
        'amount': 2500.00,
        'percentage': 78.1,
        'color': '#10b981',
        'parent': 'REVENUS',
        'children': [...],
        'transactions': 5,
        'level': 2
    }
}
```

Généré par `modules.services.fractal_service.build_fractal_hierarchy()`.

---

## 🔄 Communication Python ↔ JavaScript

### Python → JavaScript

```python
# backend.py
def sunburst_navigation(hierarchy, key="sunburst", height=600):
    component_value = _component_func(
        hierarchy=hierarchy,  # Envoyé au JS
        key=key,
        height=height
    )
    return component_value
```

### JavaScript → Python

```javascript
// sunburst.js
function onNodeClick(node) {
    // Renvoyer le node à Python
    Streamlit.setComponentValue({
        code: node.code,
        label: node.label,
        amount: node.amount
    });
}
```

---

## 🎯 Cas d'usage dans l'app

### transactions.py

```python
# Arbre dynamique pour filtrage
with col_tree:
    st.subheader("🌳 Arbre Dynamique")
    hierarchy = build_fractal_hierarchy()
    
    tree_result = sunburst_navigation(
        hierarchy=hierarchy,
        key="tree_transactions",
        height=500
    )
    
    # Filtrer selon la sélection
    if tree_result and tree_result['code'] != 'TR':
        # Extraire catégorie/sous-catégorie depuis le code
        if tree_result['code'].startswith('CAT_'):
            category = tree_result['label']
            df_filtered = df[df['categorie'] == category]
        
        elif tree_result['code'].startswith('SUBCAT_'):
            subcategory = tree_result['label']
            df_filtered = df[df['sous_categorie'] == subcategory]
```

---

## ⚙️ Personnalisation

### Modifier les couleurs

Dans `backend.py` ou directement dans la hiérarchie :

```python
hierarchy['REVENUS']['color'] = '#custom_green'
hierarchy['DEPENSES']['color'] = '#custom_red'
```

### Modifier la hauteur

```python
sunburst_navigation(hierarchy, height=800)  # Plus grand
```

### Désactiver multi-sélection

Modifier `sunburst.js` (ligne ~150) :
```javascript
const MULTI_SELECT_ENABLED = false;
```

---

## 🔧 Développement du composant

### Structure des fichiers

**`__init__.py`** :
- Déclaration du composant
- Point d'entrée
- Export de la fonction `sunburst_navigation()`

**`backend.py`** :
- Logique Python
- Préparation des données
- Gestion du state Streamlit

**`frontend/index.html`** :
- Container HTML
- Import des scripts JS
- Charge D3.js depuis CDN

**`frontend/sunburst.js`** :
- Rendu D3.js du Sunburst
- Gestion des clics
- Communication avec Streamlit

**`frontend/styles.css`** :
- Styles CSS du composant
- Animations
- Responsive design

---

## 🚀 Rebuild après modifications

Si tu modifies le code JavaScript ou CSS :

```bash
cd modules/ui/sunburst_navigation
streamlit run __init__.py  # Test le composant isolé

# Ou simplement relancer l'app
streamlit run main.py
```

Streamlit recharge automatiquement les composants custom.

---

## 📚 Ressources

- **Streamlit Components** : https://docs.streamlit.io/library/components
- **D3.js Sunburst** : https://observablehq.com/@d3/sunburst
- **API Communication** : https://docs.streamlit.io/library/components/components-api

---

## ✅ Points clés

1. **Composant custom complet** avec Python + JavaScript
2. **Communication bidirectionnelle** sophistiquée
3. **Réutilisable** facilement dans n'importe quelle page
4. **Visuellement riche** et interactif
5. **Intégration parfaite** avec le reste de l'app Streamlit

C'est un des composants les plus complexes de l'application ! 🌟
