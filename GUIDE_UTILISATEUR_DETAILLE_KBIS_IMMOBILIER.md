# 📚 Guide Utilisateur Détaillé - KBIS Immobilier
## Système de Gestion Immobilière Professionnel

---

## 🎯 Table des Matières

1. [Introduction Détaillée](#introduction-détaillée)
2. [Installation et Première Connexion](#installation-et-première-connexion)
3. [Interface Utilisateur Complète](#interface-utilisateur-complète)
4. [Gestion des Propriétés - Guide Complet](#gestion-des-propriétés---guide-complet)
5. [Gestion des Bailleurs - Procédures Détaillées](#gestion-des-bailleurs---procédures-détaillées)
6. [Gestion des Locataires - Workflow Complet](#gestion-des-locataires---workflow-complet)
7. [Système de Contrats - Processus Détaillé](#système-de-contrats---processus-détaillé)
8. [Système de Paiements - Guide Complet](#système-de-paiements---guide-complet)
9. [Rapports et Récapitulatifs - Procédures Détaillées](#rapports-et-récapitulatifs---procédures-détaillées)
10. [Gestion des Unités Locatives - Guide Avancé](#gestion-des-unités-locatives---guide-avancé)
11. [Système de Notifications - Configuration](#système-de-notifications---configuration)
12. [Actions Rapides et Raccourcis](#actions-rapides-et-raccourcis)
13. [FAQ Détaillée et Dépannage](#faq-détaillée-et-dépannage)
14. [Formation et Support](#formation-et-support)

---

## 🚀 Introduction Détaillée

### Qu'est-ce que KBIS Immobilier ?
**KBIS Immobilier** est un système de gestion immobilière complet et professionnel conçu spécifiquement pour les gestionnaires de patrimoine immobilier au Burkina Faso. L'application simplifie et automatise tous les aspects de la gestion locative.

### 🎯 Objectifs de l'Application
- **Centraliser** toutes les informations immobilières
- **Automatiser** les processus de gestion
- **Faciliter** le suivi des paiements et contrats
- **Générer** des rapports financiers précis
- **Optimiser** la communication avec bailleurs et locataires

### 🏢 Types d'Utilisateurs et Permissions

#### 👑 Administrateur
**Accès complet à toutes les fonctionnalités**
- ✅ Gestion des utilisateurs et groupes
- ✅ Configuration du système
- ✅ Accès à tous les modules
- ✅ Génération de tous les rapports
- ✅ Gestion des sauvegardes

#### 💰 Caissier
**Spécialisé dans la gestion financière**
- ✅ Enregistrement des paiements
- ✅ Génération de reçus
- ✅ Gestion des retraits
- ✅ Suivi des impayés
- ❌ Modification des propriétés
- ❌ Gestion des utilisateurs

#### 🔍 Contrôleur
**Gestion des propriétés et contrats**
- ✅ Gestion des propriétés
- ✅ Gestion des contrats
- ✅ Gestion des locataires
- ✅ Consultation des paiements
- ❌ Enregistrement des paiements
- ❌ Gestion des utilisateurs

#### ⭐ Utilisateur Privilégié
**Accès étendu avec limitations**
- ✅ Gestion des propriétés
- ✅ Gestion des contrats
- ✅ Consultation des paiements
- ✅ Génération de rapports limités
- ❌ Gestion des utilisateurs
- ❌ Configuration système

---

## 🔐 Installation et Première Connexion

### 🌐 Accès à l'Application

#### URL de Production
```
https://78.138.58.185
```

#### URL de Connexion
```
https://78.138.58.185/utilisateurs/connexion-groupes/
```

### 📱 Compatibilité Navigateurs
- **Chrome** 90+ (Recommandé)
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

### 🔑 Processus de Connexion Détaillé

#### Étape 1 : Accès à la Page de Connexion
1. Ouvrez votre navigateur web
2. Tapez l'URL : `https://78.138.58.185`
3. Vous serez redirigé vers la page de connexion
4. **Interface visible** :
   ```
   ┌─────────────────────────────────────┐
   │  🏠 KBIS IMMOBILIER                │
   │  Système de Gestion Immobilière    │
   │                                     │
   │  Nom d'utilisateur: [___________]  │
   │  Mot de passe:     [___________]   │
   │                                     │
   │  [Se connecter]                     │
   │                                     │
   │  Mot de passe oublié ?              │
   └─────────────────────────────────────┘
   ```

#### Étape 2 : Saisie des Identifiants
1. **Nom d'utilisateur** : Votre identifiant fourni par l'administrateur
   - Format : `prenom.nom` ou `nom_utilisateur`
   - Exemple : `jean.dupont` ou `admin`

2. **Mot de passe** : Votre mot de passe personnel
   - Minimum 8 caractères
   - Contient au moins une majuscule et un chiffre

#### Étape 3 : Connexion
1. Cliquez sur **"Se connecter"**
2. **Si succès** : Redirection vers le tableau de bord
3. **Si échec** : Message d'erreur affiché

### 🚨 Gestion des Erreurs de Connexion

#### Erreur : "Nom d'utilisateur ou mot de passe incorrect"
**Solutions** :
1. Vérifiez l'orthographe du nom d'utilisateur
2. Vérifiez la casse (majuscules/minuscules)
3. Vérifiez que le Caps Lock n'est pas activé
4. Contactez l'administrateur pour réinitialiser le mot de passe

#### Erreur : "Compte désactivé"
**Solutions** :
1. Contactez l'administrateur
2. Vérifiez que votre compte est actif
3. Attendez la réactivation

#### Erreur : "Connexion impossible"
**Solutions** :
1. Vérifiez votre connexion internet
2. Vérifiez que l'URL est correcte
3. Contactez le support technique

---

## 🖥️ Interface Utilisateur Complète

### 📊 Tableau de Bord Principal

#### Structure de l'Interface
```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 KBIS IMMOBILIER                    👤 Jean Dupont [▼]   │
├─────────────────────────────────────────────────────────────┤
│ 📊 Tableau de Bord                                         │
│                                                             │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│ │ 🏠 25   │ │ 👥 45   │ │ 💰 12   │ │ 📄 8    │           │
│ │Propriétés│ │Bailleurs│ │Locataires│ │Contrats │           │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💰 Revenus du Mois : 2,450,000 F CFA                   │ │
│ │ 📈 Paiements en Attente : 3                           │ │
│ │ ⚠️ Contrats à Renouveler : 2                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⚡ Actions Rapides                                      │ │
│ │ [➕ Ajouter Propriété] [💰 Enregistrer Paiement]      │ │
│ │ [📄 Créer Contrat] [📊 Générer Rapport]               │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Menu de Navigation Latéral
```
┌─────────────────┐
│ 📊 Tableau de   │
│    Bord         │
├─────────────────┤
│ 🏠 Propriétés   │
│ 👥 Bailleurs    │
│ 🏠 Locataires   │
│ 📄 Contrats     │
│ 💰 Paiements    │
│ 📊 Rapports     │
│ 🏢 Unités       │
│ 🔔 Notifications│
│ ⚙️ Paramètres   │
└─────────────────┘
```

### 🎨 Éléments de l'Interface

#### Barre de Navigation Supérieure
- **Logo** : KBIS Immobilier
- **Titre de la page** : Module actuel
- **Profil utilisateur** : Nom et menu déroulant
- **Notifications** : Badge avec nombre de notifications

#### Cartes Statistiques
- **Couleur** : Bleu, vert, orange, rouge
- **Icône** : Représentant le type de données
- **Nombre** : Valeur principale
- **Label** : Description
- **Tendance** : Flèche de progression (si applicable)

#### Actions Rapides
- **Boutons colorés** : Chaque action a une couleur spécifique
- **Icônes** : Représentant l'action
- **Tooltips** : Description au survol
- **Raccourcis** : Indication des touches de raccourci

---

## 🏠 Gestion des Propriétés - Guide Complet

### 📋 Types de Biens Supportés

#### 🏢 Appartements
- **Description** : Logements complets avec plusieurs pièces
- **Caractéristiques** : Chambre(s), salon, cuisine, salle de bain
- **Usage** : Habitation principale ou secondaire
- **Exemples** : T2, T3, T4, T5, duplex

#### 🏡 Maisons
- **Description** : Habitations individuelles
- **Caractéristiques** : Jardin, garage, plusieurs niveaux
- **Usage** : Habitation familiale
- **Exemples** : Villa, pavillon, maison de ville

#### 🏠 Studios
- **Description** : Logements d'une pièce principale
- **Caractéristiques** : Pièce unique avec kitchenette
- **Usage** : Logement étudiant ou temporaire
- **Exemples** : Studio, chambre avec kitchenette

#### 🏢 Bureaux
- **Description** : Espaces de travail professionnels
- **Caractéristiques** : Espace ouvert ou divisé
- **Usage** : Activité professionnelle
- **Exemples** : Bureau individuel, open space

#### 🏪 Locaux Commerciaux
- **Description** : Espaces commerciaux
- **Caractéristiques** : Vitrine, stockage, parking
- **Usage** : Commerce, restauration, services
- **Exemples** : Boutique, restaurant, salon

#### 🛏️ Chambres Meublées
- **Description** : Chambres individuelles avec mobilier
- **Caractéristiques** : Meublée, équipée
- **Usage** : Logement temporaire ou étudiant
- **Exemples** : Chambre d'hôte, résidence étudiante

#### 🅿️ Places de Parking
- **Description** : Espaces de stationnement
- **Caractéristiques** : Couvert ou découvert
- **Usage** : Stationnement de véhicules
- **Exemples** : Box, place en extérieur

### ➕ Ajouter une Propriété - Processus Détaillé

#### Étape 1 : Accès au Formulaire
1. Cliquez sur **"Propriétés"** dans le menu latéral
2. Cliquez sur **"Ajouter une propriété"** (bouton vert avec icône +)
3. **URL** : `/proprietes/ajouter/`

#### Étape 2 : Formulaire de Création
```
┌─────────────────────────────────────────────────────────────┐
│ ➕ Ajouter une Propriété                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Informations Générales                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Titre *: [Appartement T3 - Ouagadougou]               │ │
│ │ Type de bien *: [Appartement ▼]                       │ │
│ │ Surface (m²) *: [85]                                  │ │
│ │ Nombre de pièces: [3]                                 │ │
│ │ Nombre de chambres: [2]                               │ │
│ │ Nombre de salles de bain: [1]                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Adresse                                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Adresse *: [123 Avenue Kwame Nkrumah]                  │ │
│ │ Ville *: [Ouagadougou]                                 │ │
│ │ Code postal: [01 BP 1234]                              │ │
│ │ Quartier: [Secteur 1]                                  │ │
│ │ Référence: [Près du marché central]                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Financières                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Loyer mensuel (F CFA) *: [150000]                      │ │
│ │ Charges (F CFA): [15000]                               │ │
│ │ Caution (F CFA): [300000]                              │ │
│ │ Frais d'agence (F CFA): [75000]                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Description et Détails                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Description: [Appartement moderne avec balcon...]      │ │
│ │ Équipements: [Climatisation, Internet, Parking]        │ │
│ │ État: [Bon état]                                       │ │
│ │ Disponible: [☑ Oui]                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Enregistrer]                                     │
└─────────────────────────────────────────────────────────────┘
```

#### Étape 3 : Remplissage du Formulaire

##### Informations Générales
- **Titre** (obligatoire) : Nom descriptif de la propriété
  - Exemple : "Appartement T3 - Ouagadougou"
  - Longueur : 3-100 caractères
  - Caractères autorisés : Lettres, chiffres, espaces, tirets

- **Type de bien** (obligatoire) : Sélection dans la liste déroulante
  - Options : Appartement, Maison, Studio, Bureau, Local commercial, Chambre meublée, Place de parking
  - Impact : Détermine les champs suivants

- **Surface** (obligatoire) : Surface en mètres carrés
  - Format : Nombre entier
  - Minimum : 1 m²
  - Maximum : 10000 m²
  - Exemple : 85

- **Nombre de pièces** : Nombre total de pièces
  - Format : Nombre entier
  - Minimum : 1
  - Exemple : 3

- **Nombre de chambres** : Nombre de chambres à coucher
  - Format : Nombre entier
  - Minimum : 0
  - Exemple : 2

- **Nombre de salles de bain** : Nombre de salles de bain
  - Format : Nombre entier
  - Minimum : 0
  - Exemple : 1

##### Adresse
- **Adresse** (obligatoire) : Adresse complète
  - Exemple : "123 Avenue Kwame Nkrumah"
  - Longueur : 5-200 caractères

- **Ville** (obligatoire) : Ville de localisation
  - Exemple : "Ouagadougou"
  - Longueur : 2-50 caractères

- **Code postal** : Code postal (optionnel)
  - Format : Alphanumérique
  - Exemple : "01 BP 1234"

- **Quartier** : Quartier ou secteur
  - Exemple : "Secteur 1"
  - Longueur : 2-50 caractères

- **Référence** : Points de repère
  - Exemple : "Près du marché central"
  - Longueur : 0-200 caractères

##### Informations Financières
- **Loyer mensuel** (obligatoire) : Montant du loyer en F CFA
  - Format : Nombre décimal
  - Minimum : 1000 F CFA
  - Maximum : 10,000,000 F CFA
  - Exemple : 150000

- **Charges** : Montant des charges mensuelles
  - Format : Nombre décimal
  - Minimum : 0 F CFA
  - Exemple : 15000

- **Caution** : Montant de la caution
  - Format : Nombre décimal
  - Minimum : 0 F CFA
  - Exemple : 300000

- **Frais d'agence** : Frais d'agence (si applicable)
  - Format : Nombre décimal
  - Minimum : 0 F CFA
  - Exemple : 75000

##### Description et Détails
- **Description** : Description détaillée de la propriété
  - Longueur : 0-1000 caractères
  - Exemple : "Appartement moderne avec balcon, vue sur la ville"

- **Équipements** : Liste des équipements
  - Exemple : "Climatisation, Internet, Parking"
  - Longueur : 0-500 caractères

- **État** : État général de la propriété
  - Options : Excellent, Bon état, Moyen, À rénover
  - Exemple : "Bon état"

- **Disponible** : Propriété disponible à la location
  - Case à cocher : Oui/Non
  - Par défaut : Oui

#### Étape 4 : Validation et Enregistrement
1. **Vérification** : Vérifiez tous les champs obligatoires
2. **Validation** : Cliquez sur "Enregistrer"
3. **Confirmation** : Message de succès affiché
4. **Redirection** : Vers la page de détail de la propriété

### ✏️ Modifier une Propriété

#### Accès à la Modification
1. Dans la liste des propriétés, cliquez sur l'icône **"Modifier"** (crayon)
2. **URL** : `/proprietes/modifier/{id}/`
3. Le formulaire s'ouvre avec les données existantes

#### Processus de Modification
1. **Modification** : Changez les champs nécessaires
2. **Sauvegarde** : Cliquez sur "Enregistrer les modifications"
3. **Confirmation** : Message de succès affiché
4. **Redirection** : Vers la page de détail mise à jour

### 👁️ Détails d'une Propriété

#### Page de Détail
```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 Appartement T3 - Ouagadougou                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ 📍 Adresse      │ │ 💰 Financier    │ │ 📊 Statistiques │ │
│ │ 123 Av. Kwame   │ │ Loyer: 150,000  │ │ Occupé: 8 mois  │ │
│ │ Nkrumah         │ │ Charges: 15,000 │ │ Revenus: 1.2M   │ │
│ │ Ouagadougou     │ │ Caution: 300,000│ │ Taux: 100%      │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📄 Contrats Actifs (1)                                 │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Jean Dupont - 01/01/2024 au 31/12/2024            │ │ │
│ │ │ Loyer: 150,000 F CFA - Statut: Actif              │ │ │
│ │ │ [Voir] [Modifier] [Résilier]                      │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📸 Galerie Photos                                       │ │
│ │ [Photo 1] [Photo 2] [Photo 3] [➕ Ajouter]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Modifier] [Supprimer] [Retour à la liste]                 │
└─────────────────────────────────────────────────────────────┘
```

#### Sections de la Page de Détail

##### Informations Générales
- **Titre** : Nom de la propriété
- **Type** : Type de bien
- **Surface** : Surface en m²
- **Pièces** : Nombre de pièces, chambres, salles de bain
- **Adresse** : Adresse complète
- **Description** : Description détaillée
- **Équipements** : Liste des équipements
- **État** : État général

##### Informations Financières
- **Loyer mensuel** : Montant du loyer
- **Charges** : Montant des charges
- **Caution** : Montant de la caution
- **Frais d'agence** : Frais d'agence
- **Total mensuel** : Loyer + charges

##### Statistiques
- **Taux d'occupation** : Pourcentage d'occupation
- **Durée d'occupation** : Temps d'occupation actuel
- **Revenus totaux** : Revenus générés
- **Paiements en attente** : Nombre de paiements en attente

##### Contrats Actifs
- **Liste des contrats** : Contrats en cours
- **Locataire** : Nom du locataire
- **Période** : Dates de début et fin
- **Montant** : Loyer mensuel
- **Statut** : Actif, expiré, résilié
- **Actions** : Voir, modifier, résilier

##### Galerie Photos
- **Photos** : Images de la propriété
- **Ajouter** : Bouton pour ajouter des photos
- **Supprimer** : Bouton pour supprimer des photos
- **Aperçu** : Vue d'ensemble des photos

### 🔍 Recherche et Filtres

#### Barre de Recherche
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Rechercher une propriété... [Rechercher] [Filtres] ▼   │
└─────────────────────────────────────────────────────────────┘
```

#### Options de Recherche
- **Texte libre** : Recherche dans le titre, adresse, description
- **Ville** : Filtrage par ville
- **Type de bien** : Filtrage par type
- **Prix** : Filtrage par fourchette de prix
- **Surface** : Filtrage par surface
- **Disponibilité** : Disponible, occupée, en maintenance

#### Filtres Avancés
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Filtres Avancés                                         │
├─────────────────────────────────────────────────────────────┤
│ Ville: [Ouagadougou ▼]                                     │
│ Type: [Appartement ▼]                                      │
│ Prix min: [100000] Prix max: [500000]                      │
│ Surface min: [50] Surface max: [200]                       │
│ Disponible: [☑ Oui] [☐ Non] [☐ Tous]                     │
│ État: [Bon état ▼]                                         │
│                                                             │
│ [Réinitialiser] [Appliquer] [Fermer]                       │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Liste des Propriétés

#### Tableau des Propriétés
```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 Liste des Propriétés (25)                               │
├─────────────────────────────────────────────────────────────┤
│ Titre              │ Adresse        │ Type    │ Loyer  │ État│
├─────────────────────────────────────────────────────────────┤
│ Appartement T3     │ 123 Av. Kwame  │ Appart. │ 150,000│ Actif│
│ Maison Villa       │ 456 Rue de la  │ Maison  │ 300,000│ Actif│
│ Studio Moderne     │ 789 Bd. de la  │ Studio  │ 80,000 │ Libre│
│ Bureau Centre      │ 321 Av. de la  │ Bureau  │ 200,000│ Actif│
└─────────────────────────────────────────────────────────────┘
```

#### Actions sur les Propriétés
- **👁️ Voir** : Afficher les détails
- **✏️ Modifier** : Modifier les informations
- **🗑️ Supprimer** : Supprimer la propriété
- **📄 Contrats** : Voir les contrats
- **💰 Paiements** : Voir les paiements

---

## 👥 Gestion des Bailleurs - Procédures Détaillées

### ➕ Ajouter un Bailleur - Processus Complet

#### Étape 1 : Accès au Formulaire
1. Cliquez sur **"Bailleurs"** dans le menu latéral
2. Cliquez sur **"Ajouter un bailleur"** (bouton vert)
3. **URL** : `/proprietes/ajouter_bailleur/`

#### Étape 2 : Formulaire de Création Détaillé
```
┌─────────────────────────────────────────────────────────────┐
│ ➕ Ajouter un Bailleur                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Informations Personnelles                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Prénom *: [Jean]                                       │ │
│ │ Nom *: [Dupont]                                        │ │
│ │ Nom complet: [Jean Dupont] (auto-généré)               │ │
│ │ Téléphone *: [226 70 12 34 56]                        │ │
│ │ Email: [jean.dupont@email.com]                         │ │
│ │ Date de naissance: [15/03/1980]                        │ │
│ │ Lieu de naissance: [Ouagadougou]                        │ │
│ │ Nationalité: [Burkinabè]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Professionnelles                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Profession: [Ingénieur]                                │ │
│ │ Employeur: [Société ABC]                               │ │
│ │ Adresse professionnelle: [123 Rue de la Paix]          │ │
│ │ Téléphone professionnel: [226 50 12 34 56]             │ │
│ │ Email professionnel: [j.dupont@societe.com]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Adresse de Résidence                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Adresse *: [456 Avenue de l'Indépendance]              │ │
│ │ Ville *: [Ouagadougou]                                 │ │
│ │ Code postal: [01 BP 5678]                              │ │
│ │ Quartier: [Secteur 2]                                  │ │
│ │ Pays: [Burkina Faso]                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Bancaires                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ IBAN *: [BF42BF0840101300463574000390]                 │ │
│ │ BIC: [BF42BF08]                                        │ │
│ │ Nom de la banque: [Banque Atlantique]                  │ │
│ │ Numéro de compte: [1300463574000390]                   │ │
│ │ Titulaire du compte: [Jean Dupont]                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Supplémentaires                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Type de bailleur: [Personne physique ▼]                │ │
│ │ Statut: [Actif]                                        │ │
│ │ Notes: [Bailleur fiable, paiements ponctuels]          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Enregistrer]                                     │
└─────────────────────────────────────────────────────────────┘
```

#### Étape 3 : Remplissage Détaillé du Formulaire

##### Informations Personnelles
- **Prénom** (obligatoire) : Prénom du bailleur
  - Longueur : 2-50 caractères
  - Caractères autorisés : Lettres, espaces, tirets
  - Exemple : "Jean"

- **Nom** (obligatoire) : Nom de famille
  - Longueur : 2-50 caractères
  - Caractères autorisés : Lettres, espaces, tirets
  - Exemple : "Dupont"

- **Nom complet** : Généré automatiquement
  - Format : "Prénom Nom"
  - Exemple : "Jean Dupont"

- **Téléphone** (obligatoire) : Numéro de téléphone
  - Format : 226 XX XX XX XX
  - Longueur : 12 caractères
  - Exemple : "226 70 12 34 56"

- **Email** : Adresse email (optionnel)
  - Format : email@domaine.com
  - Longueur : 5-100 caractères
  - Exemple : "jean.dupont@email.com"

- **Date de naissance** : Date de naissance (optionnel)
  - Format : JJ/MM/AAAA
  - Exemple : "15/03/1980"

- **Lieu de naissance** : Ville de naissance (optionnel)
  - Longueur : 2-50 caractères
  - Exemple : "Ouagadougou"

- **Nationalité** : Nationalité (optionnel)
  - Exemple : "Burkinabè"

##### Informations Professionnelles
- **Profession** : Profession exercée
  - Longueur : 2-100 caractères
  - Exemple : "Ingénieur"

- **Employeur** : Nom de l'employeur
  - Longueur : 2-100 caractères
  - Exemple : "Société ABC"

- **Adresse professionnelle** : Adresse du lieu de travail
  - Longueur : 5-200 caractères
  - Exemple : "123 Rue de la Paix"

- **Téléphone professionnel** : Téléphone professionnel
  - Format : 226 XX XX XX XX
  - Exemple : "226 50 12 34 56"

- **Email professionnel** : Email professionnel
  - Format : email@domaine.com
  - Exemple : "j.dupont@societe.com"

##### Adresse de Résidence
- **Adresse** (obligatoire) : Adresse de résidence
  - Longueur : 5-200 caractères
  - Exemple : "456 Avenue de l'Indépendance"

- **Ville** (obligatoire) : Ville de résidence
  - Longueur : 2-50 caractères
  - Exemple : "Ouagadougou"

- **Code postal** : Code postal (optionnel)
  - Format : Alphanumérique
  - Exemple : "01 BP 5678"

- **Quartier** : Quartier ou secteur
  - Longueur : 2-50 caractères
  - Exemple : "Secteur 2"

- **Pays** : Pays de résidence
  - Par défaut : "Burkina Faso"

##### Informations Bancaires
- **IBAN** (obligatoire) : Code IBAN du compte
  - Format : BF42BF0840101300463574000390
  - Longueur : 28 caractères
  - Exemple : "BF42BF0840101300463574000390"

- **BIC** : Code BIC de la banque
  - Format : 8 caractères
  - Exemple : "BF42BF08"

- **Nom de la banque** : Nom de l'établissement bancaire
  - Longueur : 2-100 caractères
  - Exemple : "Banque Atlantique"

- **Numéro de compte** : Numéro de compte bancaire
  - Longueur : 10-20 caractères
  - Exemple : "1300463574000390"

- **Titulaire du compte** : Nom du titulaire du compte
  - Longueur : 2-100 caractères
  - Exemple : "Jean Dupont"

##### Informations Supplémentaires
- **Type de bailleur** : Personne physique ou morale
  - Options : Personne physique, Personne morale
  - Exemple : "Personne physique"

- **Statut** : Statut du bailleur
  - Options : Actif, Inactif, Suspendu
  - Par défaut : "Actif"

- **Notes** : Notes supplémentaires
  - Longueur : 0-500 caractères
  - Exemple : "Bailleur fiable, paiements ponctuels"

#### Étape 4 : Validation et Enregistrement
1. **Vérification** : Vérifiez tous les champs obligatoires
2. **Validation IBAN** : Vérification automatique du format IBAN
3. **Validation email** : Vérification du format email
4. **Enregistrement** : Cliquez sur "Enregistrer"
5. **Confirmation** : Message de succès affiché
6. **Redirection** : Vers la page de détail du bailleur

### 👁️ Détails d'un Bailleur

#### Page de Détail Complète
```
┌─────────────────────────────────────────────────────────────┐
│ 👥 Jean Dupont - Bailleur                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ 📞 Contact      │ │ 🏦 Bancaire     │ │ 📊 Statistiques │ │
│ │ Tél: 70 12 34 56│ │ IBAN: BF42BF08  │ │ Propriétés: 3   │ │
│ │ Email: jean@... │ │ Banque: Atlant. │ │ Revenus: 450K   │ │
│ │ Adresse: 456... │ │ Compte: 1300... │ │ Actif: 8 mois   │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🏠 Propriétés (3)                                      │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Appartement T3 - Ouagadougou                       │ │ │
│ │ │ Loyer: 150,000 F CFA - Statut: Occupé             │ │ │
│ │ │ [Voir] [Modifier] [Contrats]                      │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Maison Villa - Bobo-Dioulasso                      │ │ │
│ │ │ Loyer: 300,000 F CFA - Statut: Libre              │ │ │
│ │ │ [Voir] [Modifier] [Contrats]                      │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💰 Historique des Retraits                             │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ 15/01/2024 - 150,000 F CFA - Validé               │ │ │
│ │ │ 15/12/2023 - 150,000 F CFA - Validé               │ │ │
│ │ │ 15/11/2023 - 150,000 F CFA - Validé               │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Modifier] [Supprimer] [Retour à la liste]                 │
└─────────────────────────────────────────────────────────────┘
```

#### Sections de la Page de Détail

##### Informations de Contact
- **Nom complet** : Prénom et nom
- **Téléphone** : Numéro de téléphone principal
- **Email** : Adresse email
- **Adresse** : Adresse de résidence complète
- **Profession** : Profession exercée
- **Employeur** : Nom de l'employeur

##### Informations Bancaires
- **IBAN** : Code IBAN complet
- **BIC** : Code BIC de la banque
- **Banque** : Nom de l'établissement bancaire
- **Compte** : Numéro de compte
- **Titulaire** : Nom du titulaire du compte

##### Statistiques
- **Nombre de propriétés** : Total des propriétés
- **Revenus mensuels** : Revenus générés par mois
- **Durée d'activité** : Temps depuis le premier contrat
- **Taux d'occupation** : Pourcentage d'occupation des propriétés

##### Propriétés Associées
- **Liste des propriétés** : Toutes les propriétés du bailleur
- **Informations** : Titre, adresse, loyer, statut
- **Actions** : Voir, modifier, gérer les contrats

##### Historique des Retraits
- **Liste des retraits** : Historique des paiements reçus
- **Dates** : Date de chaque retrait
- **Montants** : Montant de chaque retrait
- **Statut** : Validé, en attente, refusé

### 🔍 Recherche et Filtres des Bailleurs

#### Barre de Recherche
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Rechercher un bailleur... [Rechercher] [Filtres] ▼     │
└─────────────────────────────────────────────────────────────┘
```

#### Options de Recherche
- **Texte libre** : Recherche dans le nom, prénom, email
- **Ville** : Filtrage par ville de résidence
- **Statut** : Actif, inactif, suspendu
- **Type** : Personne physique, personne morale
- **Banque** : Filtrage par établissement bancaire

#### Filtres Avancés
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Filtres Avancés                                         │
├─────────────────────────────────────────────────────────────┤
│ Ville: [Ouagadougou ▼]                                     │
│ Statut: [Actif ▼]                                          │
│ Type: [Personne physique ▼]                                │
│ Banque: [Banque Atlantique ▼]                              │
│ Revenus min: [100000] Revenus max: [1000000]               │
│ Propriétés min: [1] Propriétés max: [10]                   │
│                                                             │
│ [Réinitialiser] [Appliquer] [Fermer]                       │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Liste des Bailleurs

#### Tableau des Bailleurs
```
┌─────────────────────────────────────────────────────────────┐
│ 👥 Liste des Bailleurs (45)                                │
├─────────────────────────────────────────────────────────────┤
│ Nom                │ Téléphone      │ Ville      │ Propriétés│
├─────────────────────────────────────────────────────────────┤
│ Jean Dupont        │ 70 12 34 56    │ Ouagadougou│ 3         │
│ Marie Traoré       │ 70 23 45 67    │ Bobo-Dioul.│ 2         │
│ Paul Ouédraogo     │ 70 34 56 78    │ Ouagadougou│ 1         │
│ Fatou Sawadogo     │ 70 45 67 89    │ Koudougou  │ 4         │
└─────────────────────────────────────────────────────────────┘
```

#### Actions sur les Bailleurs
- **👁️ Voir** : Afficher les détails complets
- **✏️ Modifier** : Modifier les informations
- **🗑️ Supprimer** : Supprimer le bailleur
- **🏠 Propriétés** : Voir les propriétés
- **💰 Retraits** : Voir l'historique des retraits

---

## 🏠 Gestion des Locataires - Workflow Complet

### ➕ Ajouter un Locataire - Processus Détaillé

#### Étape 1 : Accès au Formulaire
1. Cliquez sur **"Locataires"** dans le menu latéral
2. Cliquez sur **"Ajouter un locataire"** (bouton vert)
3. **URL** : `/proprietes/ajouter_locataire/`

#### Étape 2 : Formulaire de Création Complet
```
┌─────────────────────────────────────────────────────────────┐
│ ➕ Ajouter un Locataire                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Informations Personnelles                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Prénom *: [Marie]                                      │ │
│ │ Nom *: [Traoré]                                        │ │
│ │ Nom complet: [Marie Traoré] (auto-généré)              │ │
│ │ Téléphone *: [226 70 23 45 67]                        │ │
│ │ Email: [marie.traore@email.com]                        │ │
│ │ Date de naissance: [22/07/1985]                        │ │
│ │ Lieu de naissance: [Bobo-Dioulasso]                    │ │
│ │ Nationalité: [Burkinabè]                               │ │
│ │ Pièce d'identité: [CNI]                                │ │
│ │ Numéro CNI: [123456789]                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Professionnelles                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Profession: [Infirmière]                               │ │
│ │ Employeur: [CHU de Bobo-Dioulasso]                     │ │
│ │ Adresse professionnelle: [456 Avenue de la Santé]      │ │
│ │ Téléphone professionnel: [226 50 23 45 67]             │ │
│ │ Salaire mensuel: [250000] F CFA                        │ │
│ │ Ancienneté: [5] années                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Adresse de Résidence                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Adresse *: [789 Rue de la Paix]                        │ │
│ │ Ville *: [Bobo-Dioulasso]                              │ │
│ │ Code postal: [01 BP 9012]                              │ │
│ │ Quartier: [Secteur 3]                                  │ │
│ │ Pays: [Burkina Faso]                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Bancaires                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ IBAN: [BF42BF0840101300463574000391]                   │ │
│ │ BIC: [BF42BF08]                                        │ │
│ │ Nom de la banque: [Banque Atlantique]                  │ │
│ │ Numéro de compte: [1300463574000391]                   │ │
│ │ Titulaire du compte: [Marie Traoré]                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Garant (Optionnel)                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Nom du garant: [Jean Traoré]                           │ │
│ │ Téléphone garant: [226 70 34 56 78]                    │ │
│ │ Profession garant: [Enseignant]                        │ │
│ │ Relation: [Père]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Enregistrer]                                     │
└─────────────────────────────────────────────────────────────┘
```

### 👁️ Détails d'un Locataire

#### Page de Détail Complète
```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 Marie Traoré - Locataire                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ 📞 Contact      │ │ 💼 Profession   │ │ 📊 Statistiques │ │
│ │ Tél: 70 23 45 67│ │ Infirmière      │ │ Contrats: 1     │ │
│ │ Email: marie@...│ │ CHU Bobo-Dioul. │ │ Paiements: 12   │ │
│ │ Adresse: 789... │ │ Salaire: 250K   │ │ Dernier: 15/01  │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📄 Contrats Actifs (1)                                 │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Appartement T3 - Ouagadougou                       │ │ │
│ │ │ 01/01/2024 au 31/12/2024                          │ │ │
│ │ │ Loyer: 150,000 F CFA - Statut: Actif              │ │ │
│ │ │ [Voir] [Modifier] [Résilier]                      │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💰 Historique des Paiements                            │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ 15/01/2024 - 150,000 F CFA - Validé               │ │ │
│ │ │ 15/12/2023 - 150,000 F CFA - Validé               │ │ │
│ │ │ 15/11/2023 - 150,000 F CFA - Validé               │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Modifier] [Supprimer] [Retour à la liste]                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 Système de Contrats - Processus Détaillé

### ➕ Créer un Contrat - Workflow Complet

#### Étape 1 : Accès au Formulaire
1. Cliquez sur **"Contrats"** dans le menu latéral
2. Cliquez sur **"Créer un contrat"** (bouton vert)
3. **URL** : `/contrats/creer/`

#### Étape 2 : Formulaire de Création Détaillé
```
┌─────────────────────────────────────────────────────────────┐
│ ➕ Créer un Contrat de Location                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Sélection des Parties                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Propriété *: [Appartement T3 - Ouagadougou ▼]         │ │
│ │ Locataire *: [Marie Traoré ▼]                         │ │
│ │ Bailleur *: [Jean Dupont ▼]                           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Période de Location                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Date de début *: [01/01/2024]                          │ │
│ │ Date de fin *: [31/12/2024]                            │ │
│ │ Durée: [12] mois (calculée automatiquement)            │ │
│ │ Période d'essai: [1] mois                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Conditions Financières                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Loyer mensuel *: [150,000] F CFA                       │ │
│ │ Charges mensuelles: [15,000] F CFA                     │ │
│ │ Total mensuel: [165,000] F CFA (calculé)               │ │
│ │ Caution: [300,000] F CFA                               │ │
│ │ Frais d'agence: [75,000] F CFA                         │ │
│ │ Premier loyer: [165,000] F CFA                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Conditions Particulières                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Usage: [Habitation principale ▼]                       │ │
│ │ Animaux autorisés: [☐ Oui] [☑ Non]                    │ │
│ │ Fumeur: [☐ Oui] [☑ Non]                               │ │
│ │ Visites: [Avec préavis de 24h]                         │ │
│ │ Renouvellement: [Tacite]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Clauses Spéciales                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Clauses: [Le locataire s'engage à...]                  │ │
│ │ Notes: [Contrat standard avec clauses habituelles]     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Créer le Contrat]                               │
└─────────────────────────────────────────────────────────────┘
```

### 📋 Types de Contrats

#### 🏠 Contrat de Location Classique
- **Durée** : 1 à 3 ans
- **Usage** : Habitation principale
- **Renouvellement** : Tacite ou express
- **Résiliation** : 3 mois de préavis

#### 🏢 Contrat Commercial
- **Durée** : 3 à 9 ans
- **Usage** : Activité commerciale
- **Renouvellement** : Express
- **Résiliation** : 6 mois de préavis

#### 🏠 Contrat Temporaire
- **Durée** : 1 à 12 mois
- **Usage** : Logement temporaire
- **Renouvellement** : Express
- **Résiliation** : 1 mois de préavis

#### 🏠 Contrat de Sous-location
- **Durée** : Variable
- **Usage** : Sous-location
- **Renouvellement** : Selon contrat principal
- **Résiliation** : Selon contrat principal

---

## 💰 Système de Paiements - Guide Complet

### ➕ Enregistrer un Paiement - Processus Détaillé

#### Étape 1 : Accès au Formulaire
1. Cliquez sur **"Paiements"** dans le menu latéral
2. Cliquez sur **"Enregistrer un paiement"** (bouton vert)
3. **URL** : `/paiements/enregistrer/`

#### Étape 2 : Formulaire de Paiement Complet
```
┌─────────────────────────────────────────────────────────────┐
│ 💰 Enregistrer un Paiement                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Sélection du Contrat                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Contrat *: [Marie Traoré - Appartement T3 ▼]          │ │
│ │ Locataire: [Marie Traoré] (auto-rempli)               │ │
│ │ Propriété: [Appartement T3 - Ouagadougou] (auto-rempli)│ │
│ │ Bailleur: [Jean Dupont] (auto-rempli)                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations du Paiement                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Type de paiement *: [Loyer ▼]                         │ │
│ │ Montant *: [150,000] F CFA                            │ │
│ │ Montant des charges: [15,000] F CFA                   │ │
│ │ Montant net: [135,000] F CFA (calculé)                │ │
│ │ Date de paiement *: [15/01/2024]                      │ │
│ │ Période couverte: [Janvier 2024]                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Mode de Paiement                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Mode *: [Espèces ▼]                                    │ │
│ │ Référence: [REF-2024-001] (auto-générée)              │ │
│ │ Banque: [N/A] (si virement)                            │ │
│ │ Numéro de chèque: [N/A] (si chèque)                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Supplémentaires                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Statut: [En attente ▼]                                │ │
│ │ Notes: [Paiement en espèces reçu]                      │ │
│ │ Pièces jointes: [Aucun fichier choisi]                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Enregistrer]                                     │
└─────────────────────────────────────────────────────────────┘
```

### 💳 Types de Paiements

#### 💰 Loyer
- **Description** : Paiement mensuel du loyer
- **Fréquence** : Mensuelle
- **Montant** : Loyer + charges
- **Validation** : Automatique

#### 🏦 Caution
- **Description** : Dépôt de garantie
- **Fréquence** : Unique
- **Montant** : 1-3 mois de loyer
- **Validation** : Manuelle

#### 💵 Avance
- **Description** : Avance de loyer
- **Fréquence** : Variable
- **Montant** : Variable
- **Validation** : Manuelle

#### 🔧 Charges
- **Description** : Paiement des charges
- **Fréquence** : Mensuelle
- **Montant** : Charges mensuelles
- **Validation** : Automatique

#### ⚖️ Régularisation
- **Description** : Ajustement de montant
- **Fréquence** : Exceptionnelle
- **Montant** : Différence calculée
- **Validation** : Manuelle

### 💳 Modes de Paiement

#### 💵 Espèces
- **Description** : Paiement en liquide
- **Validation** : Immédiate
- **Preuve** : Reçu papier
- **Risque** : Faible

#### 🏦 Virement
- **Description** : Virement bancaire
- **Validation** : 24-48h
- **Preuve** : Relevé bancaire
- **Risque** : Très faible

#### 📄 Chèque
- **Description** : Paiement par chèque
- **Validation** : 5-10 jours
- **Preuve** : Chèque encaissé
- **Risque** : Moyen

#### 📱 Mobile Money
- **Description** : Paiement mobile
- **Validation** : Immédiate
- **Preuve** : SMS de confirmation
- **Risque** : Faible

### 📊 Gestion des Paiements

#### Liste des Paiements
```
┌─────────────────────────────────────────────────────────────┐
│ 💰 Liste des Paiements (156)                               │
├─────────────────────────────────────────────────────────────┤
│ Date       │ Locataire      │ Type    │ Montant  │ Statut  │
├─────────────────────────────────────────────────────────────┤
│ 15/01/2024│ Marie Traoré   │ Loyer   │ 150,000  │ Validé  │
│ 15/01/2024│ Paul Ouédraogo │ Loyer   │ 200,000  │ En att. │
│ 14/01/2024│ Fatou Sawadogo │ Caution │ 300,000  │ Validé  │
│ 13/01/2024│ Jean Kaboré    │ Loyer   │ 120,000  │ Refusé  │
└─────────────────────────────────────────────────────────────┘
```

#### Actions sur les Paiements
- **👁️ Voir** : Détails du paiement
- **✅ Valider** : Confirmer le paiement
- **❌ Refuser** : Rejeter le paiement
- **✏️ Modifier** : Modifier les informations
- **📄 Reçu** : Générer le reçu
- **🗑️ Supprimer** : Supprimer le paiement

---

## 📊 Rapports et Récapitulatifs - Procédures Détaillées

### 📈 Récapitulatifs Mensuels

#### Génération d'un Récapitulatif
1. Cliquez sur **"Rapports"** dans le menu latéral
2. Cliquez sur **"Récapitulatifs mensuels"**
3. **URL** : `/paiements/recapitulatifs/`

#### Formulaire de Génération
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Générer un Récapitulatif Mensuel                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Période                                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Mois *: [Janvier ▼]                                    │ │
│ │ Année *: [2024 ▼]                                      │ │
│ │ Type: [Récapitulatif général ▼]                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Filtres                                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Bailleur: [Tous ▼]                                     │ │
│ │ Propriété: [Toutes ▼]                                  │ │
│ │ Statut: [Tous ▼]                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Options de Génération                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Format: [PDF ▼]                                        │ │
│ │ Envoyer par email: [☑ Oui] [☐ Non]                    │ │
│ │ Inclure les détails: [☑ Oui] [☐ Non]                  │ │
│ │ Inclure les graphiques: [☑ Oui] [☐ Non]               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Générer le Récapitulatif]                       │
└─────────────────────────────────────────────────────────────┘
```

### 📋 Types de Rapports

#### 📊 Récapitulatif Général
- **Contenu** : Vue d'ensemble des revenus
- **Données** : Tous les bailleurs et propriétés
- **Format** : PDF professionnel
- **Fréquence** : Mensuelle

#### 👥 Récapitulatif par Bailleur
- **Contenu** : Revenus par bailleur
- **Données** : Propriétés et paiements du bailleur
- **Format** : PDF personnalisé
- **Fréquence** : Mensuelle

#### 🏠 Récapitulatif par Propriété
- **Contenu** : Revenus par propriété
- **Données** : Contrats et paiements de la propriété
- **Format** : PDF détaillé
- **Fréquence** : Mensuelle

#### 💰 Rapport de Trésorerie
- **Contenu** : Flux de trésorerie
- **Données** : Entrées et sorties d'argent
- **Format** : PDF avec graphiques
- **Fréquence** : Mensuelle

### 📄 Exemple de Récapitulatif PDF

#### En-tête
```
┌─────────────────────────────────────────────────────────────┐
│                    KBIS IMMOBILIER                         │
│              Récapitulatif Mensuel                         │
│                    Janvier 2024                            │
│                                                             │
│ Date de génération : 01/02/2024                            │
│ Période : 01/01/2024 au 31/01/2024                        │
└─────────────────────────────────────────────────────────────┘
```

#### Résumé Financier
```
┌─────────────────────────────────────────────────────────────┐
│                    RÉSUMÉ FINANCIER                        │
├─────────────────────────────────────────────────────────────┤
│ Total des loyers bruts     : 2,450,000 F CFA              │
│ Total des charges          : 245,000 F CFA                 │
│ Total des revenus nets     : 2,205,000 F CFA              │
│ Frais d'agence             : 122,500 F CFA                 │
│ Revenus nets après frais   : 2,082,500 F CFA              │
└─────────────────────────────────────────────────────────────┘
```

#### Détail par Bailleur
```
┌─────────────────────────────────────────────────────────────┐
│                    DÉTAIL PAR BAILLEUR                     │
├─────────────────────────────────────────────────────────────┤
│ Jean Dupont                                                │
│ ├─ Appartement T3 - Ouagadougou : 150,000 F CFA          │
│ ├─ Maison Villa - Bobo-Dioulasso : 300,000 F CFA         │
│ └─ Total : 450,000 F CFA                                  │
│                                                             │
│ Marie Traoré                                               │
│ ├─ Studio Moderne - Ouagadougou : 80,000 F CFA           │
│ └─ Total : 80,000 F CFA                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏢 Gestion des Unités Locatives - Guide Avancé

### 🏢 Pour les Grandes Propriétés

#### Types d'Unités Supportées
- **Appartements** : Logements complets
- **Studios** : Logements d'une pièce
- **Bureaux** : Espaces professionnels
- **Locaux commerciaux** : Espaces commerciaux
- **Chambres meublées** : Chambres individuelles
- **Places de parking** : Espaces de stationnement
- **Caves/Débarras** : Espaces de stockage

#### Ajouter une Unité Locative
1. Sélectionnez la **propriété parente**
2. Cliquez sur **"Gérer les unités"**
3. Cliquez sur **"Ajouter une unité"**

#### Formulaire d'Unité
```
┌─────────────────────────────────────────────────────────────┐
│ ➕ Ajouter une Unité Locative                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Identification                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Numéro d'unité *: [A1]                                 │ │
│ │ Nom descriptif: [Appartement A1]                       │ │
│ │ Type d'unité *: [Appartement ▼]                        │ │
│ │ Étage: [1]                                             │ │
│ │ Position: [Nord]                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Caractéristiques                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Surface (m²) *: [65]                                   │ │
│ │ Nombre de pièces: [3]                                  │ │
│ │ Nombre de chambres: [2]                                │ │
│ │ Nombre de salles de bain: [1]                          │ │
│ │ Balcon: [☑ Oui] [☐ Non]                               │ │
│ │ Parking: [☑ Oui] [☐ Non]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Informations Financières                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Loyer mensuel *: [120,000] F CFA                       │ │
│ │ Charges mensuelles: [12,000] F CFA                     │ │
│ │ Caution: [240,000] F CFA                               │ │
│ │ Frais d'agence: [60,000] F CFA                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ État et Disponibilité                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ État: [Disponible ▼]                                   │ │
│ │ Statut: [Libre ▼]                                       │ │
│ │ Notes: [Unité rénovée récemment]                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Enregistrer]                                     │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Tableau de Bord des Unités

#### Vue d'Ensemble
```
┌─────────────────────────────────────────────────────────────┐
│ 🏢 Gestion des Unités - Immeuble ABC                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ 📊 Statistiques │ │ 💰 Revenus      │ │ 🏠 Occupation   │ │
│ │ Total: 24 unités│ │ Mensuel: 2.4M   │ │ Taux: 87.5%    │ │
│ │ Occupées: 21    │ │ Potentiel: 2.8M │ │ Libres: 3      │ │
│ │ Libres: 3       │ │ Différence: 400K│ │ En rénovation: 0│ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🏢 Répartition par Étage                                │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ RDC: [A1] [A2] [A3] [A4] [A5] [A6]                │ │ │
│ │ │ 1er: [B1] [B2] [B3] [B4] [B5] [B6]                │ │ │
│ │ │ 2ème:[C1] [C2] [C3] [C4] [C5] [C6]                │ │ │
│ │ │ 3ème:[D1] [D2] [D3] [D4] [D5] [D6]                │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Légende des Statuts
- **🟢 Vert** : Occupée
- **🔴 Rouge** : Libre
- **🟡 Jaune** : En rénovation
- **🔵 Bleu** : Réservée
- **⚫ Gris** : Indisponible

---

## 🔔 Système de Notifications - Configuration

### 📱 Types de Notifications

#### 💰 Paiements
- **Paiement enregistré** : Nouveau paiement
- **Paiement validé** : Paiement confirmé
- **Paiement refusé** : Paiement rejeté
- **Paiement en retard** : Retard de paiement

#### 📄 Contrats
- **Contrat créé** : Nouveau contrat
- **Contrat expirant** : Contrat bientôt expiré
- **Contrat résilié** : Contrat terminé
- **Contrat renouvelé** : Contrat prolongé

#### 🏠 Propriétés
- **Propriété ajoutée** : Nouvelle propriété
- **Propriété modifiée** : Propriété mise à jour
- **Propriété supprimée** : Propriété supprimée

#### 👥 Utilisateurs
- **Nouvel utilisateur** : Utilisateur créé
- **Connexion** : Connexion utilisateur
- **Déconnexion** : Déconnexion utilisateur

### ⚙️ Configuration des Notifications

#### Paramètres Personnels
1. Cliquez sur votre **nom** en haut à droite
2. Cliquez sur **"Paramètres"**
3. Cliquez sur **"Notifications"**

#### Interface de Configuration
```
┌─────────────────────────────────────────────────────────────┐
│ 🔔 Configuration des Notifications                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Notifications par Email                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Paiements: [☑ Oui] [☐ Non]                            │ │
│ │ Contrats: [☑ Oui] [☐ Non]                             │ │
│ │ Propriétés: [☐ Oui] [☑ Non]                           │ │
│ │ Utilisateurs: [☐ Oui] [☑ Non]                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Notifications dans l'Application                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Paiements: [☑ Oui] [☐ Non]                            │ │
│ │ Contrats: [☑ Oui] [☐ Non]                             │ │
│ │ Propriétés: [☑ Oui] [☐ Non]                           │ │
│ │ Utilisateurs: [☑ Oui] [☐ Non]                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Fréquence des Notifications                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Email: [Immédiat ▼]                                    │ │
│ │ Application: [Immédiat ▼]                              │ │
│ │ Résumé quotidien: [☑ Oui] [☐ Non]                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Annuler] [Enregistrer]                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Actions Rapides et Raccourcis

### 🎯 Actions Contextuelles

#### Pour un Bailleur
- **Modifier** : Modifier les informations
- **Ajouter propriété** : Créer une nouvelle propriété
- **Voir propriétés** : Afficher ses propriétés
- **Générer rapport** : Créer un rapport personnalisé
- **Envoyer message** : Contacter le bailleur

#### Pour une Propriété
- **Modifier** : Modifier les informations
- **Créer contrat** : Nouveau contrat de location
- **Voir contrats** : Afficher les contrats
- **Gérer unités** : Gérer les unités locatives
- **Ajouter photo** : Ajouter des photos

#### Pour un Locataire
- **Modifier** : Modifier les informations
- **Créer contrat** : Nouveau contrat de location
- **Voir paiements** : Afficher l'historique
- **Envoyer message** : Contacter le locataire
- **Voir garant** : Informations du garant

#### Pour un Contrat
- **Modifier** : Modifier les conditions
- **Résilier** : Terminer le contrat
- **Renouveler** : Prolonger le contrat
- **Voir paiements** : Afficher les paiements
- **Générer reçu** : Créer un reçu

### ⌨️ Raccourcis Clavier

#### Navigation
- **Ctrl + H** : Accueil (Tableau de bord)
- **Ctrl + P** : Propriétés
- **Ctrl + B** : Bailleurs
- **Ctrl + L** : Locataires
- **Ctrl + C** : Contrats
- **Ctrl + $** : Paiements
- **Ctrl + R** : Rapports

#### Actions
- **Ctrl + N** : Nouvel élément
- **Ctrl + S** : Sauvegarder
- **Ctrl + F** : Rechercher
- **Ctrl + P** : Imprimer
- **Ctrl + E** : Exporter
- **Ctrl + Z** : Annuler
- **Ctrl + Y** : Rétablir

#### Interface
- **F5** : Actualiser la page
- **Ctrl + +** : Zoom avant
- **Ctrl + -** : Zoom arrière
- **Ctrl + 0** : Zoom normal
- **F11** : Plein écran
- **Échap** : Fermer les modales

---

## ❓ FAQ Détaillée et Dépannage

### 🔧 Problèmes Techniques

#### Erreur de Connexion
**Symptôme** : Impossible de se connecter à l'application
**Causes possibles** :
- Problème de connexion internet
- Serveur indisponible
- Identifiants incorrects

**Solutions** :
1. Vérifiez votre connexion internet
2. Vérifiez l'URL : `https://78.138.58.185`
3. Vérifiez vos identifiants
4. Contactez l'administrateur

#### Page qui ne se charge pas
**Symptôme** : Page blanche ou erreur de chargement
**Causes possibles** :
- Problème de connexion
- Cache du navigateur
- Problème serveur

**Solutions** :
1. Actualisez la page (F5)
2. Videz le cache du navigateur
3. Vérifiez votre connexion
4. Contactez le support technique

#### Données qui ne s'enregistrent pas
**Symptôme** : Les modifications ne sont pas sauvegardées
**Causes possibles** :
- Champs obligatoires non remplis
- Problème de connexion
- Erreur de validation

**Solutions** :
1. Vérifiez les champs obligatoires (marqués avec *)
2. Vérifiez votre connexion internet
3. Vérifiez les formats de données
4. Contactez l'administrateur

### 💰 Problèmes de Paiements

#### Paiement non enregistré
**Symptôme** : Le paiement n'apparaît pas dans la liste
**Solutions** :
1. Vérifiez que tous les champs sont remplis
2. Vérifiez le montant saisi
3. Vérifiez la date de paiement
4. Contactez l'administrateur

#### Reçu non généré
**Symptôme** : Impossible de générer le reçu
**Solutions** :
1. Vérifiez que le paiement est validé
2. Vérifiez les informations du contrat
3. Contactez le support technique

### 📄 Problèmes de Contrats

#### Contrat non créé
**Symptôme** : Le contrat n'apparaît pas dans la liste
**Solutions** :
1. Vérifiez que toutes les parties sont sélectionnées
2. Vérifiez les dates de début et fin
3. Vérifiez les montants saisis
4. Contactez l'administrateur

#### Contrat non modifiable
**Symptôme** : Impossible de modifier le contrat
**Solutions** :
1. Vérifiez vos permissions
2. Vérifiez le statut du contrat
3. Contactez l'administrateur

### 🏠 Problèmes de Propriétés

#### Propriété non visible
**Symptôme** : La propriété n'apparaît pas dans la liste
**Solutions** :
1. Vérifiez les filtres appliqués
2. Vérifiez vos permissions
3. Contactez l'administrateur

#### Photos non uploadées
**Symptôme** : Les photos ne s'affichent pas
**Solutions** :
1. Vérifiez le format des images (JPG, PNG)
2. Vérifiez la taille des images (max 5MB)
3. Vérifiez votre connexion internet
4. Contactez le support technique

### 📊 Problèmes de Rapports

#### Rapport non généré
**Symptôme** : Impossible de générer le rapport
**Solutions** :
1. Vérifiez la période sélectionnée
2. Vérifiez les filtres appliqués
3. Vérifiez vos permissions
4. Contactez l'administrateur

#### Rapport incomplet
**Symptôme** : Le rapport ne contient pas toutes les données
**Solutions** :
1. Vérifiez les filtres appliqués
2. Vérifiez la période sélectionnée
3. Vérifiez les permissions
4. Contactez l'administrateur

---

## 🎓 Formation et Support

### 📚 Formation Utilisateur

#### Formation Initiale (2 heures)
**Objectif** : Maîtriser les fonctionnalités de base
**Contenu** :
- Connexion et navigation
- Gestion des propriétés
- Gestion des bailleurs et locataires
- Enregistrement des paiements
- Génération de rapports

#### Formation Avancée (4 heures)
**Objectif** : Maîtriser les fonctionnalités avancées
**Contenu** :
- Gestion des unités locatives
- Configuration des notifications
- Utilisation des actions rapides
- Optimisation des workflows
- Résolution des problèmes courants

#### Formation en Ligne
**Vidéos disponibles** :
- Tutoriel de connexion
- Gestion des propriétés
- Enregistrement des paiements
- Génération de rapports
- Utilisation des filtres

### 🆘 Support Technique

#### Contact Support
- **Email** : support@kbis-immobilier.com
- **Téléphone** : +226 XX XX XX XX
- **Heures d'ouverture** : 8h00 - 18h00 (Lun-Ven)
- **Urgences** : 24h/24 (problèmes critiques)

#### Niveaux de Support
- **Niveau 1** : Problèmes de connexion et navigation
- **Niveau 2** : Problèmes de fonctionnalités
- **Niveau 3** : Problèmes techniques avancés
- **Niveau 4** : Problèmes de configuration système

#### Temps de Réponse
- **Urgent** : 2 heures
- **Important** : 4 heures
- **Normal** : 24 heures
- **Faible** : 72 heures

### 📖 Documentation Technique

#### Guides Administrateur
- Configuration du système
- Gestion des utilisateurs
- Sauvegarde et restauration
- Maintenance et mises à jour

#### API Documentation
- Endpoints disponibles
- Authentification
- Formats de données
- Exemples d'utilisation

#### Changelog
- Historique des versions
- Nouvelles fonctionnalités
- Corrections de bugs
- Améliorations de performance

---

## 🎯 Conseils d'Utilisation Avancés

### 💡 Optimisation des Workflows

#### Organisation des Données
1. **Utilisez des noms cohérents** pour les propriétés
2. **Groupez les propriétés** par quartier ou type
3. **Mettez à jour régulièrement** les informations
4. **Archivez les anciens contrats** et paiements
5. **Utilisez les notes** pour des informations importantes

#### Efficacité Opérationnelle
1. **Configurez les notifications** selon vos besoins
2. **Utilisez les actions rapides** pour gagner du temps
3. **Générez des rapports** régulièrement
4. **Utilisez les filtres** pour trouver rapidement les informations
5. **Sauvegardez vos données** régulièrement

#### Bonnes Pratiques
1. **Vérifiez les informations** avant de les enregistrer
2. **Validez les paiements** rapidement
3. **Suivez les retards** de paiement
4. **Communiquez** avec les bailleurs et locataires
5. **Formez vos utilisateurs** régulièrement

### 🔒 Sécurité et Confidentialité

#### Protection des Données
- **Mots de passe forts** : Minimum 8 caractères
- **Connexions sécurisées** : HTTPS obligatoire
- **Sauvegardes régulières** : Quotidiennes
- **Accès contrôlé** : Permissions granulaires
- **Audit des actions** : Traçabilité complète

#### Bonnes Pratiques de Sécurité
1. **Ne partagez jamais** vos identifiants
2. **Déconnectez-vous** après utilisation
3. **Utilisez des mots de passe** différents
4. **Signalez les problèmes** de sécurité
5. **Mettez à jour** régulièrement

---

*Dernière mise à jour : Octobre 2025*  
*Version : 5.0*  
*© KBIS Immobilier - Tous droits réservés*
