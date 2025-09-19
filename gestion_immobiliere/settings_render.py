"""
Configuration Django pour Render.com
Base de données PostgreSQL permanente
"""
import os
from .settings import *

# Configuration de la base de données pour Render
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'kbis_production'),
        'USER': os.environ.get('DB_USER', 'kbis_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Configuration de sécurité pour la production
DEBUG = False
ALLOWED_HOSTS = [
    'appli-kbis.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Configuration des fichiers statiques pour Render
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Configuration des fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration de la sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuration des sessions
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuration des logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'gestion_immobiliere': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuration du cache (optionnel)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuration des emails (à configurer selon vos besoins)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Configuration de la base de données avec URL complète
import dj_database_url
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'])

# Configuration des fichiers statiques pour Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware pour les fichiers statiques
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
