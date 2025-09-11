"""
Configuration Django optimisée pour PythonAnywhere (plan gratuit)
Basée sur les settings de base avec optimisations pour l'hébergement gratuit
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Import des settings de base
from .settings import *

# ===========================================
# SÉCURITÉ - CONFIGURATION PRODUCTION
# ===========================================

# Désactiver le mode debug en production
DEBUG = False

# Clé secrète sécurisée (à définir via variable d'environnement)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')

# Hosts autorisés pour PythonAnywhere
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'testserver',
    # Ajouter votre domaine PythonAnywhere
    'votre-nom.pythonanywhere.com',
    'www.votre-nom.pythonanywhere.com',
    '.pythonanywhere.com',  # Sous-domaines PythonAnywhere
]

# ===========================================
# BASE DE DONNÉES - SQLITE (GRATUIT)
# ===========================================

# SQLite est parfait pour PythonAnywhere gratuit
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 30,
        },
    }
}

# ===========================================
# FICHIERS STATIQUES - WHITENOISE (ESSENTIEL)
# ===========================================

# Configuration des fichiers statiques avec WhiteNoise
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Dossiers de fichiers statiques
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuration WhiteNoise pour la compression et le cache
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration des fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===========================================
# MIDDLEWARE - AVEC WHITENOISE
# ===========================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ⭐ ESSENTIEL pour PythonAnywhere
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===========================================
# SÉCURITÉ RENFORCÉE
# ===========================================

# Configuration de sécurité pour la production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuration des cookies sécurisés
SESSION_COOKIE_SECURE = False  # HTTP sur PythonAnywhere gratuit
CSRF_COOKIE_SECURE = False     # HTTP sur PythonAnywhere gratuit
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ===========================================
# LOGGING - OPTIMISÉ POUR PYTHONANYWHERE
# ===========================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'gestion_immobiliere': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Créer le répertoire de logs s'il n'existe pas
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ===========================================
# CACHE - OPTIMISATION POUR PLAN GRATUIT
# ===========================================

# Cache simple en mémoire (suffisant pour le plan gratuit)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# ===========================================
# SESSIONS - OPTIMISATION
# ===========================================

# Configuration des sessions optimisée
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False  # Économiser les ressources

# ===========================================
# EMAIL - CONFIGURATION PYTHONANYWHERE
# ===========================================

# Configuration email pour PythonAnywhere (SMTP gratuit)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.pythonanywhere.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@pythonanywhere.com')

# ===========================================
# PERFORMANCE - OPTIMISATIONS
# ===========================================

# Désactiver les fonctionnalités coûteuses en ressources
DISABLE_SERVER_SIDE_CURSORS = True

# Optimisation des requêtes
CONN_MAX_AGE = 0  # Pas de connexions persistantes avec SQLite

# ===========================================
# TEMPLATES - OPTIMISATION
# ===========================================

# Configuration des templates avec cache
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
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

# ===========================================
# REST FRAMEWORK - CONFIGURATION
# ===========================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ===========================================
# CONFIGURATION DES MESSAGES
# ===========================================

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ===========================================
# CONFIGURATION WHITENOISE AVANCÉE
# ===========================================

# Configuration WhiteNoise pour optimiser les performances
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 31536000  # 1 an pour les fichiers statiques

# ===========================================
# CONFIGURATION DE DÉVELOPPEMENT (À DÉSACTIVER EN PRODUCTION)
# ===========================================

# Variables d'environnement pour la configuration
if os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true':
    DEBUG = True
    ALLOWED_HOSTS = ['*']  # ⚠️ DANGEREUX - seulement pour le développement

# ===========================================
# NOTES IMPORTANTES
# ===========================================

"""
CONFIGURATION PYTHONANYWHERE - NOTES IMPORTANTES :

1. WHITENOISE : Essentiel pour servir les fichiers statiques sur PythonAnywhere
2. SQLITE : Parfait pour le plan gratuit, pas besoin de PostgreSQL/MySQL
3. CACHE : Utilise la mémoire locale pour optimiser les performances
4. LOGGING : Configuration optimisée pour les logs PythonAnywhere
5. SÉCURITÉ : Configuration adaptée au plan gratuit (HTTP au lieu de HTTPS)
6. PERFORMANCE : Optimisations pour les ressources limitées du plan gratuit

COMMANDES DE DÉPLOIEMENT :
- pip3.10 install --user -r requirements_pythonanywhere.txt
- python3.10 manage.py migrate
- python3.10 manage.py collectstatic --noinput
- python3.10 manage.py createsuperuser

URLS DE CONFIGURATION PYTHONANYWHERE :
- Static files: /static/ → /home/votre-nom/votre-projet/staticfiles/
- Media files: /media/ → /home/votre-nom/votre-projet/media/
"""
