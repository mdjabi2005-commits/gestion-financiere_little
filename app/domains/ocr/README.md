# Module OCR - Guide Complet

**Dernière mise à jour** : 17 décembre 2024

---

## 🎯 Vue d'Ensemble

Le module OCR (Optical Character Recognition) extrait automatiquement les données des tickets et documents scannés. Il transforme une image en transaction structurée via un pipeline en 4 étapes.

---

## 📊 Pipeline OCR Complet

```
┌──────────────┐
│ Image Ticket │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────┐
│ ÉTAPE 1: Extraction Texte       │
│ scanner.py → full_ocr()          │
│ • Prétraitement image            │
│ • Tesseract OCR (fra+eng)        │
│ • Texte brut                     │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ ÉTAPE 2: Normalisation           │
│ parsers.py → _normalize_ocr_text│
│ • Split en lignes                │
│ • Strip espaces                  │
│ ⚠️ PAS de O→0 (casse MONTANT!)   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ ÉTAPE 3: Détection Montants      │
│ 4 Méthodes Parallèles :          │
│                                  │
│ A) Pattern Matching              │
│    • Patterns YML                │
│    • "MONTANT", "TOTAL", etc.    │
│                                  │
│ B) Détection Paiement            │
│    • "CB", "CARTE", etc.         │
│    • Somme montants              │
│                                  │
│ C) Calcul HT+TVA                 │
│    • Pour factures pro           │
│                                  │
│ D) Fallback (DÉSACTIVÉ)          │
│    • Plus utilisé                │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ ÉTAPE 4: Cross-Validation        │
│ • Vote majoritaire               │
│ • Fréquence montants             │
│ • Montant final                  │
└──────┬──────────────────────────┘
       │
       ▼
┌──────────────┐
│ Montant: 4.32€│
│ Date: 2025-12-06│
│ Fiable: ✅    │
└───────────────┘
```

---

## 📄 Fichiers du Module

### 1. `scanner.py` - Extraction Texte

**Responsabilité** : Convertir image → texte brut

**Fonction principale** :
```python
def full_ocr(image_path: str, show_ticket: bool = False) -> str:
    """
    Extrait texte d'une image avec Tesseract OCR.
    
    Process:
    1. Lecture robuste image (gère accents chemins)
    2. Prétraitement (gris, blur, threshold)
    3. OCR multi-langue (fra+eng)
    4. Retourne texte nettoyé
    """
```

**Prétraitement appliqué** :
```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)      # Niveaux de gris
gray = cv2.GaussianBlur(gray, (3, 3), 0)            # Flou (réduit bruit)
_, thresh = cv2.threshold(gray, 0, 255,             # Binarisation Otsu
                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)
```

**Pourquoi fra+eng ?** Tickets mélangent français et anglais.

---

### 2. `parsers.py` - Détection Intelligente

**Responsabilité** : Texte → Données structurées

#### Fonction Principale

```python
def parse_ticket_metadata_v2(ocr_text: str) -> dict:
    """
    Parse texte OCR et extrait montant + date.
    
    Returns:
    {
        'montant': 4.32,
        'date': '2025-12-06',
        'methode_detection': 'A-PATTERNS',
        'fiable': True
    }
    """
```

#### Méthodes de Détection

**🔵 Méthode A : Pattern Matching**

```python
def _detect_amount_method_a(lines: List[str]) -> Tuple[List[float], List[str]]:
    """
    Cherche patterns configurés dans ocr_patterns.yml
    
    Patterns (exemples):
    - MONTANT\s*(REEL|KEEL)    # Tickets essence
    - TOTAL\s*\d+\s*ARTICL     # Leclerc
    - MONTANT\s*:              # Tickets CB
    
    IMPORTANT: Case-insensitive, cherche sur ligne suivante
    """
```

**Comment ça marche** :
1. Charge patterns depuis `config/ocr_patterns.yml`
2. Pour chaque pattern, appelle `get_montant_from_line()`
3. Si pattern trouvé, extrait montant de cette ligne OU ligne suivante
4. Retourne tous les montants trouvés

**🟢 Méthode B : Paiement**

```python
def _detect_amount_method_b(lines: List[str]) -> float:
    """
    Cherche lignes avec CB, CARTE, BANCAIRE, etc.
    Somme tous les montants de ces lignes.
    
    Patterns: CB, CARTE, ESPECES, DEBIT, CREDIT, etc.
    """
```

**🟠 Méthode C : HT+TVA**

```python
def _detect_amount_method_c(lines: List[str]) -> float:
    """
    Pour factures professionnelles.
    Cherche lignes HT et TVA, retourne somme.
    """
```

**⚫ Méthode D : Fallback (DÉSACTIVÉ)**

```python
def _detect_amount_method_d(ocr_text: str) -> float:
    """
    DÉSACTIVÉ depuis 17/12/2024.
    Forçait l'amélioration des vraies méthodes.
    """
    return 0.0
```

