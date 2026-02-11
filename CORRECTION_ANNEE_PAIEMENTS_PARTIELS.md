# CORRECTION - Prise en compte de l'année sélectionnée dans les paiements partiels

## Date: 11 février 2026

## Problème identifié
Lors de l'ajout d'un paiement partiel, le système ignorait l'année sélectionnée par l'utilisateur dans le formulaire et utilisait **TOUJOURS l'année courante (2026)**. Cela causait des erreurs de détection d'avance incorrectes.

### Symptômes
- L'utilisateur sélectionne "novembre 2025" mais le système interprète "novembre 2026"
- Message d'erreur : "AVANCE DÉTECTÉE : Vous tentez de payer pour novembre 2026..."
- Le système pense que l'utilisateur paie pour le futur alors qu'il veut payer pour le passé

## Solution appliquée

### Fichiers modifiés

#### 1. `paiements/views.py` (fonction `ajouter_paiement_partiel` - ligne ~176)
**Avant :**
```python
mois_paye_nom = request.POST.get('mois_paye', '')
if mois_paye_nom:
    import re
    if not re.search(r'\d{4}', mois_paye_nom):
        annee_actuelle = datetime.now().year
        mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"  # ❌ Force toujours 2026
```

**Après :**
```python
mois_paye_nom = request.POST.get('mois_paye', '')
annee_selectionnee = request.POST.get('annee_paiement', '')  # ✅ Récupère l'année

if mois_paye_nom:
    import re
    if not re.search(r'\d{4}', mois_paye_nom):
        if annee_selectionnee:  # ✅ Priorité à l'année sélectionnée
            mois_paye_nom = f"{mois_paye_nom} {annee_selectionnee}"
        else:  # Fallback si aucune année
            annee_actuelle = datetime.now().year
            mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
```

#### 2. `paiements/views.py` (fonction `ajouter_paiement` - ligne ~1159)
Même correction appliquée pour les paiements standards (avance, caution, etc.)

#### 3. `temp_views.py`
Fichier temporaire synchronisé avec les mêmes corrections

### Logique de la correction

1. **Récupération de l'année** : Le formulaire envoie deux champs :
   - `mois_paye` : le nom du mois (ex: "novembre")
   - `annee_paiement` : l'année sélectionnée (ex: "2025")

2. **Priorité** :
   - Si `annee_paiement` est fourni → utiliser cette année ✅
   - Sinon → utiliser l'année courante (fallback)

3. **Format final** : "novembre 2025" (année explicite)

4. **Validation** : La fonction `ServicePaiementPartiel.valider_mois_a_regler()` extrait correctement l'année du string "novembre 2025"

## Tests effectués

Créé `test_correction_annee.py` qui vérifie :
- ✅ "novembre" seul → 2026-11-01 (année courante)
- ✅ "novembre 2025" → 2025-11-01 (année respectée)
- ✅ Simulation views.py avec année sélectionnée → correct

## Impact

### Avant la correction
- ❌ Impossible de créer des paiements partiels pour les mois passés (2025)
- ❌ Fausses alertes d'avance détectées
- ❌ Confusion pour les utilisateurs

### Après la correction
- ✅ L'année sélectionnée dans le formulaire est respectée
- ✅ Les paiements partiels pour 2025 fonctionnent correctement
- ✅ La validation des avances est correcte

## Déploiement en production

1. **Tester en local** : ✅ Tests réussis
2. **Commit des changements** :
   ```bash
   git add paiements/views.py temp_views.py
   git commit -m "fix: Respect de l'année sélectionnée dans les paiements partiels"
   git push origin migration-postgresql-propre
   ```
3. **Déployer sur Render** : Push automatique déclenchera le déploiement

## Notes importantes

- Le formulaire `PaiementForm` dans `forms.py` gère déjà correctement la combinaison mois + année dans sa méthode `clean()`
- Cette correction s'applique AVANT l'appel à `is_valid()`, donc elle affecte la validation côté serveur
- Le champ `annee_paiement` existe déjà dans le formulaire (ligne 33 de `forms.py`)

## Fichiers concernés
- ✅ `paiements/views.py` (2 endroits corrigés)
- ✅ `temp_views.py` (2 endroits corrigés)
- ℹ️ `paiements/services_paiement_partiel.py` (fonctionne correctement une fois l'année ajoutée)
- ℹ️ `paiements/forms.py` (gère déjà correctement la combinaison)
