# 📁 Dossier `/modules/ui/financial_tree_component`

## 🎯 But du dossier

Ce dossier contient un **composant Streamlit custom** pour afficher un **arbre hiérarchique D3.js** des finances avec drag & drop pour réorganiser les catégories.

---

## 🌳 Qu'est-ce que le Financial Tree ?

Un **arbre financier interactif** basé sur D3.js qui permet de :
- Visualiser la hiérarchie Type → Catégorie → Sous-catégorie sous forme d'arbre
- **Drag & drop** pour déplacer des transactions entre catégories
- Afficher les montants à chaque niveau
- Animation fluide lors des interactions

---

## 📄 Structure

```
financial_tree_component/
├── __init__.py                 # Point d'entrée
├── backend.py                  # Logique Python
├── frontend/
│   ├── index.html             # Structure HTML
│   ├── d3_tree.js             # Rendu D3.js de l'arbre
│   ├── sankey_flow.js         # Alternative Sankey (flux)
│   └── styles.css             # Styles CSS
└── README.md                   # Cette documentation
```

---

## 🎨 Fonctionnalités

### 1. Visualisation hiérarchique
Affiche toute la structure financière en arbre :
```
Univers Financier (racine)
├── Revenus
│   ├── Salaire
│   │   └── Salaire Net
│   └── Freelance
│       └── Mission
└── Dépenses
    ├── Alimentation
    │   ├── Courses
    │   └── Restaurant
    └── Transport
        └── Essence
```

### 2. Drag & drop
Glisser-déposer une transaction d'une catégorie à une autre pour la réassigner.

### 3. Couleurs
- **Vert** : Nœuds Revenus
- **Rouge** : Nœuds Dépenses
- **Taille** proportionnelle au montant

### 4. Tooltips
Au survol d'un nœud :
- Nom de la catégorie
- Montant total
- Nombre de transactions

---

## 📦 Utilisation

```python
from modules.ui.financial_tree_component import financial_tree

# Construire la hiérarchie (même format que Sunburst)
from modules.services.fractal_service import build_fractal_hierarchy
hierarchy = build_fractal_hierarchy()

# Afficher l'arbre
result = financial_tree(
    hierarchy=hierarchy,
    key="main_tree",
    height=800
)

# Si drag & drop effectué
if result and result.get('action') == 'move':
    transaction_id = result['transaction_id']
    new_category = result['new_category']
    
    # Mettre à jour la transaction
    TransactionRepository.update_category(
        transaction_id=transaction_id,
        new_category=new_category
    )
```

---

## 🔧 Communication Python ↔ JavaScript

### Python envoie la hiérarchie

```python
# Format identique à sunburst_navigation
hierarchy = {
    'TR': {...},
    'REVENUS': {...},
    'CAT_SALAIRE': {...},
    ...
}

result = financial_tree(hierarchy)
```

### JavaScript renvoie les actions

```javascript
// Quand utilisateur drag & drop
Streamlit.setComponentValue({
    action: 'move',
    transaction_id: 42,
    old_category: 'Transport',
    new_category: 'Alimentation'
});
```

---

## 🎯 Différence avec Sunburst

| Aspect | Sunburst | Financial Tree |
|--------|----------|----------------|
| **Forme** | Cercles concentriques | Arbre hiérarchique |
| **Interaction** | Clic = filtrer | Drag & drop = réassigner |
| **Utilisation** | Navigation/lecture | Modification/réorganisation |
| **Complexité JS** | Moyenne | Élevée (drag & drop) |

**En pratique** :
- **Sunburst** : Utilisé dans `transactions.py` pour filtrer
- **Tree** : Peut être utilisé pour réorganiser les catégories (fonctionnalité avancée)

---

## 🔄 Workflow drag & drop

```
1. Utilisateur clique sur un nœud (ex: transaction "Essence")
    ↓
2. Commence à glisser
    ↓
3. Survole un autre nœud (ex: "Alimentation")
    ↓
4. Relâche (drop)
    ↓
5. JavaScript envoie à Python : {action: 'move', ...}
    ↓
6. Python met à jour la DB
    ↓
7. Rerun pour rafraîchir l'arbre
```

---

## 📂 Fichiers détaillés

### `d3_tree.js`
**Rôle** : Rendu D3.js de l'arbre hiérarchique avec drag & drop.

**Fonctions clés** :
```javascript
function renderTree(hierarchy) {
    // Convertit hiérarchie en données D3
    const root = d3.hierarchy(convertToDTree(hierarchy));
    
    // Créer le layout
    const treeLayout = d3.tree().size([height, width]);
    
    // Afficher les nœuds et liens
    renderNodes(root);
    renderLinks(root);
    
    // Activer drag & drop
    enableDragDrop();
}
```

### `sankey_flow.js`
**Rôle** : Alternative en diagramme de Sankey (flux).

Visualise les transactions comme des flux d'un nœud à l'autre.

```
[Revenus] ──(2500€)──> [Salaire] ──(2500€)──> [Salaire Net]
             ↓
[Dépenses] ──(1800€)──> [Alimentation]
             ↓
          ──(600€)──> [Transport]
```

---

## ⚙️ Personnalisation

### Modifier les couleurs

Dans `d3_tree.js` :
```javascript
const COLORS = {
    revenue: '#00D4AA',
    expense: '#FF6B6B',
    neutral: '#64748b'
};
```

### Ajuster l'espacement des nœuds

```javascript
const treeLayout = d3.tree()
    .nodeSize([50, 200]);  // Vertical, Horizontal spacing
```

### Désactiver drag & drop

```javascript
const ENABLE_DRAG_DROP = false;
```

---

## 🚀 Statut du composant

**État actuel** : Développé mais **pas activement utilisé** dans l'interface principale.

**Raison** : Le Sunburst navigation est préféré pour sa clarté visuelle et son interaction plus intuitive (clic simple vs drag & drop).

**Utilisation potentielle** :
- Page d'administration pour réorganiser les catégories
- Vue alternative de la hiérarchie financière
- Fonctionnalité avancée pour utilisateurs power users

---

## 📚 Ressources D3.js

- **D3 Tree Layout** : https://observablehq.com/@d3/tree
- **D3 Drag & Drop** : https://observablehq.com/@d3/drag-drop
- **D3 Sankey** : https://observablehq.com/@d3/sankey

---

## ✅ Points clés

1. **Composant custom avancé** avec D3.js
2. **Drag & drop** fonctionnel pour réorganisation
3. **Alternative au Sunburst** (moins utilisée actuellement)
4. **Potentiel** pour fonctionnalités futures
5. **Code bien structuré** et réutilisable

---

## 🔮 Améliorations futures possibles

- [ ] Intégrer dans une page "Gestion des catégories"
- [ ] Ajouter animation lors de la réorganisation
- [ ] Mode édition/lecture séparé
- [ ] Undo/Redo pour les modifications
- [ ] Export de la structure en JSON

Composant puissant prêt à être utilisé quand le besoin se présente ! 🎯
