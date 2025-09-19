# 🗄️ GUIDE D'UTILISATION DES FICHIERS SQL - KBIS INTERNATIONAL

Ce guide explique comment utiliser les différents fichiers SQL fournis pour l'application KBIS INTERNATIONAL.

## 📁 Fichiers SQL disponibles

### 🐬 MySQL
- **`SCHEMA_MYSQL.sql`** - Schéma complet optimisé pour MySQL 8.0+
- **Caractéristiques :**
  - Utilise `AUTO_INCREMENT` pour les clés primaires
  - Support des contraintes `CHECK` (MySQL 8.0+)
  - Collation `utf8mb4_unicode_ci`
  - Moteur `InnoDB` par défaut

### 🐘 PostgreSQL
- **`SCHEMA_POSTGRESQL.sql`** - Schéma complet optimisé pour PostgreSQL 12+
- **Caractéristiques :**
  - Utilise `SERIAL` pour les clés primaires
  - Support complet des contraintes `CHECK`
  - Types de données PostgreSQL natifs
  - Index et contraintes optimisés

### 🔧 SQL Générique
- **`SCHEMA_SQL_COMPLET.sql`** - Schéma compatible avec la plupart des SGBD
- **Caractéristiques :**
  - Syntaxe SQL standard
  - Compatible avec SQLite, MySQL, PostgreSQL
  - Contraintes de base uniquement

## 🚀 Utilisation

### Installation MySQL
```bash
# Créer la base de données
mysql -u root -p -e "CREATE DATABASE gestimmob CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Importer le schéma
mysql -u root -p gestimmob < BD/SCHEMA_MYSQL.sql
```

### Installation PostgreSQL
```bash
# Créer la base de données
createdb -U postgres gestimmob

# Importer le schéma
psql -U postgres -d gestimmob -f BD/SCHEMA_POSTGRESQL.sql
```

### Installation SQLite
```bash
# Créer la base de données
sqlite3 gestimmob.db < BD/SCHEMA_SQL_COMPLET.sql
```

## 📊 Structure des tables

### Tables principales
1. **core_configurationentreprise** - Configuration de l'entreprise
2. **core_niveauacces** - Niveaux d'accès aux données
3. **core_auditlog** - Journal d'audit
4. **utilisateurs_utilisateur** - Utilisateurs du système
5. **proprietes_propriete** - Propriétés immobilières
6. **proprietes_bailleur** - Bailleurs
7. **proprietes_locataire** - Locataires
8. **contrats_contrat** - Contrats de location
9. **paiements_paiement** - Paiements

### Relations importantes
- `contrats_contrat` → `proprietes_propriete` (PROTECT)
- `contrats_contrat` → `proprietes_locataire` (PROTECT)
- `paiements_paiement` → `contrats_contrat` (PROTECT)

## ⚠️ Points d'attention

### Suppression logique
Les tables suivantes utilisent la suppression logique :
- `utilisateurs_utilisateur` (is_deleted)
- `proprietes_propriete` (is_deleted)
- `proprietes_bailleur` (is_deleted)
- `proprietes_locataire` (is_deleted)

### Contraintes de clés étrangères
- Toutes les relations critiques utilisent `ON DELETE PROTECT`
- Les suppressions sont gérées par la suppression logique
- Les contraintes `CHECK` valident les valeurs des champs

### Index et performance
- Index automatiques sur les clés primaires
- Index sur les champs `unique`
- Index sur les champs de recherche fréquents
- Index composites pour les requêtes complexes

## 🔧 Maintenance

### Sauvegarde
```bash
# MySQL
mysqldump -u root -p gestimmob > backup_gestimmob.sql

# PostgreSQL
pg_dump -U postgres gestimmob > backup_gestimmob.sql

# SQLite
cp gestimmob.db backup_gestimmob.db
```

### Vérification de l'intégrité
```sql
-- Vérifier les contraintes de clés étrangères
SELECT * FROM information_schema.REFERENTIAL_CONSTRAINTS 
WHERE CONSTRAINT_SCHEMA = 'gestimmob';

-- Vérifier les index
SHOW INDEX FROM table_name;
```

### Mise à jour du schéma
1. Sauvegarder la base de données
2. Appliquer les nouvelles migrations
3. Vérifier l'intégrité des données
4. Tester les fonctionnalités

## 📈 Optimisations

### MySQL
- Utiliser `EXPLAIN` pour analyser les requêtes
- Configurer `innodb_buffer_pool_size`
- Optimiser les requêtes avec `SELECT_related`

### PostgreSQL
- Utiliser `EXPLAIN ANALYZE` pour analyser les requêtes
- Configurer `shared_buffers` et `work_mem`
- Utiliser les index partiels si nécessaire

### SQLite
- Utiliser `PRAGMA optimize` régulièrement
- Configurer `PRAGMA journal_mode=WAL`
- Analyser les requêtes avec `EXPLAIN QUERY PLAN`

## 🆘 Dépannage

### Problèmes courants
1. **Erreur de contrainte de clé étrangère**
   - Vérifier l'ordre d'insertion des données
   - Utiliser la suppression logique

2. **Erreur de contrainte CHECK**
   - Vérifier les valeurs des champs
   - Consulter les choix disponibles

3. **Problème de performance**
   - Analyser les requêtes lentes
   - Ajouter des index si nécessaire

### Logs et monitoring
- Surveiller les logs d'erreur du SGBD
- Utiliser les outils de monitoring
- Analyser les requêtes lentes

---

*Guide généré pour KBIS INTERNATIONAL - Gestion Immobilière*