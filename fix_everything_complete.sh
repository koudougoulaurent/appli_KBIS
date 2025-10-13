#!/bin/bash

# =============================================================================
# SCRIPT COMPLET DE CORRECTION - KBIS IMMOBILIER
# =============================================================================
# Ce script corrige TOUS les problèmes connus :
# - Références gestimmob
# - Settings incorrects
# - Configuration Gunicorn
# - Configuration Nginx
# - Permissions
# - Services
# =============================================================================

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🚀 SCRIPT COMPLET DE CORRECTION - KBIS IMMOBILIER${NC}"
echo -e "${BLUE}=============================================================================${NC}"

# =============================================================================
# PHASE 1: ARRÊT DES SERVICES
# =============================================================================
echo -e "\n${YELLOW}🛑 PHASE 1: ARRÊT DES SERVICES${NC}"
echo "=========================================="

echo -e "${YELLOW}Arrêt de Gunicorn...${NC}"
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

echo -e "${YELLOW}Arrêt de Nginx...${NC}"
sudo systemctl stop nginx 2>/dev/null || true

# =============================================================================
# PHASE 2: CORRECTION DES RÉFÉRENCES GESTIMMOB
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 2: CORRECTION DES RÉFÉRENCES GESTIMMOB${NC}"
echo "======================================================"

cd $APP_DIR || { echo -e "${RED}❌ Impossible d'accéder au répertoire $APP_DIR${NC}"; exit 1; }

echo -e "${YELLOW}Recherche des références gestimmob...${NC}"
grep -r "gestimmob" . --exclude-dir=venv --exclude-dir=.git --exclude="*.log" || echo "Aucune référence gestimmob trouvée"

echo -e "${YELLOW}Correction des fichiers principaux...${NC}"

# Corriger wsgi.py
if [ -f "gestion_immobiliere/wsgi.py" ]; then
    echo "Correction de wsgi.py..."
    sed -i 's/gestimmob/gestion_immobiliere/g' gestion_immobiliere/wsgi.py
    sed -i 's/settings_simple/settings/g' gestion_immobiliere/wsgi.py
    sed -i 's/settings_production/settings/g' gestion_immobiliere/wsgi.py
fi

# Corriger asgi.py
if [ -f "gestion_immobiliere/asgi.py" ]; then
    echo "Correction de asgi.py..."
    sed -i 's/gestimmob/gestion_immobiliere/g' gestion_immobiliere/asgi.py
    sed -i 's/settings_simple/settings/g' gestion_immobiliere/asgi.py
    sed -i 's/settings_production/settings/g' gestion_immobiliere/asgi.py
fi

# Corriger manage.py
if [ -f "manage.py" ]; then
    echo "Correction de manage.py..."
    sed -i 's/gestimmob/gestion_immobiliere/g' manage.py
    sed -i 's/settings_simple/settings/g' manage.py
    sed -i 's/settings_production/settings/g' manage.py
fi

# Corriger settings.py
if [ -f "gestion_immobiliere/settings.py" ]; then
    echo "Correction de settings.py..."
    sed -i 's/gestimmob/gestion_immobiliere/g' gestion_immobiliere/settings.py
fi

# Corriger tous les fichiers Python
echo "Correction de tous les fichiers Python..."
find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" -exec sed -i 's/gestimmob/gestion_immobiliere/g' {} \;

echo -e "${GREEN}✅ Corrections des références terminées${NC}"

# =============================================================================
# PHASE 3: VÉRIFICATION ET CORRECTION DU FICHIER .ENV
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 3: VÉRIFICATION DU FICHIER .ENV${NC}"
echo "=============================================="

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Création du fichier .env...${NC}"
    cat > .env << 'EOF'
DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings
DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production
DB_NAME=kbis_immobilier
DB_USER=kbis_user
DB_PASSWORD=kbis_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,78.138.58.185,127.0.0.1
EOF
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
else
    echo -e "${GREEN}✅ Fichier .env existe${NC}"
fi

# =============================================================================
# PHASE 4: CORRECTION DU FICHIER SETTINGS.PY
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 4: CORRECTION DU FICHIER SETTINGS.PY${NC}"
echo "=================================================="

