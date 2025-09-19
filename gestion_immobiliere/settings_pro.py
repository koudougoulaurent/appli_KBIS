"""
Configuration Django pour Render Pro (100 GB)
Base de données PostgreSQL avec capacité de stockage élevée
"""
import os
from .settings import *

# Configuration de la base de données PostgreSQL Pro
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'kbis_production'),
        'USER': os.environ.get('DB_USER', 'kbis_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'charset': 'utf8',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 300,  # Connexions persistantes (5 minutes)
        'CONN_HEALTH_CHECKS': True,  # Vérification de santé des connexions
        'ATOMIC_REQUESTS': True,  # Transactions atomiques
    }
}

# Configuration de la base de données avec URL complète (Render Pro)
import dj_database_url
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.parse(
        os.environ['DATABASE_URL'],
        conn_max_age=300,
        conn_health_checks=True,
    )

# Configuration de sécurité pour la production
DEBUG = False
ALLOWED_HOSTS = [
    'appli-kbis.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Configuration des fichiers statiques
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
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuration des sessions
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_SAVE_EVERY_REQUEST = True

# Configuration des logs avancés
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
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'gestion_immobiliere': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configuration du cache Redis (optionnel pour Render Pro)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Configuration des emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@kbis.com')

# Configuration des fichiers statiques pour Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware pour les fichiers statiques
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configuration de la base de données pour les tests
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

# Configuration des migrations
MIGRATION_MODULES = {
    'utilisateurs': 'utilisateurs.migrations',
    'proprietes': 'proprietes.migrations',
    'contrats': 'contrats.migrations',
    'paiements': 'paiements.migrations',
    'core': 'core.migrations',
    'notifications': 'notifications.migrations',
}

# Configuration de la base de données pour la migration
DATABASE_ROUTERS = ['gestion_immobiliere.db_router.DatabaseRouter']

# Configuration des performances
DATABASES['default']['OPTIONS'].update({
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'charset': 'utf8mb4',
})

# Configuration des connexions
DATABASES['default']['CONN_MAX_AGE'] = 300
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
DATABASES['default']['ATOMIC_REQUESTS'] = True

# Configuration des requêtes
DATABASES['default']['OPTIONS']['init_command'] = "SET sql_mode='STRICT_TRANS_TABLES'"

# Configuration des logs de base de données
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['file'],
    'level': 'DEBUG',
    'propagate': False,
}

# Configuration des performances
DATABASES['default']['OPTIONS'].update({
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'charset': 'utf8mb4',
})

# Configuration des connexions
DATABASES['default']['CONN_MAX_AGE'] = 300
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
DATABASES['default']['ATOMIC_REQUESTS'] = True

# Configuration des requêtes
DATABASES['default']['OPTIONS']['init_command'] = "SET sql_mode='STRICT_TRANS_TABLES'"

# Configuration des logs de base de données
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['file'],
    'level': 'DEBUG',
    'propagate': False,
}
