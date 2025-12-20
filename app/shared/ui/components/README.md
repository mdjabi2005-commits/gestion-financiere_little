# 📁 Dossier `/modules/ui/components`

## 🎯 But du dossier

Ce dossier contient les **composants UI réutilisables** - des morceaux d'interface utilisés dans plusieurs pages de l'application. Contrairement aux pages complètes, ces composants sont conçus pour être intégrés dans d'autres interfaces.

---

## 📄 Composants

### 1. `calendar_component.py` - 📅 Calendrier interactif

**Rôle** : Composant personnalisé pour sélectionner des dates et filtrer les transactions par période.

**Fonctionnalités** :
- Calendrier mensuel interactif
- Sélection de date unique OU plage de dates (début → fin)
- Mise en surbrillance des jours avec transactions
- Affichage du solde de la journée au survol
- Reset de la sélection

**Fonction principale** :
```python
def render_calendar(
    df: pd.DataFrame,
    key: str = "calendar",
    enable_range_selection: bool = True
) -> Optional[Tuple[date, date]]:
    """
    Affiche un calendrier interactif.
    
    Args:
        df: DataFrame des transactions à visualiser
        key: Clé unique pour ce calendrier
        enable_range_selection: Si True, permet de sélectionner une plage
        
    Returns:
        Tuple (date_debut, date_fin) si plage sélectionnée, None sinon
    """
```

**Utilisation dans `transactions.py`** :
```python
from modules.ui.components.calendar_component import render_calendar

# Afficher le calendrier
with col_calendar:
    st.subheader("📅 Calendrier")
    
    selected_dates = render_calendar(
        df=df_all_transactions,
        key="cal_transactions",
        enable_range_selection=True
    )
    
    # Filtrer les transactions par la plage sélectionnée
    if selected_dates:
        start_date, end_date = selected_dates
        df_filtered = df[
            (df['date'] >= start_date) &
            (df['date'] <= end_date)
        ]
```

**Comment ça marche** :
1. Génère un calendrier HTML/CSS avec JavaScript
2. Stocke la sélection dans `st.session_state`
3. Retourne les dates sélectionnées
4. Les pages l'utilisent pour filtrer les données

**État du composant** :
```python
# Stocké dans session_state
st.session_state.cal_transactions_selected_date = date(2025, 1, 15)
st.session_state.cal_transactions_date_range = (date(2025, 1, 1), date(2025, 1, 31))
```

**Complexité** : ⭐⭐⭐ Moyenne  
**Lignes** : ~280

---

### 2. `charts.py` - 📊 Graphiques Plotly configurés

**Rôle** : Fonctions helper pour créer rapidement des graphiques Plotly avec le style de l'application.

**Fonctions** :

**`create_bar_chart(x, y_revenue, y_expense, title="")`**  
Crée un graphique en barres Revenus/Dépenses avec solde en ligne.

```python
def create_bar_chart(x, y_revenue, y_expense, title=""):
    """
    Graphique barres groupées + ligne de solde.
    
    Args:
        x: Liste des labels X (ex: mois)
        y_revenue: Valeurs des revenus
        y_expense: Valeurs des dépenses
        title: Titre du graphique
        
    Returns:
        Figure Plotly configurée
    """
    fig = go.Figure()
    
    # Barres vertes (revenus)
    fig.add_trace(go.Bar(
        x=x, y=y_revenue,
        name='Revenus',
        marker_color='#00D4AA'
    ))
    
    # Barres rouges (dépenses)
    fig.add_trace(go.Bar(
        x=x, y=y_expense,
        name='Dépenses',
        marker_color='#FF6B6B'
    ))
    
    # Ligne de solde
    solde = [r - e for r, e in zip(y_revenue, y_expense)]
    fig.add_trace(go.Scatter(
        x=x, y=solde,
        name='Solde',
        mode='lines+markers',
        line=dict(color='#64748b', width=3)
    ))
    
    # Style dark
    fig.update_layout(
        title=title,
        barmode='group',
        plot_bgcolor='#1e293b',
        paper_bgcolor='#1e293b',
        font_color='white'
    )
    
    return fig
```

**Utilisation** :
```python
from modules.ui.components.charts import create_bar_chart

# Données
mois = ['Jan', 'Fév', 'Mar']
revenus = [2500, 2600, 2700]
depenses = [1800, 1900, 2000]

# Créer le graphique
fig = create_bar_chart(
    x=mois,
    y_revenue=revenus,
    y_expense=depenses,
    title="Évolution mensuelle"
)

# Afficher dans Streamlit
st.plotly_chart(fig, use_container_width=True)
```

**`create_pie_chart(labels, values, title="", hole=0.4)`**  
Crée un pie chart (camembert) avec style cohérent.

