# MISE À JOUR DES RÉCAPITULATIFS MENSUELS - Intégration Charges Bailleur

## 🎯 Objectif

Recalculer tous les récapitulatifs mensuels déjà générés (en local et en production) pour prendre en compte les charges bailleur s'il y en a.

## 📋 Commande de Gestion Django

Une commande Django a été créée : `recalculer_recaps_avec_charges.py`

### Localisation
```
paiements/management/commands/recalculer_recaps_avec_charges.py
```

### Fonctionnalités

✅ Recalcule tous les récapitulatifs mensuels  
✅ Intègre automatiquement les charges bailleur  
✅ Recalcule commission et montant à payer  
✅ Mode test (dry-run) pour vérifier avant d'appliquer  
✅ Filtrage par année et/ou mois  
✅ Statistiques détaillées  
✅ Logs complets  

## 🚀 Utilisation

### En Local (Développement)

#### 1. Mode TEST (recommandé pour commencer)
```bash
# Voir ce qui sera modifié sans rien sauvegarder
python manage.py recalculer_recaps_avec_charges --dry-run
```

#### 2. Application réelle
```bash
# Appliquer les modifications
python manage.py recalculer_recaps_avec_charges
```

#### 3. Filtrage par année
```bash
# Ne recalculer que 2025
python manage.py recalculer_recaps_avec_charges --annee 2025
```

#### 4. Filtrage par mois
```bash
# Ne recalculer que janvier (mois 1)
python manage.py recalculer_recaps_avec_charges --mois 1
```

#### 5. Forcer la mise à jour
```bash
# Même si déjà à jour
python manage.py recalculer_recaps_avec_charges --force
```

#### 6. Combinaisons
```bash
# Test pour janvier 2025 uniquement
python manage.py recalculer_recaps_avec_charges --dry-run --annee 2025 --mois 1

# Appliquer pour toute l'année 2024
python manage.py recalculer_recaps_avec_charges --annee 2024
```

### En Production (Render)

#### Méthode 1 : Via le Shell Render

1. Accéder au dashboard Render
2. Cliquer sur votre service "appli-kbis-3"
3. Aller dans l'onglet "Shell"
4. Exécuter :

```bash
# Mode test d'abord
python manage.py recalculer_recaps_avec_charges --dry-run

# Si OK, appliquer
python manage.py recalculer_recaps_avec_charges
```

#### Méthode 2 : Via Render CLI (si installé)

```bash
# Se connecter
render login

# Exécuter la commande
render shell --service appli-kbis-3 -- python manage.py recalculer_recaps_avec_charges
```

#### Méthode 3 : Créer un Job One-Off

Dans le fichier `render.yaml`, vous pouvez ajouter :

```yaml
jobs:
  - type: cron
    name: recalculer-recaps
    env: python
    schedule: "0 0 * * *"  # Tous les jours à minuit (optionnel)
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python manage.py recalculer_recaps_avec_charges"
```

## 📊 Exemple de Sortie

```
================================================================================
RECALCUL DES RÉCAPITULATIFS MENSUELS AVEC CHARGES BAILLEUR
================================================================================

📊 3 récapitulatif(s) trouvé(s)

────────────────────────────────────────────────────────────────────────────────
[1/3] Récapitulatif #45 - DUPONT Jean - janvier 2025
────────────────────────────────────────────────────────────────────────────────

📋 État actuel :
   Loyers bruts : 300,000 F CFA
   Charges bailleur (BDD) : 0 F CFA
   Charges bailleur (calculées) : 25,000 F CFA
   Nombre de charges trouvées : 2

🔄 Nouveau calcul :
   Loyers bruts : 300,000 F CFA
   - Charges bailleur : 25,000 F CFA
   = Montant net : 275,000 F CFA
   - Commission (10%) : 27,500 F CFA
   = À payer au bailleur : 247,500 F CFA

📊 Différences :
   Charges bailleur : +25,000 F CFA
   Net à payer : -25,000 F CFA
   Commission : -2,500 F CFA
   Montant réellement payé : -27,500 F CFA

   ✅ Récapitulatif mis à jour avec succès !

────────────────────────────────────────────────────────────────────────────────
[2/3] Récapitulatif #46 - MARTIN Marie - janvier 2025
────────────────────────────────────────────────────────────────────────────────

📋 État actuel :
   Loyers bruts : 150,000 F CFA
   Charges bailleur (BDD) : 0 F CFA
   Charges bailleur (calculées) : 0 F CFA
   Nombre de charges trouvées : 0

   ✅ Déjà à jour (charges = 0 F)

================================================================================
RÉSUMÉ DU TRAITEMENT
================================================================================

📊 Total récapitulatifs traités : 3
   • Avec charges bailleur : 1
   • Sans charges bailleur : 1
   • Déjà à jour : 1
   • Mis à jour : 1

💰 Montant total des charges bailleur intégrées : 25,000 F CFA

================================================================================

✅ Traitement terminé avec succès !
```

