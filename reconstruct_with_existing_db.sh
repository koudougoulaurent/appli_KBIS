#!/bin/bash

# ========================================
# SCRIPT DE RECONSTRUCTION COMPLÈTE
# AVEC BASE POSTGRESQL EXISTANTE
# ========================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔥 RECONSTRUCTION AVEC BASE POSTGRESQL EXISTANTE${NC}"
echo -e "${BLUE}================================================${NC}"

# ========================================
# ÉTAPE 1: ARRÊTER TOUS LES SERVICES
# ========================================
echo -e "\n${YELLOW}🛑 ARRÊT DES SERVICES...${NC}"
sudo systemctl stop kbis_immobilier 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# ========================================
# ÉTAPE 2: VÉRIFIER LA BASE EXISTANTE
# ========================================
echo -e "\n${YELLOW}🔍 VÉRIFICATION DE LA BASE EXISTANTE...${NC}"
sudo -u postgres psql -c "SELECT datname FROM pg_database WHERE datname = 'kbis_productiondb';" | grep -q kbis_productiondb && echo -e "${GREEN}✅ Base kbis_productiondb trouvée${NC}" || echo -e "${RED}❌ Base kbis_productiondb introuvable${NC}"

# ========================================
# ÉTAPE 3: CONFIGURER DJANGO POUR POSTGRESQL
# ========================================
echo -e "\n${YELLOW}⚙️ CONFIGURATION DJANGO POUR POSTGRESQL...${NC}"

# Créer le fichier settings.py avec PostgreSQL
cat > gestion_immobiliere/settings.py << 'EOF'
"""
Configuration Django pour l'application KBIS Immobilier
Version: Production avec PostgreSQL
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'utilisateurs',
    'proprietes',
    'contrats',
    'paiements',
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
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kbis_productiondb',
        'USER': 'kbis_prod_user',
        'PASSWORD': 'kbis_prod_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = '/utilisateurs/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email configuration (pour les notifications)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'root': {
        'handlers': ['file'],
    },
}
EOF

# ========================================
# ÉTAPE 4: INSTALLER LES DÉPENDANCES
# ========================================
echo -e "\n${YELLOW}📦 INSTALLATION DES DÉPENDANCES...${NC}"
pip install psycopg2-binary
pip install -r requirements.txt

# ========================================
# ÉTAPE 5: NETTOYER LES MIGRATIONS PROBLÉMATIQUES
# ========================================
echo -e "\n${YELLOW}🧹 NETTOYAGE DES MIGRATIONS PROBLÉMATIQUES...${NC}"
# Supprimer les migrations qui causent des problèmes
rm -f paiements/migrations/0013_chargebailleur_remove_alertepaiementpartiel_cree_par_and_more.py 2>/dev/null || true

# ========================================
# ÉTAPE 6: CRÉER LES MIGRATIONS
# ========================================
echo -e "\n${YELLOW}🔄 CRÉATION DES MIGRATIONS...${NC}"
python3 manage.py makemigrations

# ========================================
# ÉTAPE 7: APPLIQUER LES MIGRATIONS
# ========================================
echo -e "\n${YELLOW}🔄 APPLICATION DES MIGRATIONS...${NC}"
python3 manage.py migrate

# ========================================
# ÉTAPE 8: CRÉER UN SUPERUTILISATEUR (si nécessaire)
# ========================================
echo -e "\n${YELLOW}👤 VÉRIFICATION DU SUPERUTILISATEUR...${NC}"
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@kbis.com', 'admin123')
    print('Superutilisateur créé')
else:
    print('Superutilisateur existe déjà')
"

# ========================================
# ÉTAPE 9: COLLECTER LES FICHIERS STATIQUES
# ========================================
echo -e "\n${YELLOW}📁 COLLECTE DES FICHIERS STATIQUES...${NC}"
python3 manage.py collectstatic --noinput

# ========================================
# ÉTAPE 10: CONFIGURER NGINX
# ========================================
echo -e "\n${YELLOW}🌐 CONFIGURATION NGINX...${NC}"
sudo tee /etc/nginx/sites-available/kbis_immobilier << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/kbis_immobilier/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/kbis_immobilier/media/;
    }
}
EOF

# Activer le site
sudo ln -sf /etc/nginx/sites-available/kbis_immobilier /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# ========================================
# ÉTAPE 11: CONFIGURER GUNICORN
# ========================================
echo -e "\n${YELLOW}🚀 CONFIGURATION GUNICORN...${NC}"
sudo tee /etc/systemd/system/kbis_immobilier.service << 'EOF'
[Unit]
Description=KBIS Immobilier Django App
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/kbis_immobilier
Environment=PATH=/var/www/kbis_immobilier/venv/bin
ExecStart=/var/www/kbis_immobilier/venv/bin/gunicorn --bind 127.0.0.1:8000 gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# ========================================
# ÉTAPE 12: DÉMARRER LES SERVICES
# ========================================
echo -e "\n${YELLOW}🚀 DÉMARRAGE DES SERVICES...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable kbis_immobilier
sudo systemctl start kbis_immobilier
sudo systemctl start nginx

# ========================================
# ÉTAPE 13: VÉRIFICATION
# ========================================
echo -e "\n${YELLOW}🔍 VÉRIFICATION...${NC}"
sleep 5

# Vérifier les services
echo -e "\n${BLUE}📊 STATUT DES SERVICES:${NC}"
sudo systemctl status kbis_immobilier --no-pager -l
sudo systemctl status nginx --no-pager -l

# Vérifier la base de données
echo -e "\n${BLUE}🗄️ VÉRIFICATION DE LA BASE:${NC}"
python3 manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT version();'); print(f'PostgreSQL: {cursor.fetchone()[0]}')"

# Vérifier l'application
echo -e "\n${BLUE}🌐 VÉRIFICATION DE L'APPLICATION:${NC}"
curl -I http://127.0.0.1:8000 2>/dev/null && echo -e "${GREEN}✅ Application accessible${NC}" || echo -e "${RED}❌ Application inaccessible${NC}"

echo -e "\n${GREEN}🎉 RECONSTRUCTION TERMINÉE !${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Base PostgreSQL: kbis_productiondb (existante)${NC}"
echo -e "${GREEN}✅ Utilisateur: kbis_prod_user${NC}"
echo -e "${GREEN}✅ Application: http://127.0.0.1:8000${NC}"
echo -e "${GREEN}✅ Admin: http://127.0.0.1:8000/admin/${NC}"
echo -e "${GREEN}✅ Identifiants admin: admin / admin123${NC}"





