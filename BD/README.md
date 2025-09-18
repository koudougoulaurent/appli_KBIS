# 📊 SCHÉMA DE BASE DE DONNÉES - KBIS INTERNATIONAL

Ce dossier contient la documentation complète de la base de données de l'application KBIS INTERNATIONAL - Gestion Immobilière.

## 📁 Fichiers disponibles

### 📋 Documentation
- **`documentation_complete.md`** - Documentation détaillée de tous les modèles
- **`diagramme_classes_simple.md`** - Structure des modèles et relations
- **`diagramme_cas_utilisation.md`** - Cas d'utilisation et permissions

### 🔧 Guides pratiques
- **`guide_migration.md`** - Guide complet pour les migrations
- **`schema_complet.json`** - Schéma au format JSON (pour outils externes)

### 🚀 Scripts
- **`simple_schema.py`** - Script de génération automatique
- **`schema_base_donnees.py`** - Script avancé (avec erreurs corrigées)

## 🎯 Utilisation

### Pour comprendre la structure
1. Commencez par `documentation_complete.md`
2. Consultez `diagramme_classes_simple.md` pour les relations
3. Référez-vous à `diagramme_cas_utilisation.md` pour les permissions

### Pour les migrations
1. Lisez `guide_migration.md` avant toute migration
2. Suivez la checklist fournie
3. Consultez les points d'attention

### Pour la maintenance
1. Utilisez `schema_complet.json` avec des outils externes
2. Régénérez la documentation avec `simple_schema.py`
3. Mettez à jour les guides après modifications

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
python BD/simple_schema.py
```

### Ajouter un nouveau modèle
1. Créer le modèle dans l'app appropriée
2. Créer la migration
3. Mettre à jour la documentation
4. Tester la migration

### Modifier un modèle existant
1. Modifier le modèle
2. Créer la migration
3. Tester en développement
4. Appliquer en production
5. Mettre à jour la documentation

## 📞 Support

Pour toute question sur la structure de la base de données :
1. Consultez d'abord cette documentation
2. Vérifiez les guides de migration
3. Contactez l'équipe de développement

---

*Documentation générée automatiquement pour KBIS INTERNATIONAL - Gestion Immobilière*
