# DOCUMENTATION COMPLÈTE - KBIS INTERNATIONAL

*Généré le 18/09/2025 à 11:30:00*

## 📋 Vue d'ensemble

Cette documentation présente la structure complète de la base de données de l'application KBIS INTERNATIONAL - Gestion Immobilière.

**Nombre de modèles:** 25+  
**Nombre de relations:** 50+  
**Applications:** 6 (utilisateurs, proprietes, contrats, paiements, core, notifications)

## 📱 UTILISATEURS

### Utilisateur (`Utilisateur`)
**Description:** Utilisateurs du système

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `username` | CharField | Nom d'utilisateur | ❌ | ✅ | ❌ |
| `email` | EmailField | Adresse email | ✅ | ❌ | ❌ |
| `first_name` | CharField | Prénom | ✅ | ❌ | ❌ |
| `last_name` | CharField | Nom | ✅ | ❌ | ❌ |
| `telephone` | CharField | Téléphone | ✅ | ❌ | ❌ |
| `adresse` | TextField | Adresse | ✅ | ❌ | ❌ |
| `groupe_travail` | ForeignKey | Groupe de travail | ✅ | ❌ | ❌ |
| `poste` | CharField | Poste | ✅ | ❌ | ❌ |
| `actif` | BooleanField | Actif | ❌ | ❌ | ❌ |
| `is_deleted` | BooleanField | Supprimé logiquement | ❌ | ❌ | ❌ |

### GroupeTravail (`GroupeTravail`)
**Description:** Groupes de travail

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `nom` | CharField | Nom du groupe | ❌ | ✅ | ❌ |
| `description` | TextField | Description | ✅ | ❌ | ❌ |
| `permissions` | JSONField | Permissions | ❌ | ❌ | ❌ |
| `actif` | BooleanField | Actif | ❌ | ❌ | ❌ |

---

## 📱 PROPRIETES

### Propriete (`Propriete`)
**Description:** Propriétés immobilières

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `numero_propriete` | CharField | Numéro propriété | ❌ | ✅ | ❌ |
| `adresse` | TextField | Adresse | ❌ | ❌ | ❌ |
| `ville` | CharField | Ville | ❌ | ❌ | ❌ |
| `code_postal` | CharField | Code postal | ✅ | ❌ | ❌ |
| `type_bien` | ForeignKey | Type de bien | ❌ | ❌ | ❌ |
| `bailleur` | ForeignKey | Bailleur | ❌ | ❌ | ❌ |
| `loyer_mensuel` | CharField | Loyer mensuel | ❌ | ❌ | ❌ |
| `charges_mensuelles` | CharField | Charges mensuelles | ❌ | ❌ | ❌ |
| `is_deleted` | BooleanField | Supprimé logiquement | ❌ | ❌ | ❌ |

### Bailleur (`Bailleur`)
**Description:** Bailleurs

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `numero_bailleur` | CharField | Numéro bailleur | ❌ | ✅ | ❌ |
| `civilite` | CharField | Civilité | ❌ | ❌ | ❌ |
| `nom` | CharField | Nom | ❌ | ❌ | ❌ |
| `prenom` | CharField | Prénom | ❌ | ❌ | ❌ |
| `email` | EmailField | Email | ✅ | ❌ | ❌ |
| `telephone` | CharField | Téléphone | ❌ | ❌ | ❌ |
| `adresse` | TextField | Adresse | ✅ | ❌ | ❌ |
| `iban` | CharField | IBAN | ✅ | ❌ | ❌ |
| `is_deleted` | BooleanField | Supprimé logiquement | ❌ | ❌ | ❌ |

### Locataire (`Locataire`)
**Description:** Locataires

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `numero_locataire` | CharField | Numéro locataire | ❌ | ✅ | ❌ |
| `civilite` | CharField | Civilité | ❌ | ❌ | ❌ |
| `nom` | CharField | Nom | ❌ | ❌ | ❌ |
| `prenom` | CharField | Prénom | ❌ | ❌ | ❌ |
| `email` | EmailField | Email | ✅ | ❌ | ❌ |
| `telephone` | CharField | Téléphone | ❌ | ❌ | ❌ |
| `adresse` | TextField | Adresse | ✅ | ❌ | ❌ |
| `is_deleted` | BooleanField | Supprimé logiquement | ❌ | ❌ | ❌ |

### TypeBien (`TypeBien`)
**Description:** Types de biens immobiliers

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `nom` | CharField | Nom | ❌ | ❌ | ❌ |
| `description` | TextField | Description | ✅ | ❌ | ❌ |

---

## 📱 CONTRATS

### Contrat (`Contrat`)
**Description:** Contrats de location

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `numero_contrat` | CharField | Numéro contrat | ❌ | ✅ | ❌ |
| `propriete` | ForeignKey | Propriété | ❌ | ❌ | ❌ |
| `locataire` | ForeignKey | Locataire | ❌ | ❌ | ❌ |
| `date_debut` | DateField | Date début | ❌ | ❌ | ❌ |
| `date_fin` | DateField | Date fin | ✅ | ❌ | ❌ |
| `loyer_mensuel` | CharField | Loyer mensuel | ❌ | ❌ | ❌ |
| `charges_mensuelles` | CharField | Charges mensuelles | ❌ | ❌ | ❌ |
| `depot_garantie` | CharField | Dépôt garantie | ❌ | ❌ | ❌ |
| `caution_payee` | BooleanField | Caution payée | ❌ | ❌ | ❌ |

