#!/bin/bash

# Script de déploiement propre pour VPS
# Application KBIS Immobilier - Version stable

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de l'application KBIS Immobilier sur VPS"
echo "=================================================="

# Variables de configuration
APP_NAME="kbis-immobilier"
APP_DIR="/var/www/$APP_NAME"
REPO_URL="https://github.com/koudougoulaurent/appli_KBIS.git"
BRANCH="modifications-octobre-2025"
SERVICE_NAME="kbis-immobilier"
NGINX_SITE="kbis-immobilier"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root (utilisez sudo)"
    exit 1
fi

# Mettre à jour le système
log_info "Mise à jour du système..."
apt update && apt upgrade -y

# Installer les dépendances système
log_info "Installation des dépendances système..."
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y mysql-server mysql-client libmysqlclient-dev
apt install -y nginx git curl wget
apt install -y build-essential libssl-dev libffi-dev

# Démarrer et activer MySQL
log_info "Configuration de MySQL..."
systemctl start mysql
systemctl enable mysql

# Sécuriser MySQL
log_info "Sécurisation de MySQL..."
mysql_secure_installation <<EOF

y
kbis_secure_password_2024!
kbis_secure_password_2024!
y
y
y
y
EOF

# Créer la base de données et l'utilisateur
log_info "Création de la base de données..."
mysql -u root -pkbis_secure_password_2024! <<EOF
CREATE DATABASE IF NOT EXISTS kbis_immobilier CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'kbis_user'@'localhost' IDENTIFIED BY 'kbis_password_2024!';
GRANT ALL PRIVILEGES ON kbis_immobilier.* TO 'kbis_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Créer le répertoire de l'application
log_info "Création du répertoire de l'application..."
mkdir -p $APP_DIR
cd $APP_DIR

# Cloner le repository
log_info "Clonage du repository..."
if [ -d ".git" ]; then
    log_info "Repository déjà existant, mise à jour..."
    git fetch origin
    git reset --hard origin/$BRANCH
else
    git clone -b $BRANCH $REPO_URL .
fi

# Créer l'environnement virtuel
log_info "Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
log_info "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements_production.txt

# Créer le fichier .env
log_info "Création du fichier de configuration..."
cat > .env <<EOF
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DB_NAME=kbis_immobilier
DB_USER=kbis_user
DB_PASSWORD=kbis_password_2024!
DB_HOST=localhost
DB_PORT=3306
DOMAIN=your-domain.com
VPS_IP=$(curl -s ifconfig.me)
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@kbis-immobilier.com
EOF

# Créer le répertoire des logs
mkdir -p logs

# Configurer Django
log_info "Configuration de Django..."
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
python manage.py collectstatic --noinput
python manage.py migrate

# Créer un superutilisateur
log_info "Création du superutilisateur..."
python manage.py shell <<EOF
from utilisateurs.models import Utilisateur
if not Utilisateur.objects.filter(username='admin').exists():
    Utilisateur.objects.create_superuser(
        username='admin',
        email='admin@kbis-immobilier.com',
        password='admin123!',
        prenom='Administrateur',
        nom='Système'
    )
    print('Superutilisateur créé: admin / admin123!')
else:
    print('Superutilisateur existe déjà')
EOF

# Créer le service systemd
log_info "Création du service systemd..."
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=KBIS Immobilier Django Application
After=network.target mysql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment=DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configurer Nginx
log_info "Configuration de Nginx..."
cat > /etc/nginx/sites-available/$NGINX_SITE <<EOF
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
        alias $APP_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
EOF

# Activer le site Nginx
ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
nginx -t

# Démarrer les services
log_info "Démarrage des services..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl restart nginx

# Vérifier le statut des services
log_info "Vérification du statut des services..."
systemctl status $SERVICE_NAME --no-pager
systemctl status nginx --no-pager

# Afficher les informations de connexion
log_info "Déploiement terminé avec succès!"
echo ""
echo "📋 Informations de connexion:"
echo "=============================="
echo "🌐 URL de l'application: http://$(curl -s ifconfig.me)"
echo "👤 Nom d'utilisateur: admin"
echo "🔑 Mot de passe: admin123!"
echo ""
echo "📊 Base de données MySQL:"
echo "   - Nom: kbis_immobilier"
echo "   - Utilisateur: kbis_user"
echo "   - Mot de passe: kbis_password_2024!"
echo ""
echo "🔧 Commandes utiles:"
echo "   - Voir les logs: journalctl -u $SERVICE_NAME -f"
echo "   - Redémarrer: systemctl restart $SERVICE_NAME"
echo "   - Statut: systemctl status $SERVICE_NAME"
echo ""
echo "✅ L'application est maintenant accessible!"
