# DIAGRAMME DE CLASSES - KBIS IMMOBILIER

## Structure des modèles

### UTILISATEURS

#### Utilisateur
**Description:** Utilisateurs du système

**Champs principaux:**
- `id` (AutoField) - ID principal
- `username` (CharField) - Nom d'utilisateur
- `email` (EmailField) - Adresse email
- `first_name` (CharField) - Prénom
- `last_name` (CharField) - Nom
- `telephone` (CharField) - Téléphone
- `groupe_travail` (ForeignKey) - Groupe de travail
- `poste` (CharField) - Poste
- `actif` (BooleanField) - Actif
- `is_deleted` (BooleanField) - Supprimé logiquement

#### GroupeTravail
**Description:** Groupes de travail

**Champs principaux:**
- `id` (AutoField) - ID principal
- `nom` (CharField) - Nom du groupe
- `description` (TextField) - Description
- `permissions` (JSONField) - Permissions
- `actif` (BooleanField) - Actif

---

### PROPRIETES

#### Propriete
**Description:** Propriétés immobilières

**Champs principaux:**
- `id` (AutoField) - ID principal
- `numero_propriete` (CharField) - Numéro propriété
- `adresse` (TextField) - Adresse
- `ville` (CharField) - Ville
- `type_bien` (ForeignKey) - Type de bien
- `bailleur` (ForeignKey) - Bailleur
- `loyer_mensuel` (CharField) - Loyer mensuel
- `charges_mensuelles` (CharField) - Charges mensuelles
- `is_deleted` (BooleanField) - Supprimé logiquement

#### Bailleur
**Description:** Bailleurs

**Champs principaux:**
- `id` (AutoField) - ID principal
- `numero_bailleur` (CharField) - Numéro bailleur
- `civilite` (CharField) - Civilité
- `nom` (CharField) - Nom
- `prenom` (CharField) - Prénom
- `email` (EmailField) - Email
- `telephone` (CharField) - Téléphone
- `iban` (CharField) - IBAN
- `is_deleted` (BooleanField) - Supprimé logiquement

#### Locataire
**Description:** Locataires

**Champs principaux:**
- `id` (AutoField) - ID principal
- `numero_locataire` (CharField) - Numéro locataire
- `civilite` (CharField) - Civilité
- `nom` (CharField) - Nom
- `prenom` (CharField) - Prénom
- `email` (EmailField) - Email
- `telephone` (CharField) - Téléphone
- `is_deleted` (BooleanField) - Supprimé logiquement

#### TypeBien
**Description:** Types de biens immobiliers

**Champs principaux:**
- `id` (AutoField) - ID principal
- `nom` (CharField) - Nom
- `description` (TextField) - Description

---

### CONTRATS

#### Contrat
**Description:** Contrats de location

**Champs principaux:**
- `id` (AutoField) - ID principal
- `numero_contrat` (CharField) - Numéro contrat
- `propriete` (ForeignKey) - Propriété
- `locataire` (ForeignKey) - Locataire
- `date_debut` (DateField) - Date début
- `date_fin` (DateField) - Date fin
- `loyer_mensuel` (CharField) - Loyer mensuel
- `charges_mensuelles` (CharField) - Charges mensuelles
- `depot_garantie` (CharField) - Dépôt garantie
- `caution_payee` (BooleanField) - Caution payée

#### Quittance
**Description:** Quittances de loyer

**Champs principaux:**
- `id` (AutoField) - ID principal
- `contrat` (ForeignKey) - Contrat
- `numero_quittance` (CharField) - Numéro quittance
- `periode_debut` (DateField) - Période début
- `periode_fin` (DateField) - Période fin
- `montant_loyer` (CharField) - Montant loyer
- `montant_charges` (CharField) - Montant charges

---

### PAIEMENTS

#### Paiement
**Description:** Paiements

**Champs principaux:**
- `id` (AutoField) - ID principal
- `contrat` (ForeignKey) - Contrat
- `montant` (DecimalField) - Montant
- `date_paiement` (DateField) - Date paiement
- `mode_paiement` (CharField) - Mode paiement
- `statut` (CharField) - Statut
- `reference` (CharField) - Référence

#### Recu
**Description:** Reçus de paiement

**Champs principaux:**
- `id` (AutoField) - ID principal
- `paiement` (OneToOneField) - Paiement
- `numero_recu` (CharField) - Numéro reçu
- `date_emission` (DateField) - Date émission
- `montant` (DecimalField) - Montant

#### PlanPaiementPartiel
**Description:** Plans de paiement partiel

**Champs principaux:**
- `id` (AutoField) - ID principal
- `numero_plan` (CharField) - Numéro plan
- `nom_plan` (CharField) - Nom plan
- `contrat` (ForeignKey) - Contrat
- `montant_total` (DecimalField) - Montant total
- `montant_deja_paye` (DecimalField) - Montant déjà payé
- `statut` (CharField) - Statut

---

### CORE

#### NiveauAcces
**Description:** Niveaux d'accès aux données

**Champs principaux:**
- `id` (AutoField) - ID principal
- `nom` (CharField) - Nom niveau
- `niveau` (CharField) - Niveau accès
- `description` (TextField) - Description
- `priorite` (PositiveIntegerField) - Priorité

#### AuditLog
**Description:** Logs d'audit

**Champs principaux:**
- `id` (AutoField) - ID principal
- `utilisateur` (ForeignKey) - Utilisateur
- `action` (CharField) - Action
- `objet_type` (CharField) - Type objet
- `objet_id` (PositiveIntegerField) - ID objet
- `timestamp` (DateTimeField) - Timestamp

---

### NOTIFICATIONS

#### Notification
**Description:** Notifications système

**Champs principaux:**
- `id` (AutoField) - ID principal
- `utilisateur` (ForeignKey) - Utilisateur
- `titre` (CharField) - Titre
- `message` (TextField) - Message
- `type_notification` (CharField) - Type notification
- `lu` (BooleanField) - Lu
- `date_creation` (DateTimeField) - Date création

---

## Relations principales

### Relations 1:N (One-to-Many)
- **GroupeTravail** → **Utilisateur** (groupe_travail)
- **TypeBien** → **Propriete** (type_bien)
- **Bailleur** → **Propriete** (bailleur)
- **Propriete** → **Contrat** (propriete)
- **Locataire** → **Contrat** (locataire)
- **Contrat** → **Paiement** (contrat)
- **Contrat** → **Quittance** (contrat)
- **Contrat** → **PlanPaiementPartiel** (contrat)
- **Utilisateur** → **AuditLog** (utilisateur)
- **Utilisateur** → **Notification** (utilisateur)

### Relations 1:1 (One-to-One)
- **Paiement** → **Recu** (paiement)

### Relations N:N (Many-to-Many)
- **GroupeTravail** → **Group** (groupes_autorises)

---

## Contraintes et règles

### Clés primaires
- Tous les modèles ont un `id` AutoField comme clé primaire

### Clés étrangères
- Toutes les relations sont protégées (PROTECT) sauf indication contraire
- Les suppressions en cascade sont évitées pour préserver l'intégrité

### Contraintes d'unicité
- Numéros uniques pour tous les modèles principaux
- Emails uniques pour les utilisateurs
- Noms uniques pour les groupes

### Validation des données
- Montants financiers avec validation positive
- Dates cohérentes (début < fin)
- Champs obligatoires respectés

### Suppression logique
- Modèles sensibles utilisent `is_deleted` au lieu de suppression physique
- Permet la récupération et l'audit des données
