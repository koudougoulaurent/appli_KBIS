# 🗄️ DOCUMENTATION BASE DE DONNÉES - GESTIMMOB

## 📋 Vue d'ensemble

Cette documentation décrit la structure complète de la base de données de l'application GESTIMMOB, incluant les modèles, relations, et contraintes.

## 🏗️ Architecture générale

### Technologies utilisées
- **SGBD** : SQLite (développement) / PostgreSQL (production)
- **ORM** : Django ORM
- **Migrations** : Django Migrations
- **Contraintes** : Clés étrangères, index, validations

## 📊 Modèles principaux

### 1. Utilisateurs et Authentification

#### Utilisateur (utilisateurs/models.py)
```python
class Utilisateur(AbstractUser):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    est_actif = models.BooleanField(default=True)
    est_verifie = models.BooleanField(default=False)
```

**Relations :**
- `groups` → `Group` (Many-to-Many)
- `user_permissions` → `Permission` (Many-to-Many)

#### Group (Django Auth)
```python
class Group(models.Model):
    name = models.CharField(max_length=150, unique=True)
    permissions = models.ManyToManyField(Permission)
```

**Groupes utilisés :**
- `PRIVILEGE` : Accès complet au système
- `CAISSE` : Gestion des paiements
- `ADMINISTRATION` : Administration générale

### 2. Propriétés immobilières

#### Propriete (proprietes/models.py)
```python
class Propriete(models.Model):
    titre = models.CharField(max_length=200)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    type_propriete = models.CharField(max_length=50, choices=TYPE_CHOICES)
    surface = models.DecimalField(max_digits=8, decimal_places=2)
    nombre_pieces = models.IntegerField()
    loyer_mensuel = models.DecimalField(max_digits=10, decimal_places=2)
    charges_mensuelles = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bailleur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    est_active = models.BooleanField(default=True)
```

**Relations :**
- `bailleur` → `Utilisateur`
- `contrats` → `Contrat` (One-to-Many)

### 3. Contrats de location

#### Contrat (contrats/models.py)
```python
class Contrat(models.Model):
    propriete = models.ForeignKey(Propriete, on_delete=models.CASCADE)
    locataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    bailleur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='contrats_bailleur')
    date_debut = models.DateField()
    date_fin = models.DateField()
    loyer_mensuel = models.DecimalField(max_digits=10, decimal_places=2)
    charges_mensuelles = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    caution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    est_actif = models.BooleanField(default=True)
    est_resilie = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
```

**Relations :**
- `propriete` → `Propriete`
- `locataire` → `Utilisateur`
- `bailleur` → `Utilisateur`
- `paiements` → `Paiement` (One-to-Many)

### 4. Paiements et finances

#### Paiement (paiements/models.py)
```python
class Paiement(models.Model):
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    mode_paiement = models.CharField(max_length=50, choices=MODE_CHOICES)
    reference = models.CharField(max_length=100, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
```

**Relations :**
- `contrat` → `Contrat`

#### RecapMensuel (paiements/models.py)
```python
class RecapMensuel(models.Model):
    bailleur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    mois = models.IntegerField()
    annee = models.IntegerField()
    total_loyers = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paiements = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_net_a_payer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)
    est_supprime = models.BooleanField(default=False)
```

**Relations :**
- `bailleur` → `Utilisateur`

### 5. Notifications

#### Notification (notifications/models.py)
```python
class Notification(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notification = models.CharField(max_length=50, choices=TYPE_CHOICES)
    est_lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
```

**Relations :**
- `utilisateur` → `Utilisateur`

## 🔗 Relations entre modèles

### Schéma relationnel
```
Utilisateur (1) ←→ (N) Propriete
Utilisateur (1) ←→ (N) Contrat (en tant que bailleur)
Utilisateur (1) ←→ (N) Contrat (en tant que locataire)
Propriete (1) ←→ (N) Contrat
Contrat (1) ←→ (N) Paiement
Utilisateur (1) ←→ (N) RecapMensuel
Utilisateur (1) ←→ (N) Notification
Utilisateur (N) ←→ (N) Group
```

### Contraintes d'intégrité
1. **Clés étrangères** : Toutes les relations sont protégées par des clés étrangères
2. **Suppression en cascade** : Les données liées sont supprimées automatiquement
3. **Unicité** : Email unique pour les utilisateurs, noms uniques pour les groupes
4. **Validation** : Contrôles de cohérence des données (dates, montants, etc.)

## 📈 Index et performances

### Index automatiques
- Clés primaires (id)
- Clés étrangères
- Champs uniques (email, username)

### Index recommandés
```sql
-- Pour les requêtes fréquentes
CREATE INDEX idx_contrat_bailleur ON contrats_contrat(bailleur_id);
CREATE INDEX idx_contrat_locataire ON contrats_contrat(locataire_id);
CREATE INDEX idx_contrat_propriete ON contrats_contrat(propriete_id);
CREATE INDEX idx_paiement_contrat ON paiements_paiement(contrat_id);
CREATE INDEX idx_recap_bailleur ON paiements_recapmensuel(bailleur_id);
CREATE INDEX idx_recap_periode ON paiements_recapmensuel(annee, mois);
```

## 🔒 Sécurité et permissions

### Niveaux d'accès
1. **Superuser** : Accès complet à tous les modèles
2. **Groupe PRIVILEGE** : Accès complet aux récapitulatifs et suppression
3. **Groupe CAISSE** : Gestion des paiements uniquement
4. **Groupe ADMINISTRATION** : Administration générale

### Données sensibles
- **Suppression logique** : `est_supprime` au lieu de suppression physique
- **Audit trail** : `date_creation` sur tous les modèles
- **Validation** : Contrôles stricts sur les montants et dates

## 📊 Requêtes fréquentes

### 1. Récapitulatifs mensuels
```python
# Contrats actifs pour un bailleur et une période
contrats = Contrat.objects.filter(
    bailleur=bailleur,
    est_actif=True,
    est_resilie=False,
    date_debut__lte=fin_mois,
    date_fin__gte=debut_mois
)

# Paiements confirmés
paiements = Paiement.objects.filter(
    contrat__in=contrats,
    statut='confirme',
    date_paiement__range=[debut_mois, fin_mois]
)
```

### 2. Propriétés d'un bailleur
```python
proprietes = Propriete.objects.filter(
    bailleur=bailleur,
    est_active=True
).select_related('bailleur')
```

### 3. Notifications non lues
```python
notifications = Notification.objects.filter(
    utilisateur=user,
    est_lue=False
).order_by('-date_creation')
```

## 🛠️ Maintenance

### Migrations
```bash
# Créer une migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations
```

### Sauvegarde
```bash
# Sauvegarde SQLite
python manage.py dumpdata > backup.json

# Restauration
python manage.py loaddata backup.json
```

### Optimisation
```bash
# Analyser les requêtes lentes
python manage.py shell
>>> from django.db import connection
>>> connection.queries
```

## 📝 Changelog base de données

### Version 1.0 (Octobre 2025)
- ✅ Modèle RecapMensuel avec suppression logique
- ✅ Relations optimisées avec select_related
- ✅ Index sur les champs fréquemment utilisés
- ✅ Contraintes d'intégrité renforcées
- ✅ Système de permissions granulaire

---

**Base de données optimisée pour GESTIMMOB - Performance et sécurité garanties**
