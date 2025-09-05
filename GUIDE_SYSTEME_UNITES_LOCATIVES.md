# Guide du Système de Gestion des Unités Locatives

## Vue d'ensemble

Le système de gestion des unités locatives est une extension avancée du système GESTIMMOB, spécialement conçue pour les grandes propriétés avec de nombreuses unités locatives (appartements, bureaux, chambres, etc.).

## 🏢 Fonctionnalités Principales

### 1. Gestion des Unités Locatives

#### Types d'Unités Supportées
- **Appartements** : Logements complets avec plusieurs pièces
- **Studios** : Logements d'une pièce principale
- **Bureaux** : Espaces de travail professionnels
- **Locaux commerciaux** : Espaces commerciaux
- **Chambres meublées** : Chambres individuelles avec mobilier
- **Places de parking** : Espaces de stationnement
- **Caves/Débarras** : Espaces de stockage

#### Informations Détaillées par Unité
- **Identification** : Numéro d'unité, nom descriptif
- **Localisation** : Étage, position dans le bâtiment
- **Caractéristiques** : Surface, nombre de pièces, équipements
- **Financier** : Loyer, charges, caution
- **État** : Disponible, occupée, réservée, en rénovation

### 2. Système de Réservation

#### Gestion des Réservations
- **Réservation temporaire** d'unités disponibles
- **Durée configurable** des réservations (par défaut 7 jours)
- **Suivi des statuts** : En attente, confirmée, expirée, annulée
- **Conversion automatique** en contrat de location

#### Workflow de Réservation
1. **Réservation initiale** par un locataire potentiel
2. **Période de grâce** pour finaliser les démarches
3. **Confirmation** ou **expiration** automatique
4. **Conversion en contrat** si confirmée

### 3. Tableau de Bord Spécialisé

#### Vue d'Ensemble Propriété
- **Statistiques en temps réel** : Taux d'occupation, revenus
- **Répartition par étage** : Visualisation de l'occupation
- **Revenus actuels vs potentiels** : Analyse de rentabilité
- **Prochaines échéances** : Contrats se terminant

#### Indicateurs Clés
- **Taux d'occupation global** de la propriété
- **Revenus mensuels actuels** (unités occupées)
- **Revenus potentiels** (toutes unités)
- **Manque à gagner** (différence entre potentiel et actuel)

### 4. Gestion Avancée

#### Filtrage et Recherche
- **Filtres multiples** : Par propriété, statut, type, étage
- **Recherche textuelle** : Par numéro, nom, description
- **Tri intelligent** : Par revenus, surface, disponibilité

#### Rapports et Analyses
- **Rapports d'occupation** par période
- **Analyses de rentabilité** par unité/étage
- **Statistiques détaillées** : Surface moyenne, loyer moyen

## 🚀 Utilisation du Système

### Accès au Système

#### Navigation
- **Menu principal** → Propriétés → Unités Locatives
- **Tableau de bord propriété** → Bouton "Dashboard" sur les grandes propriétés

#### URLs Principales
- `/proprietes/unites/` : Liste des unités locatives
- `/proprietes/{id}/dashboard/` : Tableau de bord propriété
- `/proprietes/unites/{id}/` : Détail d'une unité

### Création d'Unités Locatives

#### Étapes de Création
1. **Sélectionner la propriété** parente
2. **Définir l'identification** : Numéro et nom
3. **Spécifier les caractéristiques** : Type, surface, pièces
4. **Configurer les équipements** : Meublé, balcon, parking
5. **Définir les tarifs** : Loyer, charges, caution

#### Bonnes Pratiques
- **Numérotation cohérente** : Ex: Apt 101, Apt 102, etc.
- **Noms descriptifs** : "Appartement 2 pièces Sud"
- **Étages logiques** : 0=RDC, -1=Sous-sol, 1=1er étage

### Gestion des Réservations

