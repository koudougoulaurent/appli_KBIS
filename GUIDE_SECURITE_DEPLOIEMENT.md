# 🛡️ Guide de Sécurité et Déploiement KBIS Immobilier

## Vue d'ensemble

Ce guide présente le système de sécurité complet mis en place pour assurer la continuité du service lors des mises à jour et déploiements de l'application KBIS Immobilier.

## 📋 Scripts de Sécurité Disponibles

### 1. 🔄 `backup_system.sh` - Système de Sauvegarde
**Usage:** `./backup_system.sh [type]`

**Types de sauvegarde:**
- `full` - Sauvegarde complète (base + média + statique + config + code)
- `data` - Données uniquement (base + média)
- `config` - Configurations uniquement
- `quick` - Base de données uniquement
- `list` - Lister les sauvegardes disponibles
- `cleanup` - Nettoyer les anciennes sauvegardes

**Exemples:**
```bash
# Sauvegarde complète avant déploiement
./backup_system.sh full

# Sauvegarde rapide des données
./backup_system.sh quick

# Lister les sauvegardes
./backup_system.sh list
```

### 2. 🔙 `rollback_system.sh` - Système de Rollback
**Usage:** `./rollback_system.sh <backup_name> [--dry-run]`

**Fonctionnalités:**
- Rollback complet, partiel ou de configuration
- Mode simulation avec `--dry-run`
- Vérification de santé après rollback
- Restauration automatique des services

**Exemples:**
```bash
# Rollback complet
./rollback_system.sh full_20241012_143000

# Simulation de rollback
./rollback_system.sh data_20241012_143000 --dry-run

# Lister les sauvegardes disponibles
./rollback_system.sh
```

### 3. 🏥 `health_monitor.sh` - Moniteur de Santé
**Usage:** `./health_monitor.sh [mode]`

**Modes de vérification:**
- `full` - Vérification complète (défaut)
- `quick` - Vérification rapide (services + HTTP)
- `database` - Base de données uniquement
- `services` - Services uniquement
- `performance` - Test de performance

**Exemples:**
```bash
# Vérification complète
./health_monitor.sh full

# Vérification rapide
./health_monitor.sh quick

# Test de performance
./health_monitor.sh performance
```

### 4. 🚀 `deploy_safe.sh` - Déploiement Sécurisé
**Usage:** `./deploy_safe.sh [commit_hash] [options]`

**Options:**
- `--no-backup` - Ne pas créer de sauvegarde
- `--no-rollback` - Désactiver le rollback automatique
- `--force` - Forcer le déploiement
- `--dry-run` - Mode simulation
- `--help` - Afficher l'aide

**Exemples:**
```bash
# Déploiement standard
./deploy_safe.sh

# Déploiement d'un commit spécifique
./deploy_safe.sh abc123def

# Simulation de déploiement
./deploy_safe.sh --dry-run

# Déploiement forcé sans sauvegarde
./deploy_safe.sh --no-backup --force
```

### 5. 💾 `data_persistence.sh` - Gestion de la Persistance
**Usage:** `./data_persistence.sh [action] [options]`

**Actions:**
- `setup` - Configuration initiale
- `check` - Vérification d'intégrité
- `backup [type]` - Sauvegarde (daily|weekly|monthly)
- `sync` - Synchronisation
- `restore` - Restauration
- `cleanup` - Nettoyage
- `schedule` - Configuration des sauvegardes automatiques
- `monitor` - Surveillance de l'espace disque
- `permissions` - Vérification des permissions
- `status` - Afficher le statut

**Exemples:**
```bash
# Configuration initiale
./data_persistence.sh setup

# Sauvegarde quotidienne
./data_persistence.sh backup daily

# Vérification d'intégrité
./data_persistence.sh check

# Configuration des sauvegardes automatiques
./data_persistence.sh schedule
```

## 🔒 Procédures de Sécurité

### Déploiement Standard (Recommandé)
```bash
# 1. Vérifier l'état actuel
./health_monitor.sh quick

# 2. Déploiement sécurisé
./deploy_safe.sh

# 3. Vérification post-déploiement
./health_monitor.sh full
```

### Déploiement d'un Commit Spécifique
```bash
# 1. Sauvegarde préventive
./backup_system.sh full

# 2. Déploiement du commit
./deploy_safe.sh abc123def

# 3. Vérification
./health_monitor.sh full
```

### En Cas de Problème
```bash
# 1. Vérifier les sauvegardes disponibles
./backup_system.sh list

# 2. Rollback vers la dernière sauvegarde stable
./rollback_system.sh full_20241012_143000

# 3. Vérifier la santé du service
./health_monitor.sh full
```

## 📊 Surveillance Continue