# Créer un settings.py propre
cat > gestion_immobiliere/settings.py << 'EOF'
"""
Django settings for gestion_immobiliere project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'proprietes',
    'contrats',
    'paiements',
    'utilisateurs',
    'core',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_immobiliere.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_immobiliere.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'kbis_immobilier'),
        'USER': os.getenv('DB_USER', 'kbis_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'kbis_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/tableau-bord/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
EOF

echo -e "${GREEN}✅ Settings.py corrigé${NC}"

# =============================================================================
# PHASE 5: INSTALLATION DES DÉPENDANCES MANQUANTES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 5: INSTALLATION DES DÉPENDANCES${NC}"
echo "============================================="

source venv/bin/activate

echo -e "${YELLOW}Installation des dépendances manquantes...${NC}"
pip install python-dotenv psycopg2-binary openpyxl reportlab

echo -e "${GREEN}✅ Dépendances installées${NC}"

# =============================================================================
# PHASE 6: VÉRIFICATION DJANGO
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 6: VÉRIFICATION DJANGO${NC}"
echo "====================================="

echo -e "${YELLOW}Test de Django...${NC}"
python3 manage.py check

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Django fonctionne correctement${NC}"
else
    echo -e "${RED}❌ Erreur Django - Vérifiez les logs${NC}"
fi

# =============================================================================
# PHASE 7: COLLECTE DES FICHIERS STATIQUES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 7: COLLECTE DES FICHIERS STATIQUES${NC}"
echo "=================================================="

echo -e "${YELLOW}Collecte des fichiers statiques...${NC}"
python3 manage.py collectstatic --noinput

echo -e "${GREEN}✅ Fichiers statiques collectés${NC}"

# =============================================================================
# PHASE 8: CORRECTION DU SERVICE SYSTEMD
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 8: CORRECTION DU SERVICE SYSTEMD${NC}"
echo "==============================================="

echo -e "${YELLOW}Création du service systemd...${NC}"
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=KBIS Immobilier Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service systemd créé${NC}"

# =============================================================================
# PHASE 9: CORRECTION DE LA CONFIGURATION NGINX
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 9: CORRECTION DE LA CONFIGURATION NGINX${NC}"
echo "======================================================="

echo -e "${YELLOW}Suppression des anciennes configurations...${NC}"
sudo rm -f /etc/nginx/sites-enabled/*
sudo rm -f /etc/nginx/sites-available/kbis_immobilier*

echo -e "${YELLOW}Création de la nouvelle configuration Nginx...${NC}"
sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null << 'EOF'
server {
    listen 80;
    server_name localhost 78.138.58.185;

    # Augmenter la limite de taille des requêtes
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        alias /var/www/kbis_immobilier/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/kbis_immobilier/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo -e "${YELLOW}Activation de la configuration...${NC}"
sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/

echo -e "${GREEN}✅ Configuration Nginx créée${NC}"

# =============================================================================
# PHASE 10: CORRECTION DES PERMISSIONS
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 10: CORRECTION DES PERMISSIONS${NC}"
echo "=============================================="

echo -e "${YELLOW}Correction des permissions...${NC}"
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod +x $APP_DIR/venv/bin/gunicorn

echo -e "${GREEN}✅ Permissions corrigées${NC}"

# =============================================================================
# PHASE 11: RECHARGEMENT ET DÉMARRAGE DES SERVICES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 11: RECHARGEMENT ET DÉMARRAGE${NC}"
echo "============================================="

echo -e "${YELLOW}Rechargement de systemd...${NC}"
sudo systemctl daemon-reload

echo -e "${YELLOW}Démarrage de Gunicorn...${NC}"
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo -e "${YELLOW}Démarrage de Nginx...${NC}"
sudo systemctl enable nginx
sudo systemctl start nginx

echo -e "${GREEN}✅ Services démarrés${NC}"

# =============================================================================
# PHASE 12: VÉRIFICATIONS FINALES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 12: VÉRIFICATIONS FINALES${NC}"
echo "====================================="

echo -e "${YELLOW}Vérification du statut des services...${NC}"
sudo systemctl status $SERVICE_NAME --no-pager -l
echo ""
sudo systemctl status nginx --no-pager -l

echo -e "\n${YELLOW}Test de connectivité...${NC}"
sleep 5

# Test Gunicorn
if curl -I http://127.0.0.1:8000 2>/dev/null | grep -q "HTTP"; then
    echo -e "${GREEN}✅ Gunicorn répond sur le port 8000${NC}"
else
    echo -e "${RED}❌ Gunicorn ne répond pas${NC}"
    echo -e "${YELLOW}Logs Gunicorn:${NC}"
    sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
fi

# Test Nginx
if curl -I http://78.138.58.185 2>/dev/null | grep -q "HTTP"; then
    echo -e "${GREEN}✅ Nginx répond correctement${NC}"
else
    echo -e "${RED}❌ Nginx ne répond pas${NC}"
    echo -e "${YELLOW}Logs Nginx:${NC}"
    sudo tail -5 /var/log/nginx/error.log
fi

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================
echo -e "\n${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🎉 SCRIPT DE CORRECTION TERMINÉ${NC}"
echo -e "${BLUE}=============================================================================${NC}"

echo -e "\n${GREEN}✅ Corrections effectuées :${NC}"
echo "  - Références gestimmob corrigées"
echo "  - Fichier .env créé/vérifié"
echo "  - Settings.py nettoyé"
echo "  - Dépendances installées"
echo "  - Service systemd configuré"
echo "  - Configuration Nginx créée"
echo "  - Permissions corrigées"
echo "  - Services redémarrés"

echo -e "\n${YELLOW}🔗 URLs d'accès :${NC}"
echo "  - Application : http://78.138.58.185"
echo "  - Admin : http://78.138.58.185/admin/"

echo -e "\n${YELLOW}📋 Commandes utiles :${NC}"
echo "  - Logs Gunicorn : sudo journalctl -u $SERVICE_NAME -f"
echo "  - Logs Nginx : sudo tail -f /var/log/nginx/error.log"
echo "  - Status services : sudo systemctl status $SERVICE_NAME nginx"

echo -e "\n${BLUE}=============================================================================${NC}"





