# 🗄️ **CODE SQL COMPLET - GESTIMMOB**

## 📋 **Vue d'ensemble**

Ce dossier contient tous les scripts SQL nécessaires pour créer et gérer la base de données de l'application GESTIMMOB (Gestion Immobilière).

---

## 📁 **Fichiers disponibles**

### **1. Scripts SQL par SGBD**

| Fichier | SGBD | Description | Taille |
|---------|------|-------------|---------|
| `SCHEMA_SQL_COMPLET.sql` | SQLite | Script complet pour SQLite | ~50KB |
| `SCHEMA_POSTGRESQL.sql` | PostgreSQL | Script optimisé pour PostgreSQL | ~14KB |
| `SCHEMA_MYSQL.sql` | MySQL | Script optimisé pour MySQL | ~10KB |

### **2. Scripts Python d'automatisation**

| Fichier | Description | Usage |
|---------|-------------|-------|
| `create_database.py` | Création automatique SQLite | `python create_database.py` |
| `create_sqlite_direct.py` | Création directe SQLite | `python create_sqlite_direct.py` |
| `generate_sql_other_dbms.py` | Génération multi-SGBD | `python generate_sql_other_dbms.py` |

### **3. Documentation**

| Fichier | Description |
|---------|-------------|
| `SCHEMA_BDD_COMPLET.md` | Documentation complète du schéma |
| `SCHEMA_BDD_GESTIMMOB.pdf` | PDF du schéma (prêt à imprimer) |
| `README_SQL.md` | Ce fichier de documentation |

---

## 🚀 **Utilisation rapide**

### **SQLite (Recommandé pour le développement)**
```bash
# Création automatique
python create_sqlite_direct.py

# Ou création manuelle
sqlite3 gestimmob_database.sqlite3 < SCHEMA_SQL_COMPLET.sql
```

### **PostgreSQL (Production)**
```bash
# Créer la base de données
createdb gestimmob

# Exécuter le script
psql -d gestimmob -f SCHEMA_POSTGRESQL.sql
```

### **MySQL (Production)**
```bash
# Créer la base de données
mysql -u root -p -e "CREATE DATABASE gestimmob;"

# Exécuter le script
mysql -u root -p gestimmob < SCHEMA_MYSQL.sql
```

---

## 🏗️ **Structure de la base de données**

### **6 modules principaux :**

1. **🔧 CORE** - Configuration et sécurité
   - `core_configurationentreprise` - Configuration de l'entreprise
   - `core_niveauacces` - Niveaux d'accès
   - `core_devise` - Gestion des devises

2. **👥 UTILISATEURS** - Gestion des utilisateurs
   - `utilisateurs_utilisateur` - Utilisateurs du système
   - `utilisateurs_groupetravail` - Groupes de travail

3. **🏠 PROPRIETES** - Gestion immobilière
   - `proprietes_propriete` - Propriétés
   - `proprietes_bailleur` - Bailleurs
   - `proprietes_locataire` - Locataires
   - `proprietes_typebien` - Types de biens

4. **📋 CONTRATS** - Gestion des contrats
   - `contrats_contrat` - Contrats de location
   - `contrats_quittance` - Quittances
   - `contrats_etatlieux` - États des lieux

5. **💰 PAIEMENTS** - Gestion financière
   - `paiements_paiement` - Paiements
   - `paiements_chargedeductible` - Charges déductibles
   - `paiements_recapmensuel` - Récapitulatifs

6. **🔔 NOTIFICATIONS** - Système de notifications
   - `notifications_notification` - Notifications
   - `notifications_notificationpreference` - Préférences

---

## 📊 **Statistiques du schéma**

- **13 tables principales** créées
- **40+ relations** ForeignKey
- **5 relations** ManyToMany
- **4 relations** OneToOne
- **15+ contraintes** d'unicité
- **20+ champs** avec choix prédéfinis
- **Suppression logique** implémentée
- **Audit complet** des actions

---

## 🔧 **Fonctionnalités avancées**

### **Sécurité**
- ✅ Niveaux d'accès granulaires
- ✅ Permissions par type de données
- ✅ Contrôle d'accès aux montants
- ✅ Journalisation complète des actions

### **Intégrité**
- ✅ Contraintes de clés étrangères
- ✅ Contraintes de validation
- ✅ Suppression logique
- ✅ Horodatage automatique

### **Performance**
- ✅ Index optimisés
- ✅ Requêtes optimisées
- ✅ Triggers pour audit
- ✅ Métadonnées communes

---

## 📝 **Données initiales incluses**

### **Niveaux d'accès (5)**
- Public, Interne, Confidentiel, Secret, Top Secret

### **Types de biens (6)**
- Appartement, Studio, Maison, Bureau, Commerce, Parking

### **Devises (3)**
- Euro (EUR), Dollar (USD), Franc CFA (XOF)

### **Utilisateur admin**
- Username: `admin`
- Email: `admin@gestimmob.fr`

### **Configuration entreprise**
- Nom: `GESTIMMOB`
- Actif par défaut

---

## 🛠️ **Maintenance**

### **Sauvegarde**
```bash
# SQLite
cp gestimmob_database.sqlite3 backup_$(date +%Y%m%d).sqlite3

# PostgreSQL
pg_dump gestimmob > backup_$(date +%Y%m%d).sql

# MySQL
mysqldump -u root -p gestimmob > backup_$(date +%Y%m%d).sql
```

### **Restauration**
```bash
# SQLite
cp backup_20250910.sqlite3 gestimmob_database.sqlite3

# PostgreSQL
psql -d gestimmob < backup_20250910.sql

# MySQL
mysql -u root -p gestimmob < backup_20250910.sql
```

---

## 🔍 **Vérification de l'intégrité**

### **SQLite**
```sql
-- Vérifier les tables
.tables

-- Vérifier les contraintes
PRAGMA foreign_key_check;

-- Compter les enregistrements
SELECT COUNT(*) FROM core_configurationentreprise;
```

### **PostgreSQL**
```sql
-- Vérifier les tables
\dt

-- Vérifier les contraintes
SELECT * FROM information_schema.table_constraints;

-- Compter les enregistrements
SELECT COUNT(*) FROM core_configurationentreprise;
```

### **MySQL**
```sql
-- Vérifier les tables
SHOW TABLES;

-- Vérifier les contraintes
SELECT * FROM information_schema.table_constraints;

-- Compter les enregistrements
SELECT COUNT(*) FROM core_configurationentreprise;
```

---

## 📞 **Support**

Pour toute question ou problème :

1. **Vérifiez** les logs d'erreur
2. **Consultez** la documentation du schéma
3. **Testez** avec les scripts fournis
4. **Contactez** l'équipe de développement

---

## 🎯 **Prochaines étapes**

1. ✅ **Créer la base de données** avec les scripts fournis
2. ✅ **Configurer Django** pour utiliser cette base
3. ✅ **Exécuter les migrations** Django si nécessaire
4. ✅ **Créer un superutilisateur** : `python manage.py createsuperuser`
5. ✅ **Démarrer l'application** : `python manage.py runserver`

---

*Documentation générée le : 10/09/2025*  
*Version de l'application : 1.0*  
*Base de données : Multi-SGBD compatible*
