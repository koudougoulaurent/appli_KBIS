# 📊 SCHÉMA COMPLET DE LA BASE DE DONNÉES
## Application de Gestion Immobilière - GESTIMMOB

---

## 🏗️ **1. MODULE CORE (Configuration & Sécurité)**

### **ConfigurationEntreprise**
Configuration de l'entreprise et paramètres généraux
```sql
- id (Primary Key)
- nom_entreprise (CharField, max_length=200, default='GESTIMMOB')
- slogan (CharField, max_length=200, blank=True)
- adresse (CharField, max_length=200, default='123 Rue de la Paix')
- code_postal (CharField, max_length=10, default='75001')
- ville (CharField, max_length=100, default='Paris')
- pays (CharField, max_length=100, default='France')
- telephone (CharField, max_length=20, default='01 23 45 67 89')
- email (EmailField, default='contact@gestimmob.fr')
- site_web (URLField, blank=True)
- siret (CharField, max_length=20, default='123 456 789 00012')
- numero_licence (CharField, max_length=50, default='123456789')
- capital_social (CharField, max_length=100, blank=True)
- forme_juridique (CharField, max_length=100, default='SARL')
- logo_url (URLField, blank=True)
- logo_upload (ImageField, upload_to='logos_entreprise/')
- entete_upload (ImageField, upload_to='entetes_entreprise/')
- couleur_principale (CharField, max_length=7, default='#2c3e50')
- couleur_secondaire (CharField, max_length=7, default='#3498db')
- iban (CharField, max_length=34, blank=True)
- bic (CharField, max_length=11, blank=True)
- banque (CharField, max_length=100, blank=True)
- texte_contrat (TextField, blank=True)
- texte_resiliation (TextField, blank=True)
- actif (BooleanField, default=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **NiveauAcces**
Gestion des niveaux d'accès aux données
```sql
- id (Primary Key)
- nom (CharField, max_length=50, unique=True)
- niveau (CharField, max_length=20, choices=NIVEAUX_CHOICES, unique=True)
  * 'public' - Données générales
  * 'interne' - Données de l'équipe
  * 'confidentiel' - Données sensibles
  * 'secret' - Données critiques direction
  * 'top_secret' - Données stratégiques
- description (TextField)
- priorite (PositiveIntegerField, 1-10)
- groupes_autorises (ManyToMany vers Group)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
- actif (BooleanField, default=True)
```

### **PermissionTableauBord**
Permissions spécifiques aux tableaux de bord
```sql
- id (Primary Key)
- nom (CharField, max_length=100, unique=True)
- type_donnees (CharField, max_length=20, choices=TYPE_DONNEES_CHOICES)
  * 'financier' - Données financières
  * 'locataire' - Données locataires
  * 'bailleur' - Données bailleurs
  * 'propriete' - Données propriétés
  * 'contrat' - Données contrats
  * 'paiement' - Données paiements
  * 'charge' - Données charges
  * 'statistique' - Statistiques globales
  * 'rapport' - Rapports détaillés
