# Guide de Déploiement VPS - Application KBIS Immobilier

## 🎯 Objectif
Déployer l'application KBIS Immobilier sur un VPS avec MySQL, Nginx et Gunicorn de manière propre et stable.

## 📋 Prérequis
- VPS Ubuntu 20.04+ ou Debian 11+
- Accès root ou sudo
- Domaine configuré (optionnel)
- Au moins 2GB RAM et 20GB d'espace disque

## 🚀 Déploiement Automatique (Recommandé)

### 1. Connexion au VPS
```bash
ssh root@votre-ip-vps
```

### 2. Téléchargement et exécution du script
```bash
# Télécharger le script de déploiement
wget https://raw.githubusercontent.com/koudougoulaurent/appli_KBIS/modifications-octobre-2025/deploy_vps_clean.sh

# Rendre le script exécutable
chmod +x deploy_vps_clean.sh

# Exécuter le déploiement
./deploy_vps_clean.sh
```

Le script va automatiquement :
- ✅ Mettre à jour le système
- ✅ Installer MySQL, Nginx, Python
- ✅ Cloner l'application
- ✅ Configurer la base de données
- ✅ Installer les dépendances
- ✅ Appliquer les migrations
- ✅ Créer un superutilisateur
- ✅ Configurer les services systemd
- ✅ Démarrer l'application

## 🔧 Déploiement Manuel (Si nécessaire)

### 1. Mise à jour du système
```bash
apt update && apt upgrade -y
```

### 2. Installation des dépendances
```bash
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y mysql-server mysql-client libmysqlclient-dev
apt install -y nginx git curl wget
apt install -y build-essential libssl-dev libffi-dev
```

### 3. Configuration de MySQL
```bash
# Démarrer MySQL
systemctl start mysql
systemctl enable mysql

# Sécuriser MySQL
mysql_secure_installation

# Créer la base de données
mysql -u root -p
```

```sql
CREATE DATABASE kbis_immobilier CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'kbis_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe_securise';
GRANT ALL PRIVILEGES ON kbis_immobilier.* TO 'kbis_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Déploiement de l'application
```bash
# Créer le répertoire
mkdir -p /var/www/kbis-immobilier
cd /var/www/kbis-immobilier

# Cloner l'application
git clone -b modifications-octobre-2025 https://github.com/koudougoulaurent/appli_KBIS.git .

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements_production.txt
```

### 5. Configuration de l'application
```bash
# Créer le fichier .env
cat > .env <<EOF
DEBUG=False
SECRET_KEY=votre_secret_key_ici
DB_NAME=kbis_immobilier
DB_USER=kbis_user
DB_PASSWORD=votre_mot_de_passe_securise
DB_HOST=localhost
DB_PORT=3306
DOMAIN=votre-domaine.com
VPS_IP=votre-ip-vps
EOF

# Créer le répertoire des logs
mkdir -p logs

# Appliquer les migrations
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Créer un superutilisateur
python manage.py createsuperuser
```

### 6. Configuration de Gunicorn
```bash
# Créer le service systemd
cat > /etc/systemd/system/kbis-immobilier.service <<EOF
[Unit]
Description=KBIS Immobilier Django Application
After=network.target mysql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/kbis-immobilier
Environment=DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
ExecStart=/var/www/kbis-immobilier/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Démarrer le service
systemctl daemon-reload
systemctl enable kbis-immobilier
systemctl start kbis-immobilier
```

### 7. Configuration de Nginx
```bash
# Créer la configuration du site
cat > /etc/nginx/sites-available/kbis-immobilier <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static/ {
        alias /var/www/kbis-immobilier/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/kbis-immobilier/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
EOF

# Activer le site
ln -s /etc/nginx/sites-available/kbis-immobilier /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester et redémarrer Nginx
nginx -t
systemctl restart nginx
```

## 🔍 Vérification du Déploiement

### 1. Vérifier les services
```bash
# Statut de l'application
systemctl status kbis-immobilier

# Statut de Nginx
systemctl status nginx

# Statut de MySQL
systemctl status mysql
```

### 2. Vérifier les logs
```bash
# Logs de l'application
journalctl -u kbis-immobilier -f

# Logs de Nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### 3. Tester l'application
```bash
# Test de connectivité
curl -I http://localhost

# Test de la base de données
mysql -u kbis_user -p kbis_immobilier -e "SELECT COUNT(*) FROM auth_user;"
```

## 🔐 Configuration HTTPS (Optionnel)

### 1. Installer Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 2. Obtenir un certificat SSL
```bash
certbot --nginx -d votre-domaine.com
```

### 3. Configurer le renouvellement automatique
```bash
crontab -e
# Ajouter cette ligne :
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring et Maintenance

### 1. Commandes utiles
```bash
# Redémarrer l'application
systemctl restart kbis-immobilier

# Voir les logs en temps réel
journalctl -u kbis-immobilier -f

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les processus
ps aux | grep gunicorn
```

### 2. Sauvegarde de la base de données
```bash
# Créer un script de sauvegarde
cat > /root/backup_db.sh <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
mysqldump -u kbis_user -p kbis_immobilier > /root/backup_kbis_\$DATE.sql
gzip /root/backup_kbis_\$DATE.sql
find /root -name "backup_kbis_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /root/backup_db.sh

# Programmer la sauvegarde quotidienne
crontab -e
# Ajouter : 0 2 * * * /root/backup_db.sh
```

## 🚨 Dépannage

### Problèmes courants

#### 1. Erreur 502 Bad Gateway
```bash
# Vérifier que Gunicorn fonctionne
systemctl status kbis-immobilier

# Vérifier les logs
journalctl -u kbis-immobilier -n 50

# Redémarrer le service
systemctl restart kbis-immobilier
```

#### 2. Erreur de base de données
```bash
# Vérifier la connexion MySQL
mysql -u kbis_user -p kbis_immobilier

# Vérifier les migrations
cd /var/www/kbis-immobilier
source venv/bin/activate
python manage.py showmigrations
```

#### 3. Problème de permissions
```bash
# Corriger les permissions
chown -R www-data:www-data /var/www/kbis-immobilier
chmod -R 755 /var/www/kbis-immobilier
```

## 📞 Support

En cas de problème :
1. Vérifiez les logs : `journalctl -u kbis-immobilier -f`
2. Vérifiez la configuration : `nginx -t`
3. Vérifiez la base de données : `systemctl status mysql`
4. Consultez ce guide ou contactez le support

## ✅ Checklist de Déploiement

- [ ] VPS configuré et accessible
- [ ] MySQL installé et configuré
- [ ] Application clonée et configurée
- [ ] Base de données créée et migrée
- [ ] Gunicorn configuré et démarré
- [ ] Nginx configuré et démarré
- [ ] Application accessible via HTTP
- [ ] Superutilisateur créé
- [ ] HTTPS configuré (optionnel)
- [ ] Monitoring configuré
- [ ] Sauvegardes programmées

---

**🎉 Félicitations ! Votre application KBIS Immobilier est maintenant déployée et fonctionnelle sur votre VPS !**