## 🔍 Processus de Recalcul

Pour chaque récapitulatif :

```python
1. Récupérer les charges bailleur du mois
   - Statut = 'valide'
   - Même mois/année que le récap
   - Non encore utilisées dans un retrait

2. Calculer le total des charges
   total_charges = Σ(montant_restant ou montant)

3. Recalculer le montant net
   net = loyers_bruts - charges_bailleur

4. Recalculer la commission (10%)
   commission = net × 0.10

5. Recalculer le montant à payer
   montant_paye = net - commission

6. Sauvegarder les nouveaux montants
   - total_charges_bailleur
   - total_net_a_payer
   - commission_agence
   - montant_reellement_paye
```

## ⚠️ Précautions

### Avant d'Exécuter

1. **Faire une sauvegarde de la base de données**
   ```bash
   # En local (SQLite)
   cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d)
   
   # En production (PostgreSQL via Render)
   # Render fait des sauvegardes automatiques
   ```

2. **Toujours tester en mode dry-run d'abord**
   ```bash
   python manage.py recalculer_recaps_avec_charges --dry-run
   ```

3. **Vérifier qu'il n'y a pas de processus en cours**
   - Pas de génération de récaps en cours
   - Pas de paiements en cours de traitement

### Recommandations

✅ **Exécuter en dehors des heures de pointe**  
✅ **Commencer par un test sur un mois spécifique**  
✅ **Vérifier les logs après exécution**  
✅ **Comparer quelques récaps manuellement**  

## 📝 Vérification Post-Exécution

### 1. Vérification Visuelle

Accédez à un récapitulatif dans l'interface et vérifiez :
- Le champ "Charges bailleur" n'est plus à 0
- Le montant net a diminué (si charges présentes)
- La commission a été recalculée
- Le montant à payer est correct

### 2. Requête SQL de Contrôle

```sql
-- Récaps avec charges bailleur intégrées
SELECT 
    r.id,
    r.mois_recap,
    b.nom as bailleur,
    r.total_loyers_bruts,
    r.total_charges_bailleur,
    r.total_net_a_payer,
    r.commission_agence,
    r.montant_reellement_paye,
    COUNT(cb.id) as nb_charges
FROM paiements_recapmensuel r
JOIN proprietes_bailleur b ON b.id = r.bailleur_id
LEFT JOIN proprietes_chargebailleur cb ON (
    cb.bailleur_id = r.bailleur_id
    AND EXTRACT(YEAR FROM cb.date_charge) = EXTRACT(YEAR FROM r.mois_recap)
    AND EXTRACT(MONTH FROM cb.date_charge) = EXTRACT(MONTH FROM r.mois_recap)
    AND cb.statut = 'valide'
)
WHERE r.is_deleted = FALSE
GROUP BY r.id, b.nom
ORDER BY r.mois_recap DESC
LIMIT 10;
```

### 3. Vérification Mathématique

```python
# Pour chaque récap vérifié :
net_calculé = loyers_bruts - charges_bailleur
commission_calculée = net_calculé * 0.10
montant_payé_calculé = net_calculé - commission_calculée

# Vérifier que :
assert net_calculé == total_net_a_payer
assert commission_calculée == commission_agence
assert montant_payé_calculé == montant_reellement_paye
```

## 🔄 Fréquence d'Exécution

### Utilisation Initiale
- **Une seule fois** après le déploiement de la correction
- Pour mettre à jour les récaps existants

### Utilisation Future
- **Pas nécessaire** : Les nouveaux récaps calculent automatiquement les charges
- **Seulement si** : Des charges ont été ajoutées rétroactivement

## 📞 En Cas de Problème

### Erreur : "no such table"
```bash
# Exécuter les migrations
python manage.py migrate
```

### Erreur : Permission denied
```bash
# Vérifier les permissions utilisateur
# En production, contacter le support Render
```

### Charges non trouvées
- Vérifier que les charges existent dans la table `ChargesBailleur`
- Vérifier que le statut = 'valide'
- Vérifier les dates (mois/année)

### Différences incorrectes
- Vérifier que `calculer_totaux_bailleur()` a bien été appelé
- Vérifier les formules de calcul
- Comparer avec un calcul manuel

## 📚 Documentation Associée

- `CORRECTION_CHARGES_BAILLEUR_RECAP.md` - Explication de la correction
- `paiements/models.py` - Méthode `calculer_totaux_bailleur()`
- `paiements/services_charges_bailleur.py` - Service d'intégration

---

**Date de création :** 20 janvier 2026  
**Auteur :** Système de gestion KBIS  
**Statut :** ✅ Prêt à l'exécution
