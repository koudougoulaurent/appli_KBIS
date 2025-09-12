#!/bin/bash
# Script de déploiement automatique sur VPS LWS
# Usage: ./deploy_vps_lws.sh

echo "🚀 Déploiement de l'application Django sur VPS LWS"
echo "=================================================="

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./deploy_vps_lws.sh"
    exit 1
fi

echo "✅ Privilèges administrateur confirmés"

# Mise à jour du système
echo "📦 Mise à jour du système..."
apt update && apt upgrade -y

# Installation des dépendances de base
echo "🔧 Installation des dépendances..."
apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib nginx git curl wget htop

# Installation de Node.js pour les assets
echo "📦 Installation de Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Configuration de PostgreSQL
echo "🗄️ Configuration de PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Créer la base de données et l'utilisateur
sudo -u postgres psql -c "CREATE DATABASE gestimmob_db;"
sudo -u postgres psql -c "CREATE USER gestimmob_user WITH PASSWORD 'gestimmob_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gestimmob_db TO gestimmob_user;"
sudo -u postgres psql -c "ALTER USER gestimmob_user CREATEDB;"

echo "✅ Base de données PostgreSQL configurée"

# Créer l'utilisateur pour l'application
echo "👤 Création de l'utilisateur application..."
useradd -m -s /bin/bash gestimmob
usermod -aG www-data gestimmob

# Créer le répertoire de l'application
echo "📁 Création du répertoire application..."
mkdir -p /home/gestimmob/appli_KBIS
chown gestimmob:gestimmob /home/gestimmob/appli_KBIS

# Cloner le code (si disponible via Git)
echo "📥 Clonage du code..."
cd /home/gestimmob
if [ -d "appli_KBIS" ]; then
    echo "   Le répertoire existe déjà, mise à jour..."
    cd appli_KBIS
    git pull origin master
else
    echo "   Clonage du repository..."
    git clone https://github.com/koudougoulaurent/appli_KBIS.git
    cd appli_KBIS
fi

# Créer l'environnement virtuel
echo "🐍 Création de l'environnement virtuel..."
python3 -m venv venv
chown -R gestimmob:gestimmob venv

# Activer l'environnement virtuel et installer les dépendances
echo "📦 Installation des dépendances Python..."
sudo -u gestimmob bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u gestimmob bash -c "source venv/bin/activate && pip install -r requirements_production.txt"
sudo -u gestimmob bash -c "source venv/bin/activate && pip install gunicorn psycopg2-binary"

# Configuration de la base de données dans settings
echo "⚙️ Configuration de la base de données..."
cat > /home/gestimmob/appli_KBIS/gestion_immobiliere/settings_vps.py << 'EOF'
"""
Configuration Django pour VPS LWS
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ics4n+vw1)3tlekunwt5b%(05ug)s&%*h-z&bmw1$_pd11_9nd')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'votre-domaine.com',
    'www.votre-domaine.com',
    os.environ.get('SERVER_IP', ''),
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'whitenoise.runserver_nostatic',
    'core',
    'utilisateurs',
    'proprietes',
    'contrats',
    'paiements',
    'notifications',
    'bailleurs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                'core.context_processors.entreprise_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_immobiliere.wsgi.application'

# Base de données PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gestimmob_db',
        'USER': 'gestimmob_user',
        'PASSWORD': 'gestimmob_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Fichiers statiques
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# Modèle utilisateur
AUTH_USER_MODEL = 'utilisateurs.Utilisateur'

# Configuration crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuration REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Configuration des messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_vps.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Créer le répertoire de logs
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
EOF

# Migrations de la base de données
echo "🗄️ Exécution des migrations..."
sudo -u gestimmob bash -c "cd /home/gestimmob/appli_KBIS && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py makemigrations"
sudo -u gestimmob bash -c "cd /home/gestimmob/appli_KBIS && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py migrate"

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
sudo -u gestimmob bash -c "cd /home/gestimmob/appli_KBIS && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py collectstatic --noinput"

# Création du superutilisateur
echo "👤 Création du superutilisateur..."
sudo -u gestimmob bash -c "cd /home/gestimmob/appli_KBIS && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && echo 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\"admin\", \"admin@example.com\", \"admin123\") if not User.objects.filter(username=\"admin\").exists() else None' | python manage.py shell"

# Configuration de Gunicorn
echo "🔧 Configuration de Gunicorn..."
cat > /etc/systemd/system/gestimmob.service << 'EOF'
[Unit]
Description=Gunicorn instance to serve gestimmob
After=network.target

[Service]
User=gestimmob
Group=www-data
WorkingDirectory=/home/gestimmob/appli_KBIS
Environment="PATH=/home/gestimmob/appli_KBIS/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps"
ExecStart=/home/gestimmob/appli_KBIS/venv/bin/gunicorn --workers 3 --bind unix:/home/gestimmob/appli_KBIS/gestimmob.sock gestion_immobiliere.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Démarrer le service Gunicorn
echo "🚀 Démarrage du service Gunicorn..."
systemctl daemon-reload
systemctl start gestimmob
systemctl enable gestimmob

# Configuration de Nginx
echo "🌐 Configuration de Nginx..."
cat > /etc/nginx/sites-available/gestimmob << 'EOF'
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/gestimmob/appli_KBIS;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        root /home/gestimmob/appli_KBIS;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/gestimmob/appli_KBIS/gestimmob.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/gestimmob /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test de la configuration Nginx
nginx -t

# Redémarrer Nginx
systemctl restart nginx
systemctl enable nginx

# Configuration du firewall
echo "🔒 Configuration du firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# Vérification des services
echo "✅ Vérification des services..."
systemctl status gestimmob --no-pager
systemctl status nginx --no-pager
systemctl status postgresql --no-pager

echo ""
echo "🎉 Déploiement VPS terminé avec succès !"
echo "=================================================="
echo ""
echo "📝 Informations importantes :"
echo "   - Application: http://votre-ip-serveur"
echo "   - Admin: http://votre-ip-serveur/admin/"
echo "   - Utilisateur: admin"
echo "   - Mot de passe: admin123"
echo ""
echo "🔧 Prochaines étapes :"
echo "   1. Configurez votre domaine dans Nginx"
echo "   2. Installez SSL avec Let's Encrypt"
echo "   3. Changez le mot de passe admin"
echo "   4. Configurez les sauvegardes"
echo ""
echo "📊 Commandes utiles :"
echo "   - Logs app: sudo journalctl -u gestimmob -f"
echo "   - Logs nginx: sudo tail -f /var/log/nginx/error.log"
echo "   - Redémarrer: sudo systemctl restart gestimmob"
echo ""
echo "✅ Votre application Django est maintenant en ligne sur le VPS !"





