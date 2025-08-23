# 💰 SYSTÈME DE CHARGES DÉDUCTIBLES - GUIDE COMPLET

**Date de mise en place :** 6 août 2025  
**Version :** 1.0  
**Statut :** ✅ Opérationnel

---

## 🎯 OBJECTIF

Permettre aux locataires d'avancer des frais qui devraient normalement être payés par le bailleur (réparations, travaux, etc.) et de les déduire automatiquement du montant du loyer lors du paiement suivant.

---

## 🏗️ ARCHITECTURE DU SYSTÈME

### 📋 Nouveau Modèle : `ChargeDeductible`

```python
class ChargeDeductible(models.Model):
    # Informations de base
    contrat = models.ForeignKey(Contrat)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    libelle = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Type et statut
    type_charge = models.CharField(choices=[
        ('reparation', 'Réparation'),
        ('travaux', 'Travaux'),
        ('entretien', 'Entretien'),
        ('urgence', 'Urgence'),
        ('fourniture', 'Fourniture'),
        ('service', 'Service'),
        ('autre', 'Autre'),
    ])
    
    statut = models.CharField(choices=[
        ('en_attente', 'En attente de validation'),
        ('validee', 'Validée'),
        ('deduite', 'Déduite du loyer'),
        ('refusee', 'Refusée'),
        ('annulee', 'Annulée'),
    ])
    
    # Dates importantes
    date_charge = models.DateField()
    date_validation = models.DateTimeField(null=True, blank=True)
    date_deduction = models.DateTimeField(null=True, blank=True)
    
    # Justificatifs
    fournisseur = models.CharField(max_length=150, blank=True)
    facture_numero = models.CharField(max_length=100, blank=True)
    justificatif_url = models.URLField(blank=True)
```

### 🔄 Modèle `Paiement` Étendu

```python
class Paiement(models.Model):
    # ... champs existants ...
    
    # NOUVEAUX CHAMPS
    montant_charges_deduites = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    montant_net_paye = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    # NOUVELLES MÉTHODES
    def calculer_montant_net(self):
        return self.montant - self.montant_charges_deduites
    
    def ajouter_charges_deductibles(self, charges_ids, utilisateur=None):
        # Logique de déduction des charges
```

---

## 🔄 WORKFLOW COMPLET

### 1️⃣ **Création d'une Charge**
```
Locataire avance des frais → Saisie dans le système
↓
Statut: "En attente de validation"
```

### 2️⃣ **Validation de la Charge**
```
Agent/Gestionnaire vérifie → Validation ou Refus
↓
Statut: "Validée" ou "Refusée"
```

### 3️⃣ **Déduction lors du Paiement**
```
Création du paiement → Sélection des charges validées
↓
Déduction automatique → Calcul du montant net
↓
Statut des charges: "Déduite du loyer"
```

### 4️⃣ **Génération du Reçu**
```
Reçu avec détail des charges → Montant net affiché
↓
Traçabilité complète pour bailleur et locataire
```

---

## 🌐 INTERFACES UTILISATEUR

### 📋 **Gestion des Charges**
- **Liste des charges :** `/paiements/charges-deductibles/`
- **Ajouter une charge :** `/paiements/charges-deductibles/ajouter/`
- **Détail d'une charge :** `/paiements/charges-deductibles/detail/{id}/`
- **Valider une charge :** `/paiements/charges-deductibles/valider/{id}/`
- **Refuser une charge :** `/paiements/charges-deductibles/refuser/{id}/`

### 💰 **Paiements avec Charges**
- **Paiement avec charges :** `/paiements/paiement-avec-charges/{contrat_id}/`
- **API charges par contrat :** `/paiements/api/charges-par-contrat/{contrat_id}/`

### 🏛️ **Administration Django**
- **Charges déductibles :** `/admin/paiements/chargedeductible/`
- **Paiements étendus :** `/admin/paiements/paiement/`

---

## 📋 FONCTIONNALITÉS CLÉS