```python
fig = create_pie_chart(
    labels=['Alimentation', 'Transport', 'Logement'],
    values=[456, 234, 800],
    title="Répartition dépenses",
    hole=0.4  # Donut chart
)
```

**Avantages** :
- Style cohérent dans toute l'app (dark theme)
- Code réutilisable, pas de duplication
- Configuration par défaut optimale
- Facile à modifier le style globalement

**Complexité** : ⭐⭐ Faible  
**Lignes** : ~120

---

## 🔗 Utilisation dans les pages

### home.py
```python
from modules.ui.components.calendar_component import render_calendar
from modules.ui.components.charts import create_bar_chart, create_pie_chart

# Graphique principal
fig_main = create_bar_chart(mois, revenus, depenses, "Évolution financière")
st.plotly_chart(fig_main, use_container_width=True)

# Pie charts
fig_depenses = create_pie_chart(categories, montants, "Dépenses par catégorie")
```

### transactions.py
```python
from modules.ui.components.calendar_component import render_calendar

# Calendrier pour filtrage
selected_dates = render_calendar(df, key="main_calendar")

if selected_dates:
    start, end = selected_dates
    df_filtered = df[(df['date'] >= start) & (df['date'] <= end)]
```

---

## 🎨 Style des composants

Tous les composants suivent la charte graphique de l'app :

**Couleurs** :
```python
COLORS = {
    'revenue': '#00D4AA',      # Vert
    'expense': '#FF6B6B',      # Rouge
    'background': '#1e293b',   # Fond dark
    'text': 'white'            # Texte blanc
}
```

**Thème dark** appliqué par défaut à tous les graphiques Plotly.

---

## 📦 Créer un nouveau composant

**Template** :
```python
# modules/ui/components/mon_composant.py
import streamlit as st

def mon_composant(param1, param2, key="mon_comp"):
    """
    Description du composant.
    
    Args:
        param1: Premier paramètre
        param2: Deuxième paramètre
        key: Clé unique pour le state
        
    Returns:
        Valeur ou None
    """
    # State initialization
    if f'{key}_state' not in st.session_state:
        st.session_state[f'{key}_state'] = None
    
    # Rendu du composant
    with st.container():
        # HTML/CSS/JavaScript si nécessaire
        # Ou widgets Streamlit classiques
        value = st.selectbox("Option", options, key=f"{key}_select")
    
    # Stocker et retourner
    st.session_state[f'{key}_state'] = value
    return value
```

**Utilisation** :
```python
from modules.ui.components.mon_composant import mon_composant

result = mon_composant(param1="val1", param2="val2", key="unique_key")
```

---

## ⚠️ Bonnes pratiques

### 1. Keys uniques
```python
# ✅ BON - Key pour éviter conflits
render_calendar(df, key="cal_home")
render_calendar(df, key="cal_transactions")

# ❌ MAUVAIS - Conflit si utilisé 2x
render_calendar(df)  # key par défaut = "calendar"
render_calendar(df)  # Erreur DuplicateWidgetID!
```

### 2. Session state pour la persistance
```python
# Stocker l'état entre reruns
if 'calendar_selection' not in st.session_state:
    st.session_state.calendar_selection = None
```

### 3. Return None si pas de sélection
```python
# Permet aux pages de gérer facilement
dates = render_calendar(df)

if dates:  # Si une sélection existe
    start, end = dates
    # Filtrer...
else:  # Pas de sélection
    # Afficher toutes les données
```

---

## 🔄 Workflow typique d'un composant

```
1. Initialisation du state
    ↓
2. Rendu HTML/CSS ou widgets Streamlit
    ↓
3. Interaction utilisateur (clic, sélection, etc.)
    ↓
4. Mise à jour du state
    ↓
5. Trigger rerun (si nécessaire)
    ↓
6. Return de la valeur à la page appelante
```

---

## 📊 Composants vs Pages

| Aspect | Composant | Page |
|--------|-----------|------|
| **Portée** | Petit morceau d'UI | Interface complète |
| **Réutilisable** | Oui (plusieurs pages) | Non (unique) |
| **Navigation** | Non | Oui (menu latéral) |
| **Exemple** | Calendrier, graphique | Dashboard, Transactions |
| **Fichier** | `components/*.py` | `pages/*.py` |

---

## 🚀 Évolution future

**Composants à créer** :
- [ ] Sélecteur de catégories hiérarchique
- [ ] Graphique d'évolution temporelle configurable
- [ ] Carte de transaction (card UI)
- [ ] Filtre multi-critères avancé
- [ ] Composant d'upload de fichier stylisé

---

## 📚 Résumé

Ce dossier contient les **briques réutilisables** de l'interface :
- **Calendrier** pour sélection de dates
- **Charts** pour graphiques cohérents

Simple mais essentiel pour éviter la duplication de code et garantir un style uniforme ! 🎨