- niveau_acces_requis (ForeignKey vers NiveauAcces)
- peut_voir_montants (BooleanField, default=False)
- peut_voir_details_personnels (BooleanField, default=False)
- peut_voir_historique (BooleanField, default=False)
- peut_exporter (BooleanField, default=False)
- peut_imprimer (BooleanField, default=False)
- limite_periode_jours (PositiveIntegerField, null=True)
- limite_nombre_resultats (PositiveIntegerField, null=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
- actif (BooleanField, default=True)
```

### **AuditLog**
Journalisation des actions utilisateur
```sql
- id (Primary Key)
- content_type (ForeignKey vers ContentType)
- object_id (PositiveIntegerField)
- content_object (GenericForeignKey)
- action (CharField, max_length=20, choices=ACTION_CHOICES)
  * 'create' - Création
  * 'update' - Modification
  * 'delete' - Suppression
  * 'view' - Consultation
  * 'export' - Export
  * 'import' - Import
  * 'login' - Connexion
  * 'logout' - Déconnexion
  * 'validation' - Validation
  * 'rejection' - Rejet
- user (ForeignKey vers Utilisateur)
- details (JSONField)
- object_repr (CharField, max_length=200)
- ip_address (GenericIPAddressField)
- user_agent (TextField)
- timestamp (DateTimeField, auto_now_add=True)
- description (TextField, blank=True)
```

### **Devise**
Gestion des devises
```sql
- id (Primary Key)
- code (CharField, max_length=3, unique=True) # ISO 4217
- nom (CharField, max_length=100)
- symbole (CharField, max_length=10)
- taux_change (DecimalField, max_digits=10, decimal_places=4, default=1.0)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
- actif (BooleanField, default=True)
- par_defaut (BooleanField, default=False)
```

---

## 👥 **2. MODULE UTILISATEURS**

### **GroupeTravail**
Groupes de travail des utilisateurs
```sql
- id (Primary Key)
- nom (CharField, max_length=100, unique=True)
- description (TextField, blank=True)
- actif (BooleanField, default=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Utilisateur** (étend AbstractUser)
Utilisateurs du système
```sql
- id (Primary Key)
- username (CharField, max_length=150, unique=True)
- email (EmailField, blank=True)
- first_name (CharField, max_length=150, blank=True)
- last_name (CharField, max_length=150, blank=True)
- is_staff (BooleanField, default=False)
- is_active (BooleanField, default=True)
- date_joined (DateTimeField, auto_now_add=True)
- telephone (CharField, max_length=100, blank=True)
- adresse (TextField, blank=True)
- date_naissance (DateField, null=True, blank=True)
- photo (ImageField, upload_to='photos_utilisateurs/', null=True, blank=True)
- groupe_travail (ForeignKey vers GroupeTravail, null=True, blank=True)
- poste (CharField, max_length=100, blank=True)
- departement (CharField, max_length=100, blank=True)
- date_embauche (DateField, null=True, blank=True)
- actif (BooleanField, default=True)
- derniere_connexion (DateTimeField, null=True, blank=True)
- date_creation (DateTimeField, default=timezone.now)
- date_modification (DateTimeField, auto_now=True)
- is_deleted (BooleanField, default=False)
- deleted_at (DateTimeField, null=True, blank=True)
- deleted_by (ForeignKey vers 'self', null=True, blank=True)
```

---

## 🏠 **3. MODULE PROPRIETES**

### **TypeBien**
Types de biens immobiliers
```sql
- id (Primary Key)
- nom (CharField, max_length=100, unique=True)
- description (TextField, blank=True)
- actif (BooleanField, default=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Bailleur**
Propriétaires des biens
```sql
- id (Primary Key)
- numero_bailleur (CharField, max_length=20, unique=True, default='BL0001')
- civilite (CharField, max_length=5, choices=CIVILITE_CHOICES, default='M')
  * 'M' - Monsieur
  * 'Mme' - Madame
  * 'Mlle' - Mademoiselle
- nom (CharField, max_length=100)
- prenom (CharField, max_length=100)
- date_naissance (DateField, blank=True, null=True)
- email (EmailField, blank=True, null=True)
- telephone (CharField, max_length=20)
- telephone_mobile (CharField, max_length=20, blank=True)
- adresse (TextField, blank=True, null=True)
- code_postal (CharField, max_length=10, blank=True, null=True)
- ville (CharField, max_length=100, blank=True, null=True)
- pays (CharField, max_length=100, blank=True, null=True)
- profession (CharField, max_length=100, blank=True)
- employeur (CharField, max_length=100, blank=True)
- revenus_mensuels (DecimalField, max_digits=12, decimal_places=2, blank=True, null=True)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='actif')
  * 'actif' - Actif
  * 'inactif' - Inactif
  * 'suspendu' - Suspendu
- is_deleted (BooleanField, default=False)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Locataire**
Locataires des biens
```sql
- id (Primary Key)
- numero_locataire (CharField, max_length=20, unique=True, default='LT0001')
- civilite (CharField, max_length=5, choices=CIVILITE_CHOICES, default='M')
- nom (CharField, max_length=100)
- prenom (CharField, max_length=100)
- date_naissance (DateField, blank=True, null=True)
- email (EmailField, blank=True, null=True)
- telephone (CharField, max_length=20)
- telephone_mobile (CharField, max_length=20, blank=True)
- adresse (TextField, blank=True, null=True)
- code_postal (CharField, max_length=10, blank=True, null=True)
- ville (CharField, max_length=100, blank=True, null=True)
- pays (CharField, max_length=100, blank=True, null=True)
- profession (CharField, max_length=100, blank=True)
- employeur (CharField, max_length=100, blank=True)
- revenus_mensuels (DecimalField, max_digits=12, decimal_places=2, blank=True, null=True)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='actif')
- is_deleted (BooleanField, default=False)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Propriete**
Propriétés immobilières
```sql
- id (Primary Key)
- numero_propriete (CharField, max_length=20, unique=True, default='PR0001')
- titre (CharField, max_length=200)
- description (TextField, blank=True)
- adresse (TextField, blank=True, null=True)
- code_postal (CharField, max_length=10, blank=True, null=True)
- ville (CharField, max_length=100, blank=True, null=True)
- pays (CharField, max_length=100, blank=True, null=True)
- type_bien (ForeignKey vers TypeBien)
- surface (DecimalField, max_digits=8, decimal_places=2, blank=True, null=True)
- nombre_pieces (PositiveIntegerField)
- nombre_chambres (PositiveIntegerField)
- nombre_salles_bain (PositiveIntegerField)
- ascenseur (BooleanField, default=False)
- parking (BooleanField, default=False)
- balcon (BooleanField, default=False)
- jardin (BooleanField, default=False)
- prix_achat (DecimalField, max_digits=12, decimal_places=2, blank=True, null=True)
- loyer_actuel (DecimalField, max_digits=10, decimal_places=2, default=0.00)
- charges_locataire (DecimalField, max_digits=10, decimal_places=2, default=0)
- etat (CharField, max_length=20, choices=ETAT_CHOICES, default='bon')
  * 'excellent' - Excellent
  * 'tres_bon' - Très bon
  * 'bon' - Bon
  * 'moyen' - Moyen
  * 'a_renover' - À rénover
- disponible (BooleanField, default=True)
- bailleur (ForeignKey vers Bailleur)
- notes (TextField, blank=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
- cree_par (ForeignKey vers Utilisateur)
- is_deleted (BooleanField, default=False)
```

### **UniteLocative**
Unités locatives dans les propriétés
```sql
- id (Primary Key)
- propriete (ForeignKey vers Propriete)
- nom (CharField, max_length=100)
- type_unite (CharField, max_length=50, choices=TYPE_UNITE_CHOICES, default='appartement')
  * 'appartement' - Appartement
  * 'studio' - Studio
  * 'chambre' - Chambre
  * 'bureau' - Bureau
  * 'commerce' - Commerce
  * 'autre' - Autre
- numero_etage (IntegerField, default=0)
- surface (DecimalField, max_digits=8, decimal_places=2, blank=True, null=True)
- nombre_pieces (PositiveIntegerField, default=1)
- nombre_chambres (PositiveIntegerField, default=0)
- nombre_salles_bain (PositiveIntegerField, default=0)
- meuble (BooleanField, default=False)
- balcon (BooleanField, default=False)
- parking_inclus (BooleanField, default=False)
- climatisation (BooleanField, default=False)
- internet_inclus (BooleanField, default=False)
- loyer_mensuel (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- charges_mensuelles (DecimalField, max_digits=10, decimal_places=2, default=0.00)
- caution_demandee (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='disponible')
  * 'disponible' - Disponible
  * 'occupe' - Occupé
  * 'maintenance' - En maintenance
  * 'reserve' - Réservé
- date_disponibilite (DateField, blank=True, null=True)
- description (TextField, blank=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Piece**
Pièces individuelles dans les propriétés
```sql
- id (Primary Key)
- propriete (ForeignKey vers Propriete)
- nom (CharField, max_length=100)
- type_piece (CharField, max_length=50, choices=TYPE_PIECE_CHOICES, default='chambre')
  * 'chambre' - Chambre
  * 'salon' - Salon
  * 'cuisine' - Cuisine
  * 'salle_bain' - Salle de bain
  * 'bureau' - Bureau
  * 'autre' - Autre
- surface (DecimalField, max_digits=8, decimal_places=2, blank=True, null=True)
- description (TextField, blank=True)
- equipements (TextField, blank=True)
- loyer_piece (DecimalField, max_digits=10, decimal_places=2, default=0.00)
- charges_piece (DecimalField, max_digits=10, decimal_places=2, default=0.00)
- disponible (BooleanField, default=True)
- actif (BooleanField, default=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

---

## 📋 **4. MODULE CONTRATS**

### **Contrat**
Contrats de location
```sql
- id (Primary Key)
- numero_contrat (CharField, max_length=50, unique=True)
- propriete (ForeignKey vers Propriete)
- locataire (ForeignKey vers Locataire)
- date_debut (DateField)
- date_fin (DateField, blank=True, null=True)
- date_signature (DateField)
- loyer_mensuel (CharField, max_length=20, default='0')
- charges_mensuelles (CharField, max_length=20, default='0')
- depot_garantie (CharField, max_length=20, default='0')
- avance_loyer (CharField, max_length=20, default='0')
- caution_payee (BooleanField, default=False)
- avance_loyer_payee (BooleanField, default=False)
- date_paiement_caution (DateField, null=True, blank=True)
- date_paiement_avance (DateField, null=True, blank=True)
- jour_paiement (PositiveIntegerField, default=1, validators=[1-31])
- mode_paiement (CharField, max_length=20, choices=MODE_PAIEMENT_CHOICES, default='virement')
  * 'virement' - Virement bancaire
  * 'cheque' - Chèque
  * 'especes' - Espèces
  * 'prelevement' - Prélèvement automatique
- est_actif (BooleanField, default=True)
- est_resilie (BooleanField, default=False)
- date_resiliation (DateField, null=True, blank=True)
- motif_resiliation (TextField, blank=True)
- unite_locative (ForeignKey vers UniteLocative, blank=True, null=True)
- pieces (ManyToMany vers Piece via PieceContrat)
- cree_par (ForeignKey vers Utilisateur)
- is_deleted (BooleanField, default=False)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **PieceContrat**
Relation entre pièces et contrats
```sql
- id (Primary Key)
- piece (ForeignKey vers Piece)
- contrat (ForeignKey vers Contrat)
- loyer_piece (DecimalField, max_digits=10, decimal_places=2)
- charges_piece (DecimalField, max_digits=10, decimal_places=2)
- date_debut_occupation (DateField)
- date_fin_occupation (DateField)
- actif (BooleanField, default=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Quittance**
Quittances de loyer
```sql
- id (Primary Key)
- contrat (ForeignKey vers Contrat)
- mois (DateField)
- montant_loyer (CharField, max_length=20)
- montant_charges (CharField, max_length=20, default='0')
- montant_total (CharField, max_length=20)
- numero_quittance (CharField, max_length=50, unique=True)
- date_creation (DateTimeField, auto_now_add=True)
- date_emission (DateTimeField, auto_now_add=True)
```

### **EtatLieux**
États des lieux
```sql
- id (Primary Key)
- contrat (ForeignKey vers Contrat)
- type_etat (CharField, max_length=10, choices=TYPE_CHOICES)
  * 'entree' - Entrée
  * 'sortie' - Sortie
- date_etat (DateField)
- observations_generales (TextField, blank=True)
- etat_murs (CharField, max_length=20, choices=ETAT_CHOICES, default='bon')
- etat_sol (CharField, max_length=20, choices=ETAT_CHOICES, default='bon')
- etat_plomberie (CharField, max_length=20, choices=ETAT_CHOICES, default='bon')
- etat_electricite (CharField, max_length=20, choices=ETAT_CHOICES, default='bon')
- cree_par (ForeignKey vers Utilisateur)
- date_creation (DateTimeField, auto_now_add=True)
- notes (TextField, blank=True)
```

### **RecuCaution**
Reçus de caution et avance
```sql
- id (Primary Key)
- contrat (OneToOneField vers Contrat)
- numero_recu (CharField, max_length=50, unique=True)
- date_emission (DateTimeField, auto_now_add=True)
- type_recu (CharField, max_length=20, choices=TYPE_RECU_CHOICES, default='complet')
  * 'caution' - Caution
  * 'avance' - Avance de loyer
  * 'complet' - Caution + Avance
- imprime (BooleanField, default=False)
- date_impression (DateTimeField, null=True, blank=True)
- imprime_par (ForeignKey vers Utilisateur)
- format_impression (CharField, max_length=20, choices=FORMAT_CHOICES, default='a5')
  * 'a5' - A5
  * 'a4' - A4
- notes_internes (TextField, blank=True)
```

### **DocumentContrat**
Documents PDF des contrats
```sql
- id (Primary Key)
- contrat (OneToOneField vers Contrat)
- numero_document (CharField, max_length=50, unique=True)
- date_creation (DateTimeField, auto_now_add=True)
- type_document (CharField, max_length=25, choices=TYPE_DOCUMENT_CHOICES, default='contrat_complet')
  * 'contrat_complet' - Contrat complet
  * 'contrat_simplifie' - Contrat simplifié
  * 'contrat_professionnel' - Contrat professionnel
- imprime (BooleanField, default=False)
- date_impression (DateTimeField, null=True, blank=True)
- imprime_par (ForeignKey vers Utilisateur)
- format_impression (CharField, max_length=20, choices=FORMAT_CHOICES, default='a4')
  * 'a4' - A4
  * 'a3' - A3
- version_template (CharField, max_length=10, default='1.0')
- notes_internes (TextField, blank=True)
```

### **ResiliationContrat**
Résiliations de contrats
```sql
- id (Primary Key)
- contrat (OneToOneField vers Contrat)
- date_resiliation (DateField)
- motif_resiliation (TextField)
- type_resiliation (CharField, max_length=20, choices=TYPE_RESILIATION_CHOICES)
  * 'locataire' - Résiliation par le locataire
  * 'bailleur' - Résiliation par le bailleur
  * 'accord_mutuel' - Résiliation d'accord mutuel
  * 'expiration' - Expiration naturelle
  * 'judiciaire' - Résiliation judiciaire
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_cours')
  * 'en_cours' - En cours de traitement
  * 'validee' - Validée
  * 'annulee' - Annulée
  * 'supprimee' - Supprimée définitivement
- etat_lieux_sortie (TextField, blank=True)
- caution_remboursee (BooleanField, default=False)
- montant_remboursement (CharField, max_length=20, default='0')
- date_remboursement (DateField, null=True, blank=True)
- cree_par (ForeignKey vers Utilisateur)
- validee_par (ForeignKey vers Utilisateur)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
- notes (TextField, blank=True)
```

---

## 💰 **5. MODULE PAIEMENTS**

### **ChargeDeductible**
Charges déductibles
```sql
- id (Primary Key)
- nom (CharField, max_length=200)
- description (TextField, blank=True)
- montant (DecimalField, max_digits=12, decimal_places=2)
- type_charge (CharField, max_length=50, choices=TYPE_CHARGE_CHOICES)
  * 'maintenance' - Maintenance
  * 'reparation' - Réparation
  * 'assurance' - Assurance
  * 'impot' - Impôt
  * 'autre' - Autre
- periode (CharField, max_length=50)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_attente')
  * 'en_attente' - En attente
  * 'validee' - Validée
  * 'payee' - Payée
  * 'annulee' - Annulée
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **Paiement**
Paiements des locataires
```sql
- id (Primary Key)
- reference_paiement (CharField, max_length=50, unique=True)
- contrat (ForeignKey vers Contrat)
- type_paiement (CharField, max_length=50, choices=TYPE_PAIEMENT_CHOICES)
  * 'loyer' - Loyer
  * 'charges' - Charges
  * 'caution' - Caution
  * 'avance_loyer' - Avance de loyer
  * 'autre' - Autre
- mode_paiement (CharField, max_length=20, choices=MODE_PAIEMENT_CHOICES)
  * 'virement' - Virement bancaire
  * 'cheque' - Chèque
  * 'especes' - Espèces
  * 'prelevement' - Prélèvement automatique
- montant (DecimalField, max_digits=12, decimal_places=2)
- date_paiement (DateField)
- periode (CharField, max_length=50, blank=True)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_attente')
  * 'en_attente' - En attente
  * 'valide' - Validé
  * 'refuse' - Refusé
  * 'annule' - Annulé
- notes (TextField, blank=True)
- cree_par (ForeignKey vers Utilisateur)
- is_deleted (BooleanField, default=False)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **QuittancePaiement**
Quittances de paiement
```sql
- id (Primary Key)
- paiement (ForeignKey vers Paiement)
- numero_quittance (CharField, max_length=50, unique=True)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='generee')
  * 'generee' - Générée
  * 'imprimee' - Imprimée
  * 'envoyee' - Envoyée
- date_emission (DateTimeField, auto_now_add=True)
- date_impression (DateTimeField, null=True, blank=True)
- format_impression (CharField, max_length=20, choices=FORMAT_CHOICES, default='a5')
  * 'a5' - A5
  * 'a4' - A4
```

### **RetraitBailleur**
Retraits pour les bailleurs
```sql
- id (Primary Key)
- bailleur (ForeignKey vers Bailleur)
- montant_total (DecimalField, max_digits=12, decimal_places=2)
- periode_debut (DateField)
- periode_fin (DateField)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_attente')
  * 'en_attente' - En attente
  * 'valide' - Validé
  * 'paye' - Payé
  * 'annule' - Annulé
- date_creation (DateTimeField, auto_now_add=True)
- date_validation (DateTimeField, null=True, blank=True)
- valide_par (ForeignKey vers Utilisateur)
- notes (TextField, blank=True)
```

### **RetraitChargeDeductible**
Retraits des charges déductibles
```sql
- id (Primary Key)
- charge (ForeignKey vers ChargeDeductible)
- montant (DecimalField, max_digits=12, decimal_places=2)
- date_retrait (DateField)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_attente')
  * 'en_attente' - En attente
  * 'valide' - Validé
  * 'paye' - Payé
  * 'annule' - Annulé
- date_creation (DateTimeField, auto_now_add=True)
- notes (TextField, blank=True)
```

### **RecuRetrait**
Reçus de retrait
```sql
- id (Primary Key)
- retrait (ForeignKey vers RetraitBailleur)
- numero_recu (CharField, max_length=50, unique=True)
- type_recu (CharField, max_length=20, choices=TYPE_RECU_CHOICES, default='retrait_bailleur')
  * 'retrait_bailleur' - Retrait bailleur
  * 'retrait_charge' - Retrait charge
- imprime (BooleanField, default=False)
- date_impression (DateTimeField, null=True, blank=True)
- imprime_par (ForeignKey vers Utilisateur)
- format_impression (CharField, max_length=20, choices=FORMAT_CHOICES, default='a5')
- notes_internes (TextField, blank=True)
```

### **TableauBordFinancier**
Tableau de bord financier
```sql
- id (Primary Key)
- periode (CharField, max_length=50)
- total_loyers (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- total_charges (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- total_retraits (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- benefice_net (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- date_creation (DateTimeField, auto_now_add=True)
- date_modification (DateTimeField, auto_now=True)
```

### **RecapMensuel**
Récapitulatifs mensuels
```sql
- id (Primary Key)
- mois (PositiveIntegerField, choices=MOIS_CHOICES)
- annee (PositiveIntegerField)
- total_loyers_percus (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- total_charges_deductibles (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- total_retraits_bailleurs (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- benefice_net (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_attente')
  * 'en_attente' - En attente
  * 'valide' - Validé
  * 'finalise' - Finalisé
- date_creation (DateTimeField, auto_now_add=True)
- date_validation (DateTimeField, null=True, blank=True)
- valide_par (ForeignKey vers Utilisateur)
```

### **RecapitulatifMensuelBailleur**
Récapitulatifs mensuels par bailleur
```sql
- id (Primary Key)
- recap_mensuel (ForeignKey vers RecapMensuel)
- bailleur (ForeignKey vers Bailleur)
- total_loyers (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- total_charges (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- montant_net (DecimalField, max_digits=12, decimal_places=2, default=0.00)
- statut (CharField, max_length=20, choices=STATUT_CHOICES, default='en_attente')
  * 'en_attente' - En attente
  * 'valide' - Validé
  * 'paye' - Payé
- date_creation (DateTimeField, auto_now_add=True)
- date_validation (DateTimeField, null=True, blank=True)
- valide_par (ForeignKey vers Utilisateur)
```

---

## 🔔 **6. MODULE NOTIFICATIONS**

### **Notification**
Notifications système
```sql
- id (Primary Key)
- type (CharField, max_length=50, choices=TYPE_CHOICES, default='info')
  * 'payment_due' - Échéance de paiement
  * 'payment_received' - Paiement reçu
  * 'payment_overdue' - Paiement en retard
  * 'contract_expiring' - Contrat expirant
  * 'maintenance_request' - Demande de maintenance
  * 'maintenance_completed' - Maintenance terminée
  * 'system_alert' - Alerte système
  * 'info' - Information générale
- title (CharField, max_length=200)
- message (TextField)
- priority (CharField, max_length=20, choices=PRIORITY_CHOICES, default='medium')
  * 'low' - Faible
  * 'medium' - Moyenne
  * 'high' - Élevée
  * 'urgent' - Urgente
- recipient (ForeignKey vers Utilisateur)
- content_type (ForeignKey vers ContentType, null=True, blank=True)
- object_id (PositiveIntegerField, null=True, blank=True)
- content_object (GenericForeignKey)
- is_read (BooleanField, default=False)
- is_sent_email (BooleanField, default=False)
- is_sent_sms (BooleanField, default=False)
- created_at (DateTimeField, auto_now_add=True)
- read_at (DateTimeField, null=True, blank=True)
```

### **NotificationPreference**
Préférences de notification par utilisateur
```sql
- id (Primary Key)
- user (OneToOneField vers Utilisateur)
- email_notifications (BooleanField, default=True)
- browser_notifications (BooleanField, default=True)
- sms_notifications (BooleanField, default=False)
- payment_due_email (BooleanField, default=True)
- payment_received_email (BooleanField, default=True)
- payment_overdue_email (BooleanField, default=True)
- contract_expiring_email (BooleanField, default=True)
- maintenance_email (BooleanField, default=True)
- system_alerts_email (BooleanField, default=True)
- payment_due_sms (BooleanField, default=False)
- payment_received_sms (BooleanField, default=False)
- payment_overdue_sms (BooleanField, default=True)
- contract_expiring_sms (BooleanField, default=False)
- maintenance_sms (BooleanField, default=False)
- system_alerts_sms (BooleanField, default=False)
- daily_digest (BooleanField, default=False)
- weekly_digest (BooleanField, default=False)
- phone_number (CharField, max_length=20, blank=True, null=True)
- sms_provider (CharField, max_length=50, default='twilio')
  * 'twilio' - Twilio
  * 'nexmo' - Nexmo/Vonage
  * 'custom' - Fournisseur personnalisé
- created_at (DateTimeField, auto_now_add=True)
- updated_at (DateTimeField, auto_now=True)
```

### **SMSNotification**
Notifications SMS
```sql
- id (Primary Key)
- notification (ForeignKey vers Notification, null=True, blank=True)
- user (ForeignKey vers Utilisateur, null=True, blank=True)
- phone_number (CharField, max_length=20)
- message (TextField)
- status (CharField, max_length=20, choices=STATUS_CHOICES, default='pending')
  * 'pending' - En attente
  * 'sent' - Envoyé
  * 'delivered' - Livré
  * 'failed' - Échec
  * 'cancelled' - Annulé
- provider (CharField, max_length=50, default='twilio')
- provider_message_id (CharField, max_length=100, blank=True, null=True)
- provider_response (TextField, blank=True, null=True)
- attempts (PositiveIntegerField, default=0)
- max_attempts (PositiveIntegerField, default=3)
- created_at (DateTimeField, auto_now_add=True)
- sent_at (DateTimeField, null=True, blank=True)
- delivered_at (DateTimeField, null=True, blank=True)
```

---

## 🔗 **7. RELATIONS PRINCIPALES**

### **Relations One-to-Many (1:N)**
```
Bailleur (1) ←→ (N) Propriete
Propriete (1) ←→ (N) UniteLocative
Propriete (1) ←→ (N) Piece
Propriete (1) ←→ (N) Contrat
Locataire (1) ←→ (N) Contrat
Contrat (1) ←→ (N) Paiement
Contrat (1) ←→ (N) Quittance
Contrat (1) ←→ (N) EtatLieux
Bailleur (1) ←→ (N) RetraitBailleur
Utilisateur (1) ←→ (N) Notification
Utilisateur (1) ←→ (N) SMSNotification
RecapMensuel (1) ←→ (N) RecapitulatifMensuelBailleur
```

### **Relations One-to-One (1:1)**
```
Contrat (1) ←→ (1) RecuCaution
Contrat (1) ←→ (1) DocumentContrat
Contrat (1) ←→ (1) ResiliationContrat
Utilisateur (1) ←→ (1) NotificationPreference
```

### **Relations Many-to-Many (N:N)**
```
Contrat (N) ←→ (N) Piece (via PieceContrat)
Group (N) ←→ (N) NiveauAcces
```

### **Relations Generic Foreign Key**
```
Notification → ContentObject (Contrat, Paiement, etc.)
AuditLog → ContentObject (n'importe quel modèle)
```

---

## 📈 **8. STATISTIQUES DU SCHÉMA**

- **Total des modèles** : 25 modèles principaux
- **Relations ForeignKey** : 40+ relations
- **Relations ManyToMany** : 5 relations
- **Relations OneToOne** : 4 relations
- **Relations GenericForeignKey** : 2 relations
- **Champs JSON** : 3 (pour la flexibilité)
- **Suppression logique** : Implémentée sur 8 modèles principaux
- **Audit complet** : Via AuditLog et LogAccesDonnees
- **Indexes** : Optimisés pour les requêtes fréquentes
- **Contraintes d'unicité** : 15+ contraintes
- **Choices fields** : 20+ champs avec choix prédéfinis

---

## 🛡️ **9. SÉCURITÉ ET AUDIT**

### **Système de permissions**
- Niveaux d'accès (public, interne, confidentiel, secret, top_secret)
- Permissions granulaires par type de données
- Contrôle d'accès aux montants et détails personnels
- Limitations de période et nombre de résultats

### **Audit et traçabilité**
- Journalisation complète des actions (AuditLog)
- Traçabilité des accès aux données sensibles (LogAccesDonnees)
- Horodatage de toutes les modifications
- Identification des utilisateurs responsables

### **Suppression logique**
- Implémentée sur les modèles principaux
- Préservation de l'intégrité référentielle
- Possibilité de restauration
- Traçabilité des suppressions

---

## 📋 **10. MÉTADONNÉES COMMUNES**

Tous les modèles principaux incluent :
- `date_creation` (DateTimeField, auto_now_add=True)
- `date_modification` (DateTimeField, auto_now=True)
- `is_deleted` (BooleanField, default=False) - pour la suppression logique
- `deleted_at` (DateTimeField, null=True, blank=True)
- `deleted_by` (ForeignKey vers Utilisateur, null=True, blank=True)

---

*Document généré le : {{ date_actuelle }}*
*Version de l'application : 1.0*
*Base de données : SQLite/PostgreSQL/MySQL compatible*
