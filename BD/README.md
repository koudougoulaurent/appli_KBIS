# 📊 SCHÉMA DE BASE DE DONNÉES - KBIS IMMOBILIER


## 📝 Mise à jour - 23/09/2025 21:13

### Changements récents :
- ✅ Suppression de "INTERNATIONAL" du nom de l'entreprise
- ✅ Remplacement par "KBIS IMMOBILIER" dans toute l'application
- ✅ Ajout du processeur de contexte entreprise_config
- ✅ Mise à jour des templates pour utiliser la configuration dynamique


Ce dossier contient la documentation complète de la base de données de l'application KBIS IMMOBILIER - Gestion Immobilière.

## 📁 Fichiers disponibles

### 📋 Documentation
- **`SCHEMA_BDD_COMPLET.md`** - Documentation complète et détaillée de tous les modèles
- **`documentation_complete.md`** - Documentation générée automatiquement
- **`diagramme_classes_simple.md`** - Structure des modèles et relations
- **`diagramme_cas_utilisation.md`** - Cas d'utilisation et permissions

### 🔧 Guides pratiques
- **`guide_migration.md`** - Guide complet pour les migrations
- **`README_SQL.md`** - Guide d'utilisation des fichiers SQL

### 🚀 Scripts
- **`simple_schema.py`** - Script de génération automatique simple
- **`schema_base_donnees.py`** - Script avancé de génération complète
- **`generate_schema.py`** - Générateur de schéma optimisé
- **`generate_sql_other_dbms.py`** - Générateur SQL multi-SGBD

### 🗄️ Fichiers SQL
- **`SCHEMA_MYSQL.sql`** - Schéma complet pour MySQL
- **`SCHEMA_POSTGRESQL.sql`** - Schéma complet pour PostgreSQL
- **`SCHEMA_SQL_COMPLET.sql`** - Schéma SQL générique
- **`schema_complet.json`** - Schéma au format JSON (pour outils externes)

## 🎯 Utilisation

### Pour comprendre la structure
1. Commencez par `SCHEMA_BDD_COMPLET.md` pour une vue d'ensemble complète
2. Consultez `documentation_complete.md` pour les détails techniques
3. Utilisez `diagramme_classes_simple.md` pour visualiser les relations
4. Référez-vous à `diagramme_cas_utilisation.md` pour les permissions

### Pour les migrations
1. Lisez `guide_migration.md` avant toute migration
2. Suivez la checklist fournie
3. Consultez les points d'attention
4. Utilisez les fichiers SQL appropriés selon votre SGBD

### Pour la maintenance
1. Utilisez `schema_complet.json` avec des outils externes
2. Régénérez la documentation avec `python BD/simple_schema.py`
3. Générez les schémas SQL avec `python BD/generate_sql_other_dbms.py`
4. Mettez à jour les guides après modifications

### Pour le développement
1. Utilisez `generate_schema.py` pour une génération complète
2. Consultez `README_SQL.md` pour l'utilisation des fichiers SQL
3. Testez les migrations en développement avant production

## 📊 Vue d'ensemble

### Applications
- **utilisateurs** - Gestion des utilisateurs et groupes
- **proprietes** - Gestion immobilière (propriétés, bailleurs, locataires)
- **contrats** - Gestion des contrats de location
- **paiements** - Gestion des paiements et reçus
- **core** - Fonctionnalités centrales (sécurité, audit)
- **notifications** - Système de notifications

### Modèles principaux
- **Utilisateur** - Utilisateurs du système
- **Propriete** - Propriétés immobilières
- **Bailleur** - Bailleurs
- **Locataire** - Locataires
- **Contrat** - Contrats de location
- **Paiement** - Paiements
- **PlanPaiementPartiel** - Plans de paiement partiel

### Relations critiques
- `Contrat` → `Propriete` (PROTECT)
- `Contrat` → `Locataire` (PROTECT)
- `Paiement` → `Contrat` (PROTECT)

## ⚠️ Points d'attention

### Suppression logique
Les modèles suivants utilisent la suppression logique (`is_deleted`):
- Utilisateur
- Propriete
- Bailleur
- Locataire

### Sécurité
- Toutes les actions sont auditées
- Contrôle d'accès par groupes
- Logs de sécurité complets

### Performance
- Index sur les champs fréquemment utilisés
- Requêtes optimisées avec `select_related`
- Cache pour les données statiques

## 🔄 Mise à jour

### Régénérer la documentation
```bash
# Documentation simple
python BD/simple_schema.py

# Documentation complète avec diagrammes
python BD/schema_base_donnees.py

# Génération optimisée
python BD/generate_schema.py
```

### Générer les schémas SQL
```bash
# Générer pour tous les SGBD
python BD/generate_sql_other_dbms.py

# Ou utiliser les fichiers SQL existants
# - SCHEMA_MYSQL.sql pour MySQL
# - SCHEMA_POSTGRESQL.sql pour PostgreSQL
# - SCHEMA_SQL_COMPLET.sql pour SQL générique
```

### Ajouter un nouveau modèle
1. Créer le modèle dans l'app appropriée
2. Créer la migration
3. Régénérer la documentation avec les scripts
4. Tester la migration
5. Mettre à jour les fichiers SQL si nécessaire

### Modifier un modèle existant
1. Modifier le modèle
2. Créer la migration
3. Tester en développement
4. Appliquer en production
5. Régénérer la documentation
6. Mettre à jour les fichiers SQL

## 📞 Support

Pour toute question sur la structure de la base de données :
1. Consultez d'abord cette documentation
2. Vérifiez les guides de migration
3. Contactez l'équipe de développement

---

*Documentation générée automatiquement pour KBIS IMMOBILIER - Gestion Immobilière*
