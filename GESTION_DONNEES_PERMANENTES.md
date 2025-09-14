# 🗄️ Gestion des Données Permanentes

## 🔒 **Mots de Passe de Tous les Utilisateurs**

**Tous les utilisateurs ont le même mot de passe :** `password123`

### 👥 **Liste Complète des Utilisateurs :**

| Utilisateur | Nom Complet | Poste | Groupe | Mot de Passe |
|-------------|-------------|-------|--------|--------------|
| `admin` | Super Administrateur | Super Administrateur | PRIVILEGE | `password123` |
| `directeur` | Directeur Général | Directeur Général | PRIVILEGE | `password123` |
| `privilege1` | Alice Manager | Manager | PRIVILEGE | `password123` |
| `demo` | Démo Utilisateur | Utilisateur Démo | PRIVILEGE | `password123` |
| `admin1` | Claire Administratrice | Administratrice | ADMINISTRATION | `password123` |
| `gestion1` | Paul Gestionnaire | Gestionnaire | ADMINISTRATION | `password123` |
| `caisse1` | Marie Caissière | Caissière | CAISSE | `password123` |
| `caisse2` | Fatou Traoré | Agent de caisse | CAISSE | `password123` |
| `controle1` | Sophie Contrôleuse | Contrôleuse | CONTROLES | `password123` |
| `audit1` | Jean Auditeur | Auditeur | CONTROLES | `password123` |

## 🛡️ **Protection des Données**

### ✅ **Garanties de Permanence :**

1. **Aucune donnée ne se perd** lors des redéploiements
2. **Sauvegarde automatique** avant chaque redéploiement
3. **Restauration automatique** des données existantes
4. **Protection des données réelles** contre la suppression accidentelle

### 🔄 **Système de Sauvegarde :**

- **Sauvegarde automatique** au démarrage de l'application
- **Fichiers JSON** dans le dossier `backup_data/`
- **Timestamp unique** pour chaque sauvegarde
- **Sauvegarde complète** de tous les types de données

## 📋 **Types de Données Sauvegardées :**

### 👥 **Utilisateurs :**
- Informations personnelles
- Groupes de travail
- Permissions et statuts
- **Note :** Les mots de passe sont réinitialisés à `password123`

### 🏠 **Propriétés :**
- Adresses et descriptions
- Types de biens
- Loyers et charges
- Statuts d'activité

### 👤 **Bailleurs et Locataires :**
- Informations de contact
- Adresses
- Statuts d'activité

### 📋 **Configuration :**
- Groupes de travail
- Types de biens
- Permissions

## 🚀 **Scripts de Gestion :**

### 1. **Sauvegarde Manuelle :**
```bash
python sauvegarder_donnees.py
```

### 2. **Restauration Manuelle :**
```bash
python restaurer_donnees.py
# ou avec timestamp spécifique :
python restaurer_donnees.py 20250114_143022
```

### 3. **Gestion Interactive :**
```bash
python gestion_donnees.py
```

### 4. **Test Local :**
```bash
python test_donnees_locales.py
```

## 🔧 **Fonctionnalités du Script de Gestion :**

1. **💾 Sauvegarder** les données
2. **🔄 Restaurer** depuis une sauvegarde
3. **📊 Afficher** les statistiques
4. **🔍 Lister** les sauvegardes disponibles
5. **🗑️ Supprimer** les données de test uniquement
6. **❌ Quitter** le programme

## ⚠️ **Important :**

### ✅ **Ce qui est PROTÉGÉ :**
- Toutes les données réelles (propriétés, bailleurs, locataires)
- Groupes de travail et types de biens
- Utilisateurs admin et directeur
- Historique des paiements et contrats

### 🗑️ **Ce qui peut être supprimé :**
- Utilisateurs de test (sauf admin et directeur)
- Propriétés de test
- Bailleurs et locataires de test
- **UNIQUEMENT** avec confirmation explicite

## 🔄 **Processus de Redéploiement :**

1. **Sauvegarde automatique** des données existantes
2. **Vérification** des données essentielles
3. **Création** des données manquantes
4. **Démarrage** de l'application
5. **Aucune perte** de données réelles

## 📁 **Structure des Sauvegardes :**

```
backup_data/
├── resume_20250114_143022.json      # Résumé de la sauvegarde
├── groupes_20250114_143022.json     # Groupes de travail
├── types_biens_20250114_143022.json # Types de biens
├── utilisateurs_20250114_143022.json # Utilisateurs
├── proprietes_20250114_143022.json  # Propriétés
├── bailleurs_20250114_143022.json   # Bailleurs
└── locataires_20250114_143022.json  # Locataires
```

## 🆘 **En Cas de Problème :**

1. **Vérifiez les logs** de déploiement Render
2. **Utilisez le script de gestion** pour restaurer
3. **Contactez l'administrateur** si nécessaire

## 📞 **Support :**

- **Documentation :** Ce fichier
- **Scripts :** Dans le répertoire racine
- **Logs :** Dashboard Render
- **Sauvegardes :** Dossier `backup_data/`

---

**🛡️ Vos données sont en sécurité et ne se perdront jamais !**
