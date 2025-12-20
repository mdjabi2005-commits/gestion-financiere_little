# OCR Patterns - Documentation

**Dernière mise à jour** : 19 décembre 2024

Ce document explique comment fonctionnent les patterns OCR et comment en ajouter de nouveaux.

---

## 📋 Patterns Actuels

Les patterns sont définis dans `config/ocr_patterns.yml` et regroupés par type :

### Amount Patterns (Montants)

Patterns pour détecter le montant total :

| Pattern | Exemple Match | Raison |
|---------|--------------|--------|
| `MONTANT\s*(R[EÉ][EÉ][LI]\|REEL\| KEEL)` | "MONTANT REEL: 15.50" | Variantes OCR de "RÉEL" |
| `TOTAL\s*T[IT]C\s*[=:]?` | "TOTAL TTC = 25.80" | Total TTC avec variantes |
| `MONT\s*ANT\s*:` | "MONT ANT : 12.50" | OCR split "MONTANT" |
| `TOTAL\s*:` | "TOTAL: 45.00" | Pattern simple TOTAL |

### Payment Patterns (Paiement)

Patterns pour détecter méthodes de paiement :

| Pattern | Exemple Match |
|---------|--------------|
| `CB` | "CB: 15.50€" |
| `CARTE` | "CARTE BANCAIRE 25.80" |
| `PAIEMENT` | "PAIEMENT: 12.50" |
| `PATEMENT` | "PATEMENT 10.00" (variante OCR) |

---

## 🎯 Comment Ajouter un Pattern

### Méthode 1 : Manuel (YAML)

1. **Ouvrir** `config/ocr_patterns.yml`

2. **Ajouter** sous `amount_patterns` :
```yaml
amount_patterns:
  - pattern: "NOUVEAU\\s*PATTERN"
    # Ajouter commentaire expliquant
```

3. **Tester** avec un ticket réel

4. **Documenter** dans ce fichier

### Méthode 2 : Apprentissage Automatique 🆕

Le système peut apprendre automatiquement depuis les corrections :

1. **Utilisateur corrige** un montant dans l'interface
2. **Système analyse** le texte OCR
3. **Suggère pattern** basé sur contexte
4. **Utilisateur valide** → Pattern ajouté automatiquement

**Fichier des patterns appris** : `config/ocr_patterns_learned.yml`

---

## 🧪 Méthodes de Détection

L'OCR utilise 4 méthodes parallèles :

### Méthode A : Pattern Matching
- Cherche mots-clés (`TOTAL`, `MONTANT`, etc.)
- Extrait nombre après mot-clé
- **Fiabilité** : ⭐⭐⭐⭐⭐ (si pattern match)

### Méthode B : Payment Detection
- Cherche méthodes paiement (`CB`, `CARTE`)
- Somme tous montants trouvés
- **Fiabilité** : ⭐⭐⭐⭐

### Méthode C : Largest Number
- Trouve le plus grand nombre
- **Fiabilité** : ⭐⭐⭐

### Méthode D : Fallback (désactivée)
- Dernière solution de repli
- **Fiabilité** : ⭐

### Cross-Validation

Quand **2+ méthodes trouvent le même montant** → ✅ **Fiable**

---

## 📝 Guidelines Patterns

### ✅ Bons Patterns

```yaml
# Flexible avec espaces
- pattern: "TOTAL\\s*TTC"

# Variantes OCR communes
- pattern: "MONT(ANT|\\s*ANT)"

# Séparateurs optionnels
- pattern: "MONTANT\\s*[=:]?"
```

### ❌ Patterns à Éviter

```yaml
# Trop strict
- pattern: "TOTAL:" # Manque si "TOTAL :" (espace)

# Pas de variantes OCR
- pattern: "MONTANT RÉEL" # Manque "KEEL", "REEL"

# Trop générique
- pattern: "\\d+\\.\\d+" # Matcherait n'importe quel nombre
```

---

## 🔍 Troubleshooting

### Pattern ne match pas

1. **Vérifier texte OCR brut** dans interface
2. **Chercher variantes** (espaces, typos OCR)
3. **Tester pattern** avec regex tester
4. **Ajouter variantes** au pattern

### Pattern match trop de choses

1. **Rendre plus spécifique** (contexte avant/après)
2. **Limiter portée** du pattern
3. **Tester sur plusieurs tickets**

### Apprentissage ne suggère rien

1. **Vérifier montant dans OCR text**
2. **Analyser contexte** (lignes autour)
3. **Ajouter manuellement** si nécessaire

---

## 📊 Exemples Réels

### Ticket Carrefour
```
OCR Text:
TOTAL TTC
EUR 25.80
```

**Pattern** : `TOTAL\s*TTC`  
**Méthode** : A  
**Résultat** : 25.80€ ✅

### Ticket Uber
```
OCR Text:
MONTANT REEL
15.50 EUR
```

**Pattern** : `MONTANT\s*R[EÉ][EÉ][LI]`  
**Méthode** : A  
**Résultat** : 15.50€ ✅

### Ticket Restaurant
```
OCR Text:
CB: 45.00€
TOTAL: 45.00
```

**Patterns** : A (`TOTAL`) + B (`CB`)  
**Cross-validation** : ✅ Fiable  
**Résultat** : 45.00€ ✅

---

## 🚀 Évolution Future

### Patterns Communautaires (Phase 3)
- Export/import patterns entre utilisateurs
- Repository GitHub des patterns
- Patterns validés par communauté

### ML-Based Patterns (Phase 4)
- Machine learning pour générer patterns
- Détection automatique de nouveaux formats
- Amélioration continue

---

**Besoin d'aide ?** Voir `domains/ocr/README.md` pour plus de détails sur le pipeline OCR complet.
