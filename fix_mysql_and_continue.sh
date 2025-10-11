#!/bin/bash

# Script pour corriger MySQL et continuer le nettoyage
# Puis déployer la nouvelle version propre

set -e  # Arrêter en cas d'erreur

echo "🔧 Correction MySQL et déploiement propre"
echo "========================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[ÉTAPE]${NC} $1"
}

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root (utilisez sudo)"
    exit 1
fi

log_step "1. Vérification de l'état du système"
echo "====================================="

# Vérifier l'état actuel
log_info "Vérification de l'état du système..."

# Vérifier Nginx
if systemctl is-active --quiet nginx; then
    log_info "✅ Nginx est actif"
else
    log_warn "⚠️  Nginx n'est pas actif"
fi

# Vérifier MySQL
if systemctl is-active --quiet mysql; then
    log_info "✅ MySQL est actif"
elif systemctl is-active --quiet mariadb; then
    log_info "✅ MariaDB est actif (utiliser MariaDB)"
else
    log_warn "⚠️  MySQL/MariaDB n'est pas installé ou actif"
fi

log_step "2. Installation et configuration de MySQL"
echo "==========================================="

# Installer MySQL si nécessaire
if ! command -v mysql &> /dev/null; then
    log_info "Installation de MySQL..."
    apt update
    apt install -y mysql-server mysql-client libmysqlclient-dev
else
    log_info "MySQL est déjà installé"
fi

# Démarrer et activer MySQL
log_info "Démarrage de MySQL..."
systemctl start mysql
systemctl enable mysql

# Attendre que MySQL soit prêt
sleep 5

# Vérifier que MySQL fonctionne
if systemctl is-active --quiet mysql; then
    log_info "✅ MySQL est maintenant actif"
else
    log_error "❌ Impossible de démarrer MySQL"
    exit 1
fi

log_step "3. Configuration sécurisée de MySQL"
echo "===================================="

# Sécuriser MySQL
log_info "Configuration sécurisée de MySQL..."
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'kbis_root_password_2024!';" 2>/dev/null || log_warn "Utilisateur root déjà configuré"

# Créer la base de données et l'utilisateur
log_info "Création de la base de données et de l'utilisateur..."
mysql -u root -pkbis_root_password_2024! <<EOF
CREATE DATABASE IF NOT EXISTS kbis_immobilier CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'kbis_user'@'localhost' IDENTIFIED BY 'kbis_password_2024!';
GRANT ALL PRIVILEGES ON kbis_immobilier.* TO 'kbis_user'@'localhost';
FLUSH PRIVILEGES;
EOF

log_info "✅ Base de données et utilisateur créés"

log_step "4. Vérification du nettoyage précédent"
echo "======================================="

# Vérifier que l'ancienne application est bien supprimée
if [ -d "/var/www/kbis-immobilier" ]; then
    log_warn "L'ancienne application existe encore, suppression..."
    rm -rf /var/www/kbis-immobilier
fi

if [ -d "/var/www/appli_KBIS" ]; then
    log_warn "L'ancienne application existe encore, suppression..."
    rm -rf /var/www/appli_KBIS
fi

log_info "✅ Ancienne application supprimée"

log_step "5. Déploiement de la nouvelle version"
echo "======================================"

# Créer le répertoire de l'application
log_info "Création du répertoire de l'application..."
mkdir -p /var/www/kbis-immobilier
cd /var/www/kbis-immobilier

# Cloner la nouvelle version
log_info "Clonage de la nouvelle version..."
git clone -b modifications-octobre-2025 https://github.com/koudougoulaurent/appli_KBIS.git .

log_step "6. Configuration de l'environnement Python"
echo "==========================================="

# Créer l'environnement virtuel
log_info "Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
log_info "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements_production.txt

log_step "7. Configuration de l'application"
echo "=================================="

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
DOMAIN=$(curl -s ifconfig.me)
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

log_step "8. Configuration de Django"
echo "============================"

# Configurer Django
log_info "Configuration de Django..."
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production

# Appliquer les migrations
log_info "Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

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

log_step "9. Configuration de Gunicorn"
echo "============================="

# Créer le service systemd
log_info "Création du service systemd..."
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

# Configurer les permissions
chown -R www-data:www-data /var/www/kbis-immobilier
chmod -R 755 /var/www/kbis-immobilier

log_step "10. Configuration de Nginx"
echo "============================"

# Configurer Nginx
log_info "Configuration de Nginx..."
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
ln -sf /etc/nginx/sites-available/kbis-immobilier /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
nginx -t

log_step "11. Démarrage des services"
echo "==========================="

# Démarrer les services
log_info "Démarrage des services..."
systemctl daemon-reload
systemctl enable kbis-immobilier
systemctl start kbis-immobilier
systemctl restart nginx

# Attendre que les services démarrent
sleep 10

log_step "12. Vérification finale"
echo "========================"

# Vérifier le statut des services
log_info "Vérification du statut des services..."

if systemctl is-active --quiet kbis-immobilier; then
    log_info "✅ Service kbis-immobilier actif"
else
    log_error "❌ Service kbis-immobilier non actif"
    systemctl status kbis-immobilier --no-pager
fi

if systemctl is-active --quiet nginx; then
    log_info "✅ Nginx actif"
else
    log_error "❌ Nginx non actif"
    systemctl status nginx --no-pager
fi

if systemctl is-active --quiet mysql; then
    log_info "✅ MySQL actif"
else
    log_error "❌ MySQL non actif"
    systemctl status mysql --no-pager
fi

# Tester l'application
log_info "Test de l'application..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
    log_info "✅ Application accessible"
else
    log_warn "⚠️  Application non accessible, vérifiez les logs"
fi

log_info "🎉 Déploiement terminé!"
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
echo "   - Voir les logs: journalctl -u kbis-immobilier -f"
echo "   - Redémarrer: systemctl restart kbis-immobilier"
echo "   - Statut: systemctl status kbis-immobilier"
echo ""
echo "✅ L'application est maintenant accessible!"