#### Cross-Validation

```python
def _cross_validate_amounts(...) -> Tuple[float, str]:
    """
    Vote majoritaire entre méthodes.
    
    Example:
    - Méthode A trouve: [4.32, 4.32]
    - Méthode B trouve: 4.32
    - Méthode C trouve: 0.0
    
    Fréquence: {4.32: 3 votes}
    → Résultat: 4.32€ avec confiance 3/3
    """
```

---

### 3. `pattern_manager.py` - Gestion Patterns

**Responsabilité** : Charger et gérer patterns depuis YML

**Fonctions clés** :
```python
def get_pattern_manager() -> PatternManager:
    """Singleton, charge patterns depuis config/ocr_patterns.yml"""

manager = get_pattern_manager()
patterns = manager.get_amount_patterns()  # Liste patterns montants
payments = manager.get_payment_patterns() # Liste patterns paiement
```

**Path absolu** : Depuis 17/12/2024, utilise path absolu pour fonctionner depuis n'importe quel répertoire.

---

### 4. `parsers_OLD_BACKUP.py` - Fonctions Utilitaires

**Fonction importante** :
```python
def get_montant_from_line(pattern, lines, allow_next_line=True):
    """
    Cherche pattern dans lignes, extrait montant.
    
    Features:
    - Case-insensitive
    - Cherche sur ligne + ligne suivante
    - Corrige erreurs OCR contextuelles
    - Retourne max si plusieurs montants
    """
```

**Utilisé par** : Méthode A de `parsers.py`

---

## ⚙️ Configuration

###`config/ocr_patterns.yml`

**Structure** :
```yaml
amount_patterns:
  - pattern: "MONTANT\\s*(REEL|KEEL)"
    priority: 1
    enabled: true
    description: "Tickets essence CB"

payment_patterns:
  - "CB"
  - "CARTE"
  - "PATEMENT"  # Variante OCR
```

**Patterns Actuels** (17/12/2024) :
- ✅ MONTANT (avec variantes KEEL, MONT ANT)
- ✅ TOTAL (avec TTC, TIC, articles)
- ✅ Paiements (CB, CARTE, PATEMENT, DEBIT, CREDIT)

---

## 🚨 Règles CRITIQUES

### ❌ NE JAMAIS Normaliser O→0 Globalement

**INTERDIT** :
```python
text.replace("O", "0")  # Détruit MONTANT, TOTAL
```

**Conséquence** :
```
MONTANT → M0NTANT  ❌ Pattern ne matche plus
TOTAL   → T0TAL    ❌ Pattern ne matche plus
```

**Impact historique** : A causé 0% de réussite méthode A avant fix.

### ✅ Patterns Doivent Venir de Tickets Réels

**Process** :
1. Collecter tickets réels
2. Auditer (valeurs attendues)
3. Analyser texte OCR BRUT
4. Extraire patterns présents
5. Ajouter dans YML

**Ne PAS** inventer patterns théoriques.

### ⚠️ Case-Insensitive Obligatoire

Tous les patterns doivent être insensibles à la casse :
```python
re.search(pattern, line, re.IGNORECASE)
```

---

## 🔧 Comment Améliorer

### Ajouter Nouveau Pattern

1. **Identifier besoin** (ticket non détecté)
2. **Extraire pattern réel** du texte OCR
3. **Ajouter à YML** :
```yaml
amount_patterns:
  - pattern: "MON_PATTERN\\s*:"
    priority: 10
    enabled: true
    description: "Description"
```
4. **Tester** sur tickets réels

### Débugger Pattern qui Ne Fonctionne Pas

**Script debug** :
```python
from domains.ocr.parsers_OLD_BACKUP import get_montant_from_line

lines = ["MONTANT REEL", "57.98 EUR"]
pattern = "MONTANT.*REEL"

montant, matched = get_montant_from_line(pattern, lines)
print(f"Trouvé: {montant}€, Match: {matched}")
```

**Checklist** :
- [ ] Pattern est-il case-insensitive ?
- [ ] Texte OCR contient-il vraiment ce pattern ?
- [ ] Normalisation ne casse-t-elle pas le pattern ?

---

## 📊 Performances

**Taux de réussite** (17/12/2024) : **100%** (11/11 tickets)

**Méthodes utilisées** :
- Méthode A seule : 64%
- Méthode A+B : 27%
- Méthode A+C : 9%

**Fallback utilisé** : 0%

---

## 🔗 Références

- [ocr-rules.md](../../bibliotheque/modules/ocr-rules.md) - Règles strictes
- [Walkthrough 17/12/2024](../../bibliotheque/ajouts/04_amelioration_ocr.md) - Session amélioration
- [config/ocr_patterns.yml](../../v4/config/ocr_patterns.yml) - Patterns actuels
