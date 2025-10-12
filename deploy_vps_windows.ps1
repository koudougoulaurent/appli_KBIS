# Script de déploiement VPS pour KBIS Immobilier (Windows)
# Configuration PostgreSQL + Nginx + Gunicorn
# Version: 2025-01-27

param(
    [string]$VpsIp = "",
    [string]$Username = "root",
    [string]$Domain = ""
)

# Couleurs pour les logs
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$NC = "`e[0m"

function Write-Info {
    param([string]$Message)
    Write-Host "${Blue}[INFO]${NC} $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}[SUCCESS]${NC} $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${Yellow}[WARNING]${NC} $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "${Red}[ERROR]${NC} $Message"
}

# Vérification des paramètres
if ([string]::IsNullOrEmpty($VpsIp)) {
    $VpsIp = Read-Host "Entrez l'IP de votre VPS"
}

if ([string]::IsNullOrEmpty($Domain)) {
    $Domain = Read-Host "Entrez votre domaine (optionnel, laissez vide si pas de domaine)"
}

Write-Info "Déploiement sur VPS: $VpsIp"
if (![string]::IsNullOrEmpty($Domain)) {
    Write-Info "Domaine: $Domain"
}

# Création du script de déploiement à envoyer
$DeployScript = @"
#!/bin/bash
set -e

echo "🚀 Début du déploiement KBIS Immobilier sur VPS..."

# Variables de configuration
APP_NAME="kbis-immobilier"
APP_USER="kbis"
APP_DIR="/home/`$APP_USER/appli_KBIS"
SERVICE_NAME="kbis-immobilier"
NGINX_SITE="kbis-immobilier"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "`${BLUE}[INFO]`${NC} `$1"
}

log_success() {
    echo -e "`${GREEN}[SUCCESS]`${NC} `$1"
}

log_warning() {
    echo -e "`${YELLOW}[WARNING]`${NC} `$1"
}

log_error() {
    echo -e "`${RED}[ERROR]`${NC} `$1"
}

# Mise à jour du système
log_info "Mise à jour du système..."
apt update && apt upgrade -y

# Installation des dépendances système
log_info "Installation des dépendances système..."
apt install -y \
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

# Configuration de PostgreSQL
log_info "Configuration de PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Création de l'utilisateur et de la base de données
sudo -u postgres psql << EOF
CREATE USER `$APP_USER WITH PASSWORD 'kbis_secure_password_2025';
CREATE DATABASE kbis_immobilier OWNER `$APP_USER;
GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO `$APP_USER;
\q
EOF

# Création du répertoire de l'application
log_info "Création du répertoire de l'application..."
mkdir -p `$APP_DIR
chown `$APP_USER:`$APP_USER `$APP_DIR

# Clonage du code
log_info "Clonage du code..."
cd /tmp
git clone -b modifications-octobre-2025 https://github.com/koudougoulaurent/appli_KBIS.git
cp -r appli_KBIS/* `$APP_DIR/
chown -R `$APP_USER:`$APP_USER `$APP_DIR

# Configuration de l'application
cd `$APP_DIR
su - `$APP_USER -c "cd `$APP_DIR && python3 -m venv venv"
su - `$APP_USER -c "cd `$APP_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Configuration de l'environnement
cat > `$APP_DIR/.env << EOF
SECRET_KEY=`$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$VpsIp$(if (![string]::IsNullOrEmpty($Domain)) { ",$Domain" })
DB_NAME=kbis_immobilier
DB_USER=`$APP_USER
DB_PASSWORD=kbis_secure_password_2025
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@$VpsIp
SECURE_SSL_REDIRECT=False
EOF

# Création des répertoires nécessaires
mkdir -p `$APP_DIR/logs
mkdir -p `$APP_DIR/staticfiles
mkdir -p `$APP_DIR/media
chown -R `$APP_USER:`$APP_USER `$APP_DIR

# Configuration de Django
log_info "Configuration de Django..."
su - `$APP_USER -c "cd `$APP_DIR && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production && python manage.py collectstatic --noinput"
su - `$APP_USER -c "cd `$APP_DIR && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production && python manage.py migrate"

# Création du superutilisateur
su - `$APP_USER -c "cd `$APP_DIR && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production && echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@kbis.com', 'admin123') if not User.objects.filter(username='admin').exists() else None\" | python manage.py shell"

# Configuration de Gunicorn
mkdir -p /var/log/gunicorn
chown `$APP_USER:`$APP_USER /var/log/gunicorn

# Configuration du service systemd
cat > /etc/systemd/system/`$SERVICE_NAME.service << EOF
[Unit]
Description=KBIS Immobilier Django App
After=network.target postgresql.service

[Service]
Type=notify
User=`$APP_USER
Group=`$APP_USER
WorkingDirectory=`$APP_DIR
Environment=DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
ExecStart=`$APP_DIR/venv/bin/gunicorn --config `$APP_DIR/gunicorn.conf.py gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP `$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configuration de Nginx
cat > /etc/nginx/sites-available/`$NGINX_SITE << EOF
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias `$APP_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias `$APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
        proxy_redirect off;
    }
}
EOF

# Activation du site Nginx
ln -sf /etc/nginx/sites-available/`$NGINX_SITE /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test de la configuration Nginx
nginx -t

# Démarrage des services
log_info "Démarrage des services..."
systemctl daemon-reload
systemctl enable `$SERVICE_NAME
systemctl start `$SERVICE_NAME
systemctl restart nginx

# Configuration du pare-feu
log_info "Configuration du pare-feu..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Test de l'application
log_info "Test de l'application..."
sleep 5
if curl -f http://localhost > /dev/null 2>&1; then
    log_success "Application déployée avec succès !"
    log_info "URL: http://$VpsIp"
    log_info "Admin: http://$VpsIp/admin (admin/admin123)"
else
    log_error "Erreur lors du test de l'application"
    log_info "Vérifiez les logs: journalctl -u `$SERVICE_NAME -f"
fi

log_success "Déploiement terminé !"
"@

# Sauvegarde du script temporaire
$DeployScript | Out-File -FilePath "deploy_temp.sh" -Encoding UTF8

Write-Info "Envoi du script de déploiement vers le VPS..."

# Envoi du script vers le VPS
scp deploy_temp.sh ${Username}@${VpsIp}:/tmp/deploy_kbis.sh

Write-Info "Exécution du script de déploiement sur le VPS..."

# Exécution du script sur le VPS
ssh ${Username}@${VpsIp} "chmod +x /tmp/deploy_kbis.sh && /tmp/deploy_kbis.sh"

# Nettoyage
Remove-Item "deploy_temp.sh" -Force

Write-Success "Déploiement terminé !"
Write-Info "URL de l'application: http://$VpsIp"
Write-Info "Admin: http://$VpsIp/admin (admin/admin123)"

if (![string]::IsNullOrEmpty($Domain)) {
    Write-Info "Pour configurer HTTPS, connectez-vous au VPS et exécutez:"
    Write-Info "  certbot --nginx -d $Domain"
}