### Sauvegardes Automatiques
Les sauvegardes automatiques sont configurées via cron :
- **Quotidienne** : 02:00 (garde 7 jours)
- **Hebdomadaire** : 03:00 dimanche (garde 4 semaines)
- **Mensuelle** : 04:00 1er du mois (garde 12 mois)

### Surveillance de l'Espace Disque
```bash
# Vérifier l'espace disque
./data_persistence.sh monitor

# Nettoyer les anciennes sauvegardes
./data_persistence.sh cleanup
```

### Vérification des Permissions
```bash
# Vérifier et corriger les permissions
./data_persistence.sh permissions
```

## 🚨 Procédures d'Urgence

### Service Inaccessible
1. Vérifier le statut des services : `systemctl status kbis-immobilier nginx`
2. Consulter les logs : `journalctl -u kbis-immobilier -f`
3. Effectuer un rollback : `./rollback_system.sh [derniere_sauvegarde]`

### Problème de Base de Données
1. Vérifier l'intégrité : `./data_persistence.sh check`
2. Restaurer depuis la persistance : `./data_persistence.sh restore`
3. Si nécessaire, rollback complet : `./rollback_system.sh [sauvegarde]`

### Espace Disque Insuffisant
1. Surveiller l'espace : `./data_persistence.sh monitor`
2. Nettoyer les sauvegardes : `./data_persistence.sh cleanup`
3. Supprimer les logs anciens : `find /var/log -name "*.log" -mtime +30 -delete`

## 📁 Structure des Sauvegardes

```
/var/backups/kbis_immobilier/
├── full_YYYYMMDD_HHMMSS/          # Sauvegardes complètes
│   ├── db.sqlite3                 # Base de données
│   ├── media/                     # Fichiers média
│   ├── staticfiles/               # Fichiers statiques
│   ├── config/                    # Configurations
│   └── code/                      # Code source
├── data_YYYYMMDD_HHMMSS/          # Sauvegardes de données
├── config_YYYYMMDD_HHMMSS/        # Sauvegardes de configuration
└── quick_YYYYMMDD_HHMMSS/         # Sauvegardes rapides

/var/persistence/kbis_immobilier/  # Données de persistance
├── database/                      # Base de données
├── media/                         # Fichiers média
├── config/                        # Configurations
└── logs/                          # Logs
```

## 🔧 Configuration des Scripts

### Permissions
```bash
# Rendre tous les scripts exécutables
chmod +x *.sh

# Vérifier les propriétaires
chown kbis:kbis *.sh
```

### Variables d'Environnement
Les scripts utilisent les variables suivantes (modifiables dans chaque script) :
- `APP_DIR` : Répertoire de l'application
- `BACKUP_DIR` : Répertoire des sauvegardes
- `SERVICE_NAME` : Nom du service systemd
- `REPO_URL` : URL du dépôt Git
- `BRANCH` : Branche Git à utiliser

## 📈 Bonnes Pratiques

### Avant Chaque Déploiement
1. ✅ Vérifier l'état du service : `./health_monitor.sh quick`
2. ✅ Créer une sauvegarde : `./backup_system.sh full`
3. ✅ Tester en mode simulation : `./deploy_safe.sh --dry-run`

### Pendant le Déploiement
1. ✅ Surveiller les logs : `journalctl -u kbis-immobilier -f`
2. ✅ Vérifier la connectivité : `curl -I http://localhost:8000/`
3. ✅ Être prêt à effectuer un rollback si nécessaire

### Après le Déploiement
1. ✅ Vérifier la santé : `./health_monitor.sh full`
2. ✅ Tester les fonctionnalités critiques
3. ✅ Surveiller les performances

### Maintenance Régulière
1. ✅ Vérifier l'espace disque : `./data_persistence.sh monitor`
2. ✅ Nettoyer les anciennes sauvegardes : `./data_persistence.sh cleanup`
3. ✅ Vérifier les permissions : `./data_persistence.sh permissions`

## 🆘 Support et Dépannage

### Logs Importants
- Service Django : `journalctl -u kbis-immobilier`
- Nginx : `/var/log/nginx/error.log`
- Persistance : `/var/log/kbis_persistence.log`
- Santé : `/var/log/kbis_health.log`

### Commandes de Diagnostic
```bash
# Statut général
./data_persistence.sh status

# Vérification complète
./health_monitor.sh full

# Test de performance
./health_monitor.sh performance

# Vérification de la base de données
./data_persistence.sh check
```

---

## 📞 Contact

Pour toute question ou problème lié à la sécurité et au déploiement, consultez ce guide et les logs du système.

**Rappel :** Toujours tester en mode `--dry-run` avant un déploiement en production !
