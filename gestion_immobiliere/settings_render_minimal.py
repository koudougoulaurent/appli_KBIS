# Configuration minimale pour Render - SANS modifier l'application
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration de base
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-minimal-key-for-render')
DEBUG = False
ALLOWED_HOSTS = ['*']

# Applications - EXACTEMENT comme dans settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    'core',
    'utilisateurs',
    'proprietes',
    'contrats',
    'paiements',
    'notifications',
]

# Middleware - EXACTEMENT comme dans settings.py
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

# URLs
ROOT_URLCONF = 'gestion_immobiliere.urls'

# Templates - EXACTEMENT comme dans settings.py
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
                'core.context_processors.dynamic_navigation',
            ],
        },
    },
]

# Base de données SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration de base
WSGI_APPLICATION = 'gestion_immobiliere.wsgi.application'
AUTH_USER_MODEL = 'utilisateurs.Utilisateur'
LOGIN_URL = '/utilisateurs/connexion-groupes/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/utilisateurs/connexion-groupes/'

# Langue
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Utiliser le storage par défaut pour éviter les problèmes avec l'admin
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Média
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration crispy_forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuration admin Django
ADMIN_SITE_HEADER = "KBIS IMMOBILIER - Administration"
ADMIN_SITE_TITLE = "KBIS Admin"
ADMIN_INDEX_TITLE = "Administration du système"

# Désactiver les migrations
MIGRATION_MODULES = {
    'core': None,
    'utilisateurs': None,
    'proprietes': None,
    'contrats': None,
    'paiements': None,
    'notifications': None,
}

# Logging simple
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
