# Guide de Déploiement KBIS IMMOBILIER

## Déploiement sur VPS avec Nginx et Gunicorn

### Prérequis

- VPS Ubuntu 20.04+ ou Debian 11+
- Accès root ou sudo
- Nom de domaine configuré (optionnel)

### Installation automatique

1. **Cloner le repository**
   ```bash
   git clone <votre-repo> /var/www/kbis_immobilier
   cd /var/www/kbis_immobilier
   ```

2. **Exécuter le script de déploiement**
   ```bash
   chmod +x deploy_vps.sh
   sudo ./deploy_vps.sh
   ```

3. **Configurer l'environnement**
   ```bash
   cp env.example .env
   nano .env
   ```

### Configuration manuelle

#### 1. Installation des dépendances système

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib nginx redis-server git \
    libpq-dev build-essential
```

#### 2. Configuration de PostgreSQL

```bash
# Connexion à PostgreSQL
sudo -u postgres psql

# Création de la base de données
CREATE DATABASE kbis_immobilier;
CREATE USER kbis_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO kbis_user;
ALTER USER kbis_user CREATEDB;
\q
```

#### 3. Configuration de l'application

```bash
# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Configuration de l'environnement
cp env.example .env
nano .env

# Migrations de la base de données
python manage.py makemigrations
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Création d'un superutilisateur
python manage.py createsuperuser
```

#### 4. Configuration de Gunicorn

Le fichier `gunicorn.conf.py` est déjà configuré. Créez le service systemd :

```bash
sudo nano /etc/systemd/system/kbis_immobilier.service
```

Contenu du service :
```ini
[Unit]
Description=KBIS IMMOBILIER Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/kbis_immobilier
Environment="PATH=/var/www/kbis_immobilier/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production"
ExecStart=/var/www/kbis_immobilier/venv/bin/gunicorn --config gunicorn.conf.py gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Démarrez le service :
```bash
sudo systemctl daemon-reload
sudo systemctl enable kbis_immobilier
sudo systemctl start kbis_immobilier
```

#### 5. Configuration de Nginx

```bash
# Copie de la configuration
sudo cp nginx.conf /etc/nginx/sites-available/kbis_immobilier
sudo ln -s /etc/nginx/sites-available/kbis_immobilier /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test de la configuration
sudo nginx -t

# Redémarrage de Nginx
sudo systemctl restart nginx
```

#### 6. Configuration SSL (optionnel)

```bash
# Installation de Certbot
sudo apt install certbot python3-certbot-nginx

# Génération du certificat SSL
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Test du renouvellement automatique
sudo certbot renew --dry-run
```

### Configuration de l'environnement

Modifiez le fichier `.env` avec vos paramètres :

```env
# Configuration de sécurité
SECRET_KEY=votre-clé-secrète-très-longue-et-complexe
DEBUG=False

# Configuration des hôtes autorisés
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com,www.votre-domaine.com

# Configuration de la base de données PostgreSQL
DB_NAME=kbis_immobilier
DB_USER=kbis_user
DB_PASSWORD=votre_mot_de_passe_base_de_données
DB_HOST=localhost
DB_PORT=5432

# Configuration email
EMAIL_HOST=smtp.votre-fournisseur.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@votre-domaine.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_email
DEFAULT_FROM_EMAIL=noreply@votre-domaine.com
```

### Commandes utiles

```bash
# Redémarrage des services
sudo systemctl restart kbis_immobilier
sudo systemctl restart nginx

# Vérification des logs
sudo journalctl -u kbis_immobilier -f
sudo tail -f /var/log/nginx/kbis_immobilier_error.log

# Mise à jour de l'application
cd /var/www/kbis_immobilier
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart kbis_immobilier
```

### Sécurité

1. **Pare-feu** : Configurez UFW pour n'autoriser que les ports nécessaires
2. **SSL** : Utilisez Let's Encrypt pour le HTTPS
3. **Mots de passe** : Utilisez des mots de passe forts et uniques
4. **Mises à jour** : Maintenez le système à jour
5. **Sauvegardes** : Configurez des sauvegardes régulières de la base de données

### Monitoring

- **Logs** : `/var/log/nginx/` et `/var/log/gunicorn/`
- **Statut des services** : `systemctl status kbis_immobilier`
- **Utilisation des ressources** : `htop` ou `top`

### Dépannage

1. **Erreur 502** : Vérifiez que Gunicorn fonctionne
2. **Erreur 500** : Consultez les logs Django
3. **Fichiers statiques** : Vérifiez la configuration Nginx
4. **Base de données** : Vérifiez la connexion PostgreSQL

### Support

Pour toute question ou problème, consultez les logs et vérifiez la configuration des services.