#### Processus de Réservation
1. **Unité disponible** → Bouton "Réserver"
2. **Sélectionner le locataire** potentiel
3. **Définir la date de début** souhaitée
4. **Configurer l'expiration** (7 jours par défaut)
5. **Ajouter des notes** si nécessaire

#### Suivi des Réservations
- **Statut en temps réel** dans le tableau de bord
- **Notifications d'expiration** automatiques
- **Conversion en contrat** facilitée

### Tableau de Bord Propriété

#### Accès Automatique
Le système détecte automatiquement les **grandes propriétés** (plus de 5 unités) et propose un tableau de bord spécialisé.

#### Fonctionnalités du Dashboard
- **Vue circulaire du taux d'occupation**
- **Graphiques par étage** avec répartition
- **Liste des réservations en attente**
- **Alertes pour les échéances** (60 jours)

## 🔧 Configuration et Administration

### Paramètres Système

#### Types d'Unités
Les types d'unités sont configurables dans le modèle `UniteLocative.TYPE_UNITE_CHOICES`.

#### Statuts Disponibles
- **Disponible** : Prête à la location
- **Occupée** : Actuellement louée
- **Réservée** : Temporairement réservée
- **En rénovation** : Travaux en cours
- **Hors service** : Indisponible temporairement

### Intégration avec l'Existant

#### Relation avec les Propriétés
Chaque unité locative est liée à une propriété parente et peut contenir des pièces individuelles.

#### Compatibilité Contrats
Les contrats peuvent être liés soit à :
- Des **pièces individuelles** (système traditionnel)
- Une **unité locative complète** (nouveau système)

### Permissions et Sécurité

#### Groupes d'Utilisateurs
- **PRIVILEGE** : Accès complet à la gestion
- **CAISSE** : Consultation et création de réservations
- **Autres groupes** : Consultation selon les permissions

## 📊 Analyses et Rapports

### Métriques Disponibles

#### Par Propriété
- Taux d'occupation global
- Revenus mensuels (actuels/potentiels)
- Répartition par type d'unité
- Performance par étage

#### Par Unité
- Historique d'occupation
- Revenus générés
- Durée moyenne des contrats
- Taux de rotation

### Exportation de Données

Les données peuvent être exportées via :
- **APIs REST** pour intégration
- **Rapports PDF** pour présentation
- **Exports CSV** pour analyse

## 🎯 Cas d'Usage Typiques

### Immeuble Résidentiel
- **50 appartements** sur 10 étages
- **Gestion centralisée** des disponibilités
- **Suivi des revenus** par étage/type
- **Planification des rénovations**

### Complexe de Bureaux
- **Bureaux de différentes tailles**
- **Tarification variable** selon surface/étage
- **Gestion des services inclus**
- **Suivi des échéances commerciales**

### Résidence Étudiante
- **Chambres meublées individuelles**
- **Réservations courte durée**
- **Gestion saisonnière**
- **Services inclus** (internet, ménage)

## 🔄 Migration depuis l'Ancien Système

### Données Existantes
Le nouveau système coexiste avec l'ancien système de pièces. Les propriétés existantes continuent de fonctionner normalement.

### Mise à Niveau Graduelle
1. **Identifier les grandes propriétés** candidates
2. **Créer les unités locatives** correspondantes
3. **Migrer les contrats** progressivement
4. **Former les utilisateurs** au nouveau système

### Compatibilité Ascendante
- Les **anciennes fonctionnalités** restent disponibles
- Les **nouveaux outils** s'ajoutent sans perturber l'existant
- **Migration optionnelle** selon les besoins

## 📞 Support et Formation

### Documentation Technique
- Code source commenté
- APIs documentées
- Tests unitaires inclus

### Formation Utilisateurs
- Guide d'utilisation détaillé
- Exemples pratiques
- Support technique disponible

---

**Version** : 1.0  
**Date** : Janvier 2025  
**Système** : GESTIMMOB - Extension Unités Locatives
