# 🚀 Guide de Workflow de Déploiement Sécurisé - KBIS Immobilier

## 📋 Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Structure des scripts](#structure-des-scripts)
3. [Workflow de développement local](#workflow-de-développement-local)
4. [Workflow de déploiement](#workflow-de-déploiement)
5. [Gestion des erreurs et rollback](#gestion-des-erreurs-et-rollback)
6. [Monitoring et notifications](#monitoring-et-notifications)
7. [Maintenance et sauvegardes](#maintenance-et-sauvegardes)
8. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

Ce guide décrit le workflow complet pour le développement et le déploiement sécurisé de l'application KBIS Immobilier.

### 🔧 Scripts disponibles
- `update_from_branch.sh` - Mise à jour automatique depuis la branche
- `rollback_deployment.sh` - Rollback en cas de problème
- `notification_system.sh` - Système de notifications avancé
- `monitor_production.sh` - Monitoring de production
- `backup_database.sh` - Sauvegarde de base de données

---

## 📁 Structure des scripts

```
/var/www/kbis_immobilier/
├── update_from_branch.sh      # Mise à jour sécurisée
├── rollback_deployment.sh     # Rollback automatique
├── notification_system.sh     # Notifications
├── monitor_production.sh      # Monitoring
├── backup_database.sh         # Sauvegarde DB
└── GUIDE_WORKFLOW_DEPLOIEMENT.md
```

---

## 💻 Workflow de développement local

### 1. Préparation de l'environnement
```bash
# Cloner le repository
git clone https://github.com/koudougoulaurent/appli_KBIS.git
cd appli_KBIS

# Basculer sur la branche de développement
git checkout modifications-octobre-2025

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Développement
```bash
# Faire vos modifications...
# Tester localement
python manage.py runserver

# Vérifier les migrations
python manage.py makemigrations
python manage.py migrate

# Tester les fonctionnalités
python manage.py test
```

### 3. Commit et push
```bash
# Ajouter les modifications
git add .

# Commit avec un message descriptif
git commit -m "feat: ajout de la fonctionnalité X"
# ou
git commit -m "fix: correction du bug Y"
# ou
git commit -m "docs: mise à jour de la documentation"

# Push vers la branche
git push origin modifications-octobre-2025
```

---

## 🚀 Workflow de déploiement

### 1. Déploiement automatique (Recommandé)
```bash
# Sur le VPS, exécuter le script de mise à jour
cd /var/www/kbis_immobilier
sudo chmod +x update_from_branch.sh
sudo ./update_from_branch.sh
```

### 2. Déploiement manuel (Si nécessaire)
```bash
# 1. Sauvegarder la base de données
sudo ./backup_database.sh

# 2. Arrêter les services
sudo systemctl stop kbis_immobilier

# 3. Récupérer les modifications
git fetch origin
git checkout modifications-octobre-2025
git pull origin modifications-octobre-2025

# 4. Mettre à jour les dépendances
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. Appliquer les migrations
python manage.py migrate

# 6. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# 7. Redémarrer les services
sudo systemctl start kbis_immobilier
sudo systemctl reload nginx

# 8. Vérifier le déploiement
curl -I http://localhost
```

---

## 🔄 Gestion des erreurs et rollback

### 1. Rollback automatique
```bash
# Rollback complet (recommandé)
sudo ./rollback_deployment.sh

# Rollback de la base de données seulement
sudo ./rollback_deployment.sh --db-only

# Rollback de l'application seulement
sudo ./rollback_deployment.sh --app-only

# Rollback avec des sauvegardes spécifiques
sudo ./rollback_deployment.sh -d /path/to/db_backup.sql -a /path/to/app_backup
```

### 2. Lister les sauvegardes disponibles
```bash
sudo ./rollback_deployment.sh -l
```

### 3. Vérification post-rollback
```bash
# Vérifier les services
sudo systemctl status kbis_immobilier
sudo systemctl status nginx

# Tester la connectivité
curl -I http://localhost

# Vérifier les logs
sudo journalctl -u kbis_immobilier -n 20
```

---

## 📧 Monitoring et notifications

### 1. Configuration des notifications
```bash
# Configurer le système de notifications
sudo ./notification_system.sh configure

# Tester les notifications
sudo ./notification_system.sh test
```

### 2. Envoi de notifications manuelles
```bash
# Notification d'information
sudo ./notification_system.sh send info "Test" "Message de test"

# Notification d'erreur
sudo ./notification_system.sh send error "Erreur" "Description de l'erreur"

# Notification de succès
sudo ./notification_system.sh send success "Succès" "Opération réussie"
```

### 3. Monitoring automatique
```bash
# Démarrer le monitoring automatique
sudo ./notification_system.sh monitor

# Vérifier le monitoring
crontab -l
```

---

## 💾 Maintenance et sauvegardes

### 1. Sauvegarde automatique
```bash
# Sauvegarde manuelle
sudo ./backup_database.sh

# Vérifier les sauvegardes
ls -la /var/backups/kbis_immobilier/
```

### 2. Nettoyage des sauvegardes
```bash
# Les sauvegardes sont automatiquement nettoyées par les scripts
# Garde seulement les 5 dernières sauvegardes
```

### 3. Monitoring de l'espace disque
```bash
# Vérifier l'espace disque
df -h

# Vérifier la taille des logs
du -sh /var/log/kbis_immobilier/
```

---

## 🔧 Dépannage

### 1. Problèmes courants

#### Service ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u kbis_immobilier -n 50

# Vérifier la configuration
sudo systemctl status kbis_immobilier

# Redémarrer
sudo systemctl restart kbis_immobilier
```

#### Erreur de base de données
```bash
# Vérifier la connexion
sudo -u postgres psql -c "SELECT 1;"

# Vérifier les migrations
cd /var/www/kbis_immobilier
source venv/bin/activate
python manage.py showmigrations
```

#### Erreur de permissions
```bash
# Corriger les permissions
sudo chown -R www-data:www-data /var/www/kbis_immobilier
sudo chmod -R 755 /var/www/kbis_immobilier
```

### 2. Logs importants
```bash
# Logs de l'application
sudo journalctl -u kbis_immobilier -f

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Logs de PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 3. Vérifications de santé
```bash
# Vérifier tous les services
sudo systemctl status kbis_immobilier nginx postgresql

# Vérifier la connectivité
curl -I http://localhost
curl -I https://localhost

# Vérifier l'espace disque
df -h
```

---

## 📊 Tableau de bord de monitoring

### Métriques importantes
- **Services**: kbis_immobilier, nginx, postgresql
- **Espace disque**: /, /var, /var/log
- **Mémoire**: Utilisation RAM
- **Connectivité**: HTTP/HTTPS
- **Base de données**: Connexions actives

### Alertes automatiques
- Service arrêté
- Espace disque > 80%
- Mémoire > 80%
- Application non accessible
- Erreurs dans les logs

---

## 🎯 Bonnes pratiques

### 1. Développement
- ✅ Toujours tester localement avant de pusher
- ✅ Utiliser des messages de commit descriptifs
- ✅ Faire des commits fréquents et petits
- ✅ Tester les migrations avant déploiement

### 2. Déploiement
- ✅ Toujours sauvegarder avant déploiement
- ✅ Tester les migrations en mode dry-run
- ✅ Déployer pendant les heures creuses
- ✅ Vérifier le déploiement après mise à jour

### 3. Monitoring
- ✅ Configurer les notifications
- ✅ Surveiller les logs régulièrement
- ✅ Vérifier l'espace disque
- ✅ Tester les sauvegardes

---

## 🆘 Support et contacts

### En cas de problème
1. **Vérifier les logs** avec les commandes ci-dessus
2. **Utiliser le rollback** si nécessaire
3. **Consulter ce guide** pour les solutions courantes
4. **Contacter l'administrateur** si le problème persiste

### Informations système
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.12
- **Django**: 4.2+
- **PostgreSQL**: 14+
- **Nginx**: 1.24+
- **Gunicorn**: 21.2+

---

## 📝 Changelog

- **v1.0** - Guide initial avec workflow de base
- **v1.1** - Ajout du système de notifications
- **v1.2** - Ajout du monitoring automatique
- **v1.3** - Amélioration du rollback et des sauvegardes

---

*Dernière mise à jour: Octobre 2025*
