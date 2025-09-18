"""
Settings optimisés pour la production
"""
from .settings_minimal import *

# Mode production
DEBUG = False
ALLOWED_HOSTS = ['*']  # À configurer selon votre domaine

# Base de données optimisée
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'gestion_immobiliere'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_MAX_AGE': 600,
        }
    }
}

# Cache Redis pour la production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Sessions optimisées
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging optimisé
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}

# Optimisations de performance
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache middleware
    'django.middleware.cache.FetchFromCacheMiddleware',  # Cache middleware
]

# Cache global
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'gestion_immobiliere'

# Optimisations de base de données
DATABASE_ROUTERS = []

# Compression des réponses
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

# Optimisations de fichiers statiques
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Optimisations de templates
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Optimisations de requêtes
DATABASES['default']['CONN_MAX_AGE'] = 600

# Optimisations de mémoire
DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576  # 1MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 1048576  # 1MB

# Optimisations de sessions
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_SAVE_EVERY_REQUEST = False

# Optimisations de cache
CACHE_TIMEOUT = 300  # 5 minutes

# Optimisations de pagination
PAGINATE_BY = 20

# Optimisations de requêtes
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Optimisations de sécurité
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Optimisations de performance
USE_TZ = True
TIME_ZONE = 'UTC'

# Optimisations de fichiers
MEDIA_ROOT = '/var/www/media/'
STATIC_ROOT = '/var/www/static/'

# Optimisations de cache pour les vues
CACHE_TTL = 300  # 5 minutes

# Optimisations de requêtes
CONN_MAX_AGE = 600

# Optimisations de mémoire
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Optimisations de performance
USE_I18N = True
USE_L10N = True

# Optimisations de sécurité
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Optimisations de cache
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'gestion_immobiliere'

# Optimisations de performance
MIDDLEWARE.append('django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.insert(0, 'django.middleware.cache.FetchFromCacheMiddleware')

# Optimisations de base de données
DATABASES['default']['OPTIONS']['MAX_CONNS'] = 20
DATABASES['default']['OPTIONS']['CONN_MAX_AGE'] = 600

# Optimisations de cache
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'] = {
    'max_connections': 20,
    'retry_on_timeout': True,
}

# Optimisations de performance
MIDDLEWARE.append('django.middleware.gzip.GZipMiddleware')

# Optimisations de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Optimisations de cache
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'gestion_immobiliere'

# Optimisations de performance
MIDDLEWARE.append('django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.insert(0, 'django.middleware.cache.FetchFromCacheMiddleware')

# Optimisations de base de données
DATABASES['default']['OPTIONS']['MAX_CONNS'] = 20
DATABASES['default']['OPTIONS']['CONN_MAX_AGE'] = 600

# Optimisations de cache
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'] = {
    'max_connections': 20,
    'retry_on_timeout': True,
}

# Optimisations de performance
MIDDLEWARE.append('django.middleware.gzip.GZipMiddleware')

# Optimisations de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Optimisations de cache
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'gestion_immobiliere'

# Optimisations de performance
MIDDLEWARE.append('django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.insert(0, 'django.middleware.cache.FetchFromCacheMiddleware')

# Optimisations de base de données
DATABASES['default']['OPTIONS']['MAX_CONNS'] = 20
DATABASES['default']['OPTIONS']['CONN_MAX_AGE'] = 600

# Optimisations de cache
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'] = {
    'max_connections': 20,
    'retry_on_timeout': True,
}

# Optimisations de performance
MIDDLEWARE.append('django.middleware.gzip.GZipMiddleware')

# Optimisations de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'