### ✅ **Validation des Charges**
- Workflow d'approbation avec utilisateur validateur
- Possibilité de refuser avec motif
- Historique complet des actions

### 💰 **Calcul Automatique**
- Déduction automatique lors du paiement
- Vérification que les charges ne dépassent pas le loyer
- Calcul du montant net payé

### 🧾 **Reçus Détaillés**
- Affichage du montant brut du loyer
- Détail de chaque charge déduite
- Montant net final clairement indiqué
- Montant en lettres pour le montant net

### 📊 **Traçabilité Complète**
- Lien bidirectionnel charge ↔ paiement
- Dates de validation et déduction
- Utilisateur ayant effectué chaque action
- Logs d'audit intégrés

---

## 🎨 EXEMPLE D'UTILISATION

### Scénario : Réparation Plomberie

1. **Le locataire signale une fuite** et fait appel à un plombier en urgence
2. **Coût de la réparation :** 150 XOF (facture PL-2024-001)
3. **Saisie de la charge :**
   ```
   Libellé: "Réparation fuite robinet cuisine"
   Montant: 150.00 XOF
   Type: Réparation
   Fournisseur: "Plomberie Express"
   Facture: "PL-2024-001"
   ```

4. **Validation par le gestionnaire** → Statut: "Validée"

5. **Lors du paiement du loyer suivant :**
   ```
   Loyer mensuel: 800 XOF
   Charges déduites: -150 XOF
   Montant net à payer: 650 XOF
   ```

6. **Reçu généré automatiquement** avec détail des charges

7. **Le bailleur reçoit :** 650 XOF (au lieu de 800 XOF)

---

## 🔒 SÉCURITÉ ET CONTRÔLES

### ✅ **Validations**
- Montant des charges ne peut pas dépasser le loyer
- Seules les charges validées peuvent être déduites
- Vérification des permissions utilisateur

### 🔍 **Audit Trail**
- Chaque action est enregistrée avec utilisateur et timestamp
- Impossible de modifier une charge déjà déduite
- Historique complet consultable

### 🛡️ **Permissions**
- Création de charges : Utilisateurs connectés
- Validation : Gestionnaires/Administrateurs
- Consultation : Selon les permissions utilisateur

---

## 📈 STATISTIQUES ET RAPPORTS

### 📊 **Métriques Disponibles**
- Total des charges par statut
- Montant total des déductions par période
- Charges par type et par contrat
- Performance de validation (délais)

### 📋 **Filtres et Recherches**
- Par statut, type, contrat, période
- Recherche textuelle sur libellé et description
- Tri par date, montant, statut

---

## 🚀 AVANTAGES DU SYSTÈME

### 👥 **Pour les Locataires**
- ✅ Remboursement automatique des frais avancés
- ✅ Transparence totale sur les déductions
- ✅ Reçus détaillés pour justification

### 🏢 **Pour les Bailleurs**
- ✅ Visibilité sur tous les frais engagés
- ✅ Validation avant déduction
- ✅ Historique complet des interventions

### 🏛️ **Pour l'Agence**
- ✅ Gestion centralisée des charges
- ✅ Workflow de validation structuré
- ✅ Traçabilité complète des opérations

---

## 🔧 MAINTENANCE ET ÉVOLUTIONS

### 📅 **Tâches de Maintenance**
- Vérification périodique des charges en attente
- Nettoyage des charges anciennes refusées
- Sauvegarde des données de charges

### 🚀 **Évolutions Possibles**
- Upload de justificatifs (photos, PDF)
- Notifications automatiques aux bailleurs
- Intégration avec comptabilité
- Workflow d'approbation multi-niveaux

---

## 📞 SUPPORT ET FORMATION

### 🎓 **Formation Utilisateurs**
- Guide de saisie des charges
- Processus de validation
- Interprétation des reçus

### 🆘 **Support Technique**
- Documentation API disponible
- Logs détaillés pour débogage
- Interface d'administration complète

---

**✅ Le système de charges déductibles est maintenant pleinement opérationnel et intégré dans GESTIMMOB !**

*Dernière mise à jour : 6 août 2025*