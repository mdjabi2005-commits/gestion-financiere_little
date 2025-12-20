# Transactions View - Refactoring TODO

## État actuel

**Fichier** : `domains/transactions/pages/view.py`
**Taille** : 436 lignes
**Structure** : Relativement bonne (1 fonction principale)

## Imports à migrer

### modules.services → shared/services OU domains/

- [ ] `recurrence_service.py` → Créer `shared/services/recurrence.py`
- [ ] `file_service.py` → Créer `shared/services/files.py`
- [ ] `fractal_service.py` → Créer `shared/services/fractal.py`
- [ ] `csv_export_service.py` → Créer `domains/transactions/export_service.py`

### modules.ui.pages → domains/

- [ ] `transactions_helpers.py` → `domains/transactions/pages/helpers.py`
- [ ] Déjà corrigé : transactions_add → domains/transactions/pages/add

## Refactoring profond (OPTIONNEL - Basse priorité)

La fonction `interface_voir_transactions()` mélange encore :
- Filtrage de données
- Logique d'édition
- Affichage UI

**Idéalement** :
1. Service layer : `transaction_filter_service.py`
2. Service layer : `transaction_edit_service.py`
3. UI layer : Seulement Streamlit

**Complexité** : Élevée (~2h de travail)
**Priorité** : Basse (le code fonctionne bien tel quel)

## Recommandation

**Court terme** : Corriger les imports seulement
**Long terme** : Refactoring profond plus tard

---

**Statut** : Les imports sont la priorité pour la cohérence
