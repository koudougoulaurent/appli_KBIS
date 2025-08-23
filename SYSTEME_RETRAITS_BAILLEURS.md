# Système de Retraits aux Bailleurs - Rentila

## Vue d'ensemble

Le système de retraits aux bailleurs permet de gérer les versements effectués par l'agence immobilière aux propriétaires des biens loués. Il se distingue clairement du système de paiements qui gère les loyers payés par les locataires.

## Distinction claire

### Paiements (Loyers)
- **Qui paie** : Les locataires
- **Qui reçoit** : L'agence immobilière
- **Objectif** : Perception des loyers et charges
- **Fréquence** : Selon les contrats de location

### Retraits (Versements aux bailleurs)
- **Qui paie** : L'agence immobilière
- **Qui reçoit** : Les bailleurs/propriétaires
- **Objectif** : Versement des loyers perçus (moins les charges déductibles)
- **Fréquence** : Généralement mensuelle

## Modèles de données

### 1. RetraitBailleur
Modèle principal pour gérer les retraits aux bailleurs.

**Champs principaux :**
- `bailleur` : Référence au bailleur
- `mois_retrait` : Mois concerné par le retrait
- `montant_loyers_bruts` : Total des loyers perçus
- `montant_charges_deductibles` : Charges à déduire
- `montant_net_a_payer` : Montant final à verser
- `type_retrait` : Mensuel, trimestriel, semestriel, annuel
- `mode_retrait` : Virement, chèque, espèces, mobile money
- `statut` : En attente, validé, payé, annulé

**Relations :**
- `paiements_concernes` : Paiements inclus dans ce retrait
- `charges_deductibles` : Charges déduites (via RetraitChargeDeductible)

### 2. RetraitChargeDeductible
Modèle de liaison entre retraits et charges déductibles.

**Champs :**
- `retrait_bailleur` : Référence au retrait
- `charge_deductible` : Référence à la charge
- `date_ajout` : Date d'ajout de la charge au retrait

### 3. RecuRetrait
Modèle pour gérer les reçus/quittances de retrait.

**Champs :**
- `numero_recu` : Numéro unique du reçu
- `retrait_bailleur` : Référence au retrait
- `date_emission` : Date d'émission
- `imprime` : Statut d'impression
- `format_impression` : Format du reçu

## Fonctionnalités principales

### 1. Création manuelle de retraits
- Sélection du bailleur
- Définition du mois de retrait
- Saisie des montants
- Génération automatique du reçu

### 2. Création automatique de retraits
- Génération en masse pour tous les bailleurs
- Calcul automatique des montants
- Prise en compte des charges déductibles
- Options de configuration avancées

### 3. Gestion du cycle de vie
- **Création** : Retrait en attente
- **Validation** : Retrait validé par un responsable
- **Paiement** : Retrait marqué comme payé
- **Annulation** : Retrait annulé si nécessaire

### 4. Génération de reçus
- Format paysage pour impression
- Informations détaillées du retrait
- Calculs automatiques des montants
- Historique des actions

## Calculs automatiques

### Montant des loyers bruts
```
Loyers bruts = Σ(Paiements validés du mois pour les propriétés du bailleur)
```

### Montant des charges déductibles
```
Charges déductibles = Σ(Charges validées du mois pour les propriétés du bailleur)
```

### Montant net à payer
```
Net à payer = Loyers bruts - Charges déductibles
```

## Workflow typique

### 1. Fin de mois
- Récupération de tous les paiements validés
- Identification des charges déductibles
- Calcul des montants dus à chaque bailleur

### 2. Création des retraits
- Génération automatique ou manuelle
- Vérification des montants
- Association des paiements et charges

### 3. Validation
- Contrôle des montants
- Validation par un responsable
- Génération des reçus

### 4. Versement
- Effectuer le versement
- Marquer comme payé
- Archiver les documents

## URLs et vues

### URLs principales
- `/paiements/retraits-bailleurs/` : Liste des retraits
- `/paiements/retraits-bailleurs/create/` : Création manuelle
- `/paiements/retraits-bailleurs/auto-create/` : Création automatique
- `/paiements/retraits-bailleurs/<id>/` : Détails d'un retrait

### Vues principales
- `retrait_list` : Liste avec filtres et pagination
- `retrait_create` : Formulaire de création
- `retrait_auto_create` : Interface de création automatique
- `retrait_detail` : Affichage détaillé
- `retrait_validate` : Validation d'un retrait
- `retrait_mark_paid` : Marquage comme payé

## Templates

### Templates principaux
- `retrait_list.html` : Liste des retraits avec statistiques
- `retrait_create.html` : Formulaire de création
- `retrait_auto_create.html` : Interface de création automatique
- `retrait_detail.html` : Détails d'un retrait
- `recu_retrait_paysage.html` : Reçu en format paysage

### Fonctionnalités des templates
- Interface responsive avec Bootstrap
- Filtres avancés
- Statistiques en temps réel
- Actions contextuelles
- Modales de confirmation

## Administration Django

### RetraitBailleurAdmin
- Affichage des informations principales
- Filtres par statut, type, mode
- Actions en masse (validation, paiement, annulation)
- Optimisation des requêtes

### RetraitChargeDeductibleAdmin
- Gestion des liaisons retrait-charge
- Interface simplifiée

### RecuRetraitAdmin
- Gestion des reçus
- Suivi des impressions
- Actions de marquage

## Sécurité et permissions

### Décorateurs d'authentification
- `@login_required` sur toutes les vues
- Vérification des permissions utilisateur
- Protection CSRF sur tous les formulaires

### Validation des données
- Vérification des montants
- Contrôle des dates
- Validation des relations

## Intégration avec le système existant

### Modèles existants utilisés
- `Bailleur` : Informations des propriétaires
- `Paiement` : Loyers perçus
- `ChargeDeductible` : Charges à déduire
- `Contrat` : Contrats de location actifs

### Compatibilité
- Respect de la structure existante
- Utilisation des conventions de nommage
- Intégration avec l'interface utilisateur

## Avantages du système

### 1. Clarification des flux
- Distinction claire entre paiements et retraits
- Traçabilité complète des opérations
- Séparation des responsabilités

### 2. Automatisation
- Calculs automatiques des montants
- Génération en masse des retraits
- Réduction des erreurs manuelles

### 3. Transparence
- Reçus détaillés pour les bailleurs
- Historique complet des actions
- Suivi des statuts

### 4. Flexibilité
- Création manuelle ou automatique
- Gestion des différents types de retraits
- Adaptation aux besoins de l'agence

## Utilisation recommandée

### 1. Configuration initiale
- Vérifier les modèles et migrations
- Configurer les permissions utilisateur
- Tester avec des données d'exemple

### 2. Utilisation quotidienne
- Création automatique en fin de mois
- Validation des retraits
- Génération et impression des reçus

### 3. Maintenance
- Vérification régulière des calculs
- Archivage des retraits payés
- Suivi des statistiques

## Conclusion

Le système de retraits aux bailleurs apporte une solution complète et professionnelle pour gérer les versements aux propriétaires. Il clarifie les flux financiers, automatise les calculs et fournit une traçabilité complète des opérations.

Cette implémentation respecte les standards Django et s'intègre harmonieusement avec le système existant de Rentila.
