# 🔍 Guide Debug OCR - SIMPLIFIÉ

**Ce guide explique comment déboguer l'OCR quand ça ne marche pas.**

---

## 🎯 Qu'est-ce que l'OCR ?

**OCR = Optical Character Recognition = Scanner un ticket**

**3 étapes** :
1. 📸 Scanner image → Texte (Tesseract)
2. 🔍 Extraire montant/date du texte (Parser)
3. ✅ Vérifier si c'est bon (Validation)

---

## 🚨 Problèmes courants & Solutions

### Problème 1 : "Montant non détecté"

**Symptôme** : Le scan trouve 0.00€ ou montant faux

**Debug** :
```python
# 1. Vérifier le texte OCR brut
from modules.ocr.scanner import full_ocr
text = full_ocr("ticket.jpg")
print(text)  # Le texte est-il lisible ?
```

**Causes possibles** :
- Image floue → Rescanner en meilleure qualité
- Patterns manquants → Ajouter pattern dans `config/ocr_patterns.yml`
- Format inconnu → Voir logs pour nouveaux patterns

**Solution rapide** :
1. Ouvrir `config/ocr_patterns.yml`
2. Ajouter pattern trouvé dans ticket :
   ```yaml
   amount_patterns:
     - pattern: "VOTRE_PATTERN"
       priority: 10
       enabled: true
   ```

---

### Problème 2 : "Logs ne s'affichent pas"

**Debug** :
```python
# Activer logs détaillés
import logging
logging.basicConfig(level=logging.DEBUG)

from modules.ocr.parser_refactored import parse_ticket_metadata_v2
result = parse_ticket_metadata_v2(text)
# Vous verrez :
# 🔍 METHOD A: Looking for TOTAL patterns...
# ✅ Found 25.50€
# etc.
```

---

### Problème 3 : "Ticket va dans problématiques"

**Pourquoi ?**
- Méthode de détection = "D-FALLBACK" (peu fiable)
- Montant = 0.00€

**Solution** :
1. Ouvrir page "Tour de Contrôle OCR"
2. Onglet "Tickets Problématiques"
3. Voir quel pattern manque
4. L'ajouter dans YAML

---

## 📂 Fichiers Importants

### Pour VOUS (debug) :

**`config/ocr_patterns.yml`** - Ajouter patterns ici
```yaml
amount_patterns:
  - pattern: "TOTAL TTC"  # ← Facile à modifier !
```

**`modules/ocr/parser_refactored.py`** - Parser avec logs
- Logs détaillés à chaque étape
- Facile de voir où ça bloque

### Pour le système (auto) :

**`modules/ocr/scanner.py`** - Tesseract OCR
**`modules/ocr/pattern_manager.py`** - Charge patterns YAML
**`modules/ocr/logging.py`** - Enregistre stats
**`modules/ocr/diagnostics.py`** - Analyse perf

---

## 🛠️ Workflow de Debug

### Étape 1 : Reproduire le problème
```python
from modules.ocr.scanner import full_ocr
from modules.ocr.parser_refactored import parse_ticket_metadata_v2

# Scanner
text = full_ocr("ticket_problematique.jpg")

# Parser avec logs
import logging
logging.basicConfig(level=logging.INFO)
result = parse_ticket_metadata_v2(text)

print(f"Montant trouvé : {result['montant']}€")
print(f"Méthode : {result['methode_detection']}")
print(f"Fiable ? {result['fiable']}")
```

### Étape 2 : Analyser les logs
- `🔍 METHOD A` = Patterns TOTAL/MONTANT
- `🔍 METHOD B` = CB/CARTE
- `🔍 METHOD C` = HT+TVA
- `⚠️  METHOD D` = FALLBACK (mauvais!)

### Étape 3 : Corriger
- Si `METHOD D` utilisé → Ajouter pattern dans YAML
- Si `No amounts found` → Vérifier qualité image

---

## 📊 Activer Logs Complets

**Dans votre code** :
```python
import logging

# Config logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s'
)

# Maintenant tous les logs s'affichent !
```

**Fichiers de logs** (automatiques) :
- `~/analyse/ocr_logs/scan_history.jsonl` - Historique
- `~/analyse/ocr_logs/performance_stats.json` - Stats

---

## 🎯 Commandes Rapides

```python
# Test rapide OCR
from modules.ocr.scanner import full_ocr
text = full_ocr("ticket.jpg")
print(text)

# Parser avec debug
import logging
logging.basicConfig(level=logging.INFO)

from modules.ocr.parser_refactored import parse_ticket_metadata_v2
result = parse_ticket_metadata_v2(text)

# Ajouter pattern
from modules.ocr.pattern_manager import get_pattern_manager
pm = get_pattern_manager()
pm.add_amount_pattern("NOUVEAU PATTERN", "Description", priority=10)
```

---

## ✅ Checklist Debug

- [ ] Image nette et lisible ?
- [ ] Texte OCR contient le montant ?
- [ ] Pattern existe dans `ocr_patterns.yml` ?
- [ ] Logs activés (`logging.basicConfig(level=logging.DEBUG)`) ?
- [ ] Méthode = A/B/C (pas D-FALLBACK) ?

---

**Besoin d'aide ?** Ouvrir "Tour de Contrôle OCR" dans l'app !
