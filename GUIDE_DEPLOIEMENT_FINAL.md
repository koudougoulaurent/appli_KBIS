# Guide de Déploiement Final - KBIS Immobilier

## 🚀 Déploiement VPS avec PostgreSQL

### Prérequis
- VPS Ubuntu 20.04+ ou Debian 11+
- Accès root ou utilisateur avec privilèges sudo
- Nom de domaine (optionnel pour HTTPS)

### Méthode 1: Déploiement Automatique (Recommandé)

#### Sur Windows (PowerShell)
```powershell
# Exécuter le script PowerShell
.\deploy_vps_windows.ps1 -VpsIp "VOTRE_IP_VPS" -Domain "votre-domaine.com"
```

#### Sur Linux/Mac
```bash
# Rendre les scripts exécutables
chmod +x deploy_vps_postgresql.sh setup_https.sh maintenance_vps.sh test_deployment.sh

# Exécuter le déploiement
./deploy_vps_postgresql.sh
```

### Méthode 2: Déploiement Manuel

#### 1. Préparation du VPS
```bash
# Connexion au VPS
ssh root@VOTRE_IP_VPS

# Création de l'utilisateur application
adduser kbis
usermod -aG sudo kbis
su - kbis
```

#### 2. Installation des Dépendances
```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des paquets requis
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    supervisor \
    certbot \
    python3-certbot-nginx
```

#### 3. Configuration PostgreSQL
```bash
# Démarrage de PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Création de la base de données
sudo -u postgres psql
CREATE USER kbis WITH PASSWORD 'votre-mot-de-passe-securise';
CREATE DATABASE kbis_immobilier OWNER kbis;
GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO kbis;
\q
```

#### 4. Configuration de l'Application
```bash
# Clonage du code
git clone -b modifications-octobre-2025 https://github.com/koudougoulaurent/appli_KBIS.git
cd appli_KBIS

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Configuration de l'environnement
cp .env.production .env
# Éditer .env avec vos paramètres
```

#### 5. Configuration Django
```bash
# Migration de la base de données
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Création du superutilisateur
python manage.py createsuperuser
```

#### 6. Configuration des Services
```bash
# Configuration du service systemd
sudo cp kbis-immobilier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kbis-immobilier
sudo systemctl start kbis-immobilier

# Configuration Nginx
sudo cp nginx.conf /etc/nginx/sites-available/kbis-immobilier
sudo ln -s /etc/nginx/sites-available/kbis-immobilier /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Configuration HTTPS (Optionnel)

```bash
# Configuration du domaine et certificat SSL
./setup_https.sh
```

### Vérification du Déploiement

```bash
# Test complet de l'installation
./test_deployment.sh

# Vérification manuelle
curl http://VOTRE_IP_VPS
curl http://VOTRE_IP_VPS/admin
```

## 🔧 Maintenance

### Script de Maintenance
```bash
# Commandes disponibles
./maintenance_vps.sh update          # Mise à jour
./maintenance_vps.sh backup          # Sauvegarde
./maintenance_vps.sh restore         # Restauration
./maintenance_vps.sh status          # Statut des services
./maintenance_vps.sh logs            # Logs en temps réel
./maintenance_vps.sh restart         # Redémarrage
```

### Sauvegardes Automatiques
```bash
# Ajouter à la crontab
crontab -e

# Sauvegarde quotidienne à 2h du matin
0 2 * * * /home/kbis/appli_KBIS/maintenance_vps.sh backup
```

## 📊 Monitoring

### Vérification des Services
```bash
# Statut des services
sudo systemctl status kbis-immobilier
sudo systemctl status nginx
sudo systemctl status postgresql

# Logs
sudo journalctl -u kbis-immobilier -f
sudo tail -f /var/log/nginx/kbis_error.log
```

### Métriques de Performance
```bash
# Utilisation des ressources
htop
df -h
free -h

# Connexions actives
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
```

## 🛠️ Dépannage

### Problèmes Courants

#### 1. Erreur 502 Bad Gateway
```bash
# Vérifier que Gunicorn fonctionne
sudo systemctl status kbis-immobilier

# Vérifier les logs
sudo journalctl -u kbis-immobilier -f
```

#### 2. Erreur de Base de Données
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Tester la connexion
sudo -u postgres psql -c "SELECT 1;"
```

#### 3. Fichiers Statiques Non Servis
```bash
# Vérifier les permissions
ls -la /home/kbis/appli_KBIS/staticfiles/

# Recollecter les statiques
python manage.py collectstatic --noinput
```

### Logs Importants
- Application Django : `sudo journalctl -u kbis-immobilier`
- Nginx : `/var/log/nginx/kbis_error.log`
- PostgreSQL : `/var/log/postgresql/postgresql-*.log`

## 🔒 Sécurité

### Configuration du Pare-feu
```bash
# Configuration UFW
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### Mise à Jour Régulière
```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Mise à jour de l'application
./maintenance_vps.sh update
```

## 📱 URLs d'Accès

- **Application** : `http://VOTRE_IP` ou `https://votre-domaine`
- **Admin Django** : `http://VOTRE_IP/admin` ou `https://votre-domaine/admin`
- **API** : `http://VOTRE_IP/api/` ou `https://votre-domaine/api/`

## 🔑 Informations de Connexion par Défaut

- **Utilisateur Admin** : `admin`
- **Mot de Passe** : `admin123`
- **Base de Données** : `kbis_immobilier`
- **Utilisateur DB** : `kbis`

## 📞 Support

En cas de problème :

1. Vérifiez les logs avec `./maintenance_vps.sh logs`
2. Consultez le statut avec `./maintenance_vps.sh status`
3. Redémarrez avec `./maintenance_vps.sh restart`
4. Exécutez le test complet avec `./test_deployment.sh`

## 🎯 Architecture Finale

```
Internet → Nginx (Port 80/443) → Gunicorn (Port 8000) → Django → PostgreSQL
```

### Composants
- **Nginx** : Serveur web et reverse proxy
- **Gunicorn** : Serveur WSGI pour Django
- **Django** : Framework web Python
- **PostgreSQL** : Base de données relationnelle
- **Systemd** : Gestionnaire de services
- **Let's Encrypt** : Certificats SSL (optionnel)

### Fichiers de Configuration
- `gestion_immobiliere/settings_production.py` : Configuration Django production
- `nginx.conf` : Configuration Nginx
- `gunicorn.conf.py` : Configuration Gunicorn
- `.env.production` : Variables d'environnement
- `deploy_vps_postgresql.sh` : Script de déploiement automatique
- `maintenance_vps.sh` : Script de maintenance
- `test_deployment.sh` : Script de test

## ✅ Checklist de Déploiement

- [ ] VPS configuré avec Ubuntu/Debian
- [ ] Utilisateur `kbis` créé
- [ ] PostgreSQL installé et configuré
- [ ] Nginx installé et configuré
- [ ] Code de l'application déployé
- [ ] Environnement virtuel Python créé
- [ ] Dépendances installées
- [ ] Base de données migrée
- [ ] Fichiers statiques collectés
- [ ] Services systemd configurés
- [ ] Pare-feu configuré
- [ ] Test de l'application réussi
- [ ] HTTPS configuré (optionnel)
- [ ] Sauvegardes automatiques configurées
- [ ] Monitoring en place

## 🎉 Félicitations !

Votre application KBIS Immobilier est maintenant déployée et prête à être utilisée !