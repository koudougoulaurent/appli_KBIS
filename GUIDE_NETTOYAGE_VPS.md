# Guide de Nettoyage Complet VPS - KBIS IMMOBILIER

## 🧹 Nettoyage VPS avec Rollback Sécurisé

Ce guide vous permet de nettoyer complètement votre VPS avant un nouveau déploiement, avec possibilité de rollback complet.

## 📋 **Étapes du Nettoyage**

### 1. **Préparation**
```bash
# Connectez-vous à votre VPS
ssh user@votre-vps

# Téléchargez les scripts de nettoyage
git clone <votre-repo> /tmp/kbis_scripts
cd /tmp/kbis_scripts
```

### 2. **Nettoyage Complet avec Rollback**
```bash
# Exécutez le script de nettoyage
sudo ./clean_vps_with_rollback.sh
```

### 3. **Vérification du Nettoyage**
```bash
# Vérifiez que tout est propre
sudo ./verify_clean_vps.sh
```

## 🔄 **Fonctionnalités du Script de Nettoyage**

### ✅ **Sauvegarde Automatique**
- 📁 **Application complète** dans `/var/backups/kbis_immobilier_cleanup_YYYYMMDD_HHMMSS/`
- ⚙️ **Configuration Nginx** sauvegardée
- 🔧 **Service systemd** sauvegardé
- 🗄️ **Base de données PostgreSQL** exportée
- 📝 **Logs complets** sauvegardés

### 🧹 **Nettoyage Complet**
- 🛑 **Arrêt des services** (Gunicorn, Nginx)
- 🗑️ **Suppression de l'application** `/var/www/kbis_immobilier`
- 🔧 **Suppression du service systemd**
- 🌐 **Suppression de la configuration Nginx**
- 📝 **Suppression des logs**
- 🗄️ **Suppression de la base de données** (optionnel)
- 📦 **Suppression des packages** (optionnel)

### 🔄 **Script de Rollback Automatique**
- 📄 **Script généré automatiquement** : `/var/backups/rollback_YYYYMMDD_HHMMSS.sh`
- 🔄 **Restauration complète** en une commande
- ✅ **Vérification automatique** de la restauration

## 🚀 **Utilisation du Rollback**

Si vous devez restaurer l'ancienne version :

```bash
# Exécutez le script de rollback
sudo /var/backups/rollback_YYYYMMDD_HHMMSS.sh
```

## 📊 **Vérification Post-Nettoyage**

Le script `verify_clean_vps.sh` vérifie :

- ✅ **Répertoires supprimés**
- ✅ **Services arrêtés et désactivés**
- ✅ **Fichiers de configuration supprimés**
- ✅ **Logs supprimés**
- ✅ **Ports libérés**
- ✅ **Base de données supprimée**
- ✅ **Processus arrêtés**

## ⚠️ **Points Importants**

### 🔒 **Sécurité**
- **Sauvegarde complète** avant toute suppression
- **Script de rollback** généré automatiquement
- **Vérification** avant suppression des données critiques

### 🎯 **Options Interactives**
- **Suppression de la base de données** : Demande confirmation
- **Suppression des packages** : Demande confirmation
- **Logs détaillés** de chaque étape

### 📁 **Structure des Sauvegardes**
```
/var/backups/kbis_immobilier_cleanup_YYYYMMDD_HHMMSS/
├── application_backup/          # Application complète
├── nginx_site.conf             # Configuration Nginx
├── systemd_service.service     # Service systemd
├── database_backup.sql         # Base de données
├── nginx_symlink.txt           # Info lien symbolique
└── logs/                       # Logs complets
    ├── gunicorn/
    ├── django/
    └── gunicorn_journal.log
```

## 🎯 **Workflow Recommandé**

### 1. **Nettoyage Complet**
```bash
sudo ./clean_vps_with_rollback.sh
```

### 2. **Vérification**
```bash
sudo ./verify_clean_vps.sh
```

### 3. **Nouveau Déploiement**
```bash
git clone <votre-repo> /var/www/kbis_immobilier
cd /var/www/kbis_immobilier
sudo ./deploy_vps.sh
```

## 🔍 **Dépannage**

### Si le nettoyage échoue :
```bash
# Vérifiez les logs
sudo journalctl -u kbis_immobilier -f

# Vérifiez les processus
ps aux | grep kbis

# Forcez l'arrêt
sudo pkill -f kbis
sudo systemctl stop kbis_immobilier
```

### Si vous devez rollback :
```bash
# Listez les sauvegardes disponibles
ls -la /var/backups/ | grep kbis_immobilier_cleanup

# Exécutez le rollback
sudo /var/backups/rollback_YYYYMMDD_HHMMSS.sh
```

## ✅ **Avantages du Nettoyage Complet**

- 🧹 **VPS 100% propre** sans résidus
- 🔄 **Rollback sécurisé** en cas de problème
- 🚀 **Déploiement optimal** sans conflits
- 📊 **Vérification complète** de l'état
- 🛡️ **Sécurité maximale** avec sauvegardes

Votre VPS sera parfaitement nettoyé et prêt pour un déploiement optimal ! 🎉
