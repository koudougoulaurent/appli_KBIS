# GUIDE DE MIGRATION - KBIS IMMOBILIER

## 🚀 Commandes essentielles

```bash
# Créer une migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations

# Créer une migration pour une app spécifique
python manage.py makemigrations <app_name>

# Appliquer une migration spécifique
python manage.py migrate <app_name> <migration_number>

# Annuler une migration
python manage.py migrate <app_name> <migration_number_previous>

# Créer une migration vide (pour données)
python manage.py makemigrations --empty <app_name>
```

## 📋 Checklist avant migration

- [ ] Sauvegarder la base de données
- [ ] Tester en environnement de développement
- [ ] Vérifier les contraintes de clés étrangères
- [ ] Documenter les changements
- [ ] Informer l'équipe
- [ ] Vérifier les dépendances
- [ ] Tester les rollbacks

## ⚠️ Points d'attention

### Modèles avec suppression logique
- `Utilisateur` (is_deleted)
- `Propriete` (is_deleted)
- `Bailleur` (is_deleted)
- `Locataire` (is_deleted)

**Impact:** Les suppressions ne sont pas physiques, attention aux requêtes.

### Relations critiques
- `Contrat` → `Propriete` (PROTECT)
- `Contrat` → `Locataire` (PROTECT)
- `Paiement` → `Contrat` (PROTECT)

**Impact:** Impossible de supprimer les modèles référencés.

### Modèles principaux par application

#### utilisateurs
- `Utilisateur` - Utilisateurs du système
- `GroupeTravail` - Groupes de travail

#### proprietes
- `Propriete` - Propriétés immobilières
- `Bailleur` - Bailleurs
- `Locataire` - Locataires
- `TypeBien` - Types de biens
- `ChargesBailleur` - Charges bailleur
- `Document` - Documents

#### contrats
- `Contrat` - Contrats de location
- `Quittance` - Quittances de loyer
- `EtatLieux` - États des lieux

#### paiements
- `Paiement` - Paiements
- `Recu` - Reçus de paiement
- `Retrait` - Retraits
- `CompteBancaire` - Comptes bancaires
- `ChargeDeductible` - Charges déductibles
- `PlanPaiementPartiel` - Plans de paiement partiel
- `EchelonPaiement` - Échéances de paiement
- `PaiementPartiel` - Paiements partiels

#### core
- `NiveauAcces` - Niveaux d'accès
- `AuditLog` - Logs d'audit

#### notifications
- `Notification` - Notifications système

## 🔄 Processus de migration

### 1. Développement
```bash
# Modifier les modèles
# Créer la migration
python manage.py makemigrations

# Tester localement
python manage.py migrate
```

### 2. Test
```bash
# Appliquer sur base de test
python manage.py migrate --settings=gestion_immobiliere.settings_test

# Vérifier les données
python manage.py shell
```

### 3. Production
```bash
# Sauvegarder la base
pg_dump appli_kbis > backup_$(date +%Y%m%d_%H%M%S).sql

# Appliquer la migration
python manage.py migrate

# Vérifier l'état
python manage.py showmigrations
```

## 🛠️ Migration de données

### Script de migration personnalisé
```python
# Dans le fichier de migration
from django.db import migrations

def migrate_data(apps, schema_editor):
    # Logique de migration des données
    pass

def reverse_migrate_data(apps, schema_editor):
    # Logique de rollback
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('app_name', 'previous_migration'),
    ]
    
    operations = [
        migrations.RunPython(migrate_data, reverse_migrate_data),
    ]
```

### Exemples de migrations courantes

#### Ajouter un champ avec valeur par défaut
```python
# models.py
class MonModele(models.Model):
    nouveau_champ = models.CharField(max_length=100, default='valeur_defaut')

# Migration générée automatiquement
```

#### Renommer un champ
```python
# 1. Créer un nouveau champ
# 2. Migrer les données
# 3. Supprimer l'ancien champ
```

#### Modifier un type de champ
```python
# Attention aux pertes de données
# Toujours tester sur des données de test
```

## 🚨 Gestion des erreurs

### Erreur de contrainte de clé étrangère
```bash
# Vérifier les données orphelines
python manage.py shell
>>> from app.models import MonModele
>>> MonModele.objects.filter(foreign_key__isnull=True)
```

### Erreur de migration
```bash
# Annuler la dernière migration
python manage.py migrate app_name previous_migration_number

# Corriger le code
# Recréer la migration
python manage.py makemigrations
```

### Données corrompues
```bash
# Restaurer depuis la sauvegarde
psql appli_kbis < backup_file.sql

# Ou restaurer partiellement
```

## 📊 Monitoring des migrations

### Vérifier l'état
```bash
python manage.py showmigrations
```

### Logs de migration
```bash
# Les migrations sont loggées dans les logs Django
tail -f logs/django.log | grep migration
```

### Vérifier l'intégrité
```python
# Script de vérification
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT * FROM django_migrations;")
>>> cursor.fetchall()
```

## 🔧 Outils utiles

### Django Extensions
```bash
pip install django-extensions

# Voir le schéma SQL
python manage.py graph_models -a -o schema.png

# Shell amélioré
python manage.py shell_plus
```

### pgAdmin (PostgreSQL)
- Interface graphique pour la base de données
- Visualisation des contraintes
- Exécution de requêtes SQL

### Backup automatique
```bash
# Script de sauvegarde quotidienne
#!/bin/bash
pg_dump appli_kbis > /backups/appli_kbis_$(date +%Y%m%d).sql
```

## 📝 Documentation des migrations

### Template de documentation
```markdown
## Migration [numero] - [date]

### Changements
- Ajout du champ X dans le modèle Y
- Modification du type de champ Z
- Suppression de la table W

### Impact
- Aucun impact sur les données existantes
- Nouveau champ avec valeur par défaut

### Tests
- [ ] Migration appliquée avec succès
- [ ] Données existantes préservées
- [ ] Nouvelles fonctionnalités opérationnelles
- [ ] Rollback testé

### Notes
- Attention particulière à...
- Données migrées depuis...
```

## 🎯 Bonnes pratiques

1. **Toujours sauvegarder** avant migration
2. **Tester en développement** d'abord
3. **Documenter les changements**
4. **Prévoir le rollback**
5. **Communiquer avec l'équipe**
6. **Monitorer après migration**
7. **Valider les données critiques**