### Quittance (`Quittance`)
**Description:** Quittances de loyer

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `contrat` | ForeignKey | Contrat | ❌ | ❌ | ❌ |
| `numero_quittance` | CharField | Numéro quittance | ❌ | ✅ | ❌ |
| `periode_debut` | DateField | Période début | ❌ | ❌ | ❌ |
| `periode_fin` | DateField | Période fin | ❌ | ❌ | ❌ |
| `montant_loyer` | CharField | Montant loyer | ❌ | ❌ | ❌ |
| `montant_charges` | CharField | Montant charges | ❌ | ❌ | ❌ |

---

## 📱 PAIEMENTS

### Paiement (`Paiement`)
**Description:** Paiements

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `contrat` | ForeignKey | Contrat | ❌ | ❌ | ❌ |
| `montant` | DecimalField | Montant | ❌ | ❌ | ❌ |
| `date_paiement` | DateField | Date paiement | ❌ | ❌ | ❌ |
| `mode_paiement` | CharField | Mode paiement | ❌ | ❌ | ❌ |
| `statut` | CharField | Statut | ❌ | ❌ | ❌ |
| `reference` | CharField | Référence | ✅ | ❌ | ❌ |

### Recu (`Recu`)
**Description:** Reçus de paiement

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `paiement` | OneToOneField | Paiement | ❌ | ❌ | ❌ |
| `numero_recu` | CharField | Numéro reçu | ❌ | ✅ | ❌ |
| `date_emission` | DateField | Date émission | ❌ | ❌ | ❌ |
| `montant` | DecimalField | Montant | ❌ | ❌ | ❌ |

### PlanPaiementPartiel (`PlanPaiementPartiel`)
**Description:** Plans de paiement partiel

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `numero_plan` | CharField | Numéro plan | ❌ | ✅ | ❌ |
| `nom_plan` | CharField | Nom plan | ❌ | ❌ | ❌ |
| `contrat` | ForeignKey | Contrat | ❌ | ❌ | ❌ |
| `montant_total` | DecimalField | Montant total | ❌ | ❌ | ❌ |
| `montant_deja_paye` | DecimalField | Montant déjà payé | ❌ | ❌ | ❌ |
| `statut` | CharField | Statut | ❌ | ❌ | ❌ |

---

## 📱 CORE

### NiveauAcces (`NiveauAcces`)
**Description:** Niveaux d'accès aux données

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `nom` | CharField | Nom niveau | ❌ | ✅ | ❌ |
| `niveau` | CharField | Niveau accès | ❌ | ✅ | ❌ |
| `description` | TextField | Description | ❌ | ❌ | ❌ |
| `priorite` | PositiveIntegerField | Priorité | ❌ | ❌ | ❌ |

### AuditLog (`AuditLog`)
**Description:** Logs d'audit

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `utilisateur` | ForeignKey | Utilisateur | ❌ | ❌ | ❌ |
| `action` | CharField | Action | ❌ | ❌ | ❌ |
| `objet_type` | CharField | Type objet | ❌ | ❌ | ❌ |
| `objet_id` | PositiveIntegerField | ID objet | ❌ | ❌ | ❌ |
| `timestamp` | DateTimeField | Timestamp | ❌ | ❌ | ❌ |

---

## 📱 NOTIFICATIONS

### Notification (`Notification`)
**Description:** Notifications système

| Nom | Type | Description | Null | Unique | PK |
|-----|------|-------------|------|--------|----|
| `id` | AutoField | ID principal | ❌ | ✅ | ✅ |
| `utilisateur` | ForeignKey | Utilisateur | ❌ | ❌ | ❌ |
| `titre` | CharField | Titre | ❌ | ❌ | ❌ |
| `message` | TextField | Message | ❌ | ❌ | ❌ |
| `type_notification` | CharField | Type notification | ❌ | ❌ | ❌ |
| `lu` | BooleanField | Lu | ❌ | ❌ | ❌ |
| `date_creation` | DateTimeField | Date création | ❌ | ❌ | ❌ |

---

## 🔗 Relations principales

- **Utilisateur** → **GroupeTravail** (ForeignKey)
- **Propriete** → **TypeBien** (ForeignKey)
- **Propriete** → **Bailleur** (ForeignKey)
- **Contrat** → **Propriete** (ForeignKey)
- **Contrat** → **Locataire** (ForeignKey)
- **Paiement** → **Contrat** (ForeignKey)
- **Recu** → **Paiement** (OneToOneField)
- **PlanPaiementPartiel** → **Contrat** (ForeignKey)
- **AuditLog** → **Utilisateur** (ForeignKey)
- **Notification** → **Utilisateur** (ForeignKey)

---

## ⚠️ Points d'attention

### Suppression logique
Les modèles suivants utilisent la suppression logique (`is_deleted`):
- Utilisateur
- Propriete
- Bailleur
- Locataire

### Relations critiques
- `Contrat` → `Propriete` (PROTECT)
- `Contrat` → `Locataire` (PROTECT)
- `Paiement` → `Contrat` (PROTECT)

### Contraintes importantes
- Numéros uniques pour tous les modèles principaux
- Clés étrangères protégées contre la suppression
- Validation des montants financiers
- Gestion des dates et périodes
