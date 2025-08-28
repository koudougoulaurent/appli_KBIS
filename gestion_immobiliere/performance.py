"""
Configuration des optimisations de performance pour l'application
de gestion immobilière
"""

import os
from pathlib import Path

# Configuration des performances
PERFORMANCE_CONFIG = {
    # Cache
    'CACHE_TIMEOUT': 300,  # 5 minutes par défaut
    'CACHE_MAX_ENTRIES': 1000,
    'CACHE_CULL_FREQUENCY': 3,
    
    # Base de données
    'DB_OPTIMIZATION': True,
    'DB_CONN_MAX_AGE': 60,
    'DB_ATOMIC_REQUESTS': False,
    
    # Sessions
    'SESSION_ENGINE': 'django.contrib.sessions.backends.cached_db',
    'SESSION_COOKIE_AGE': 3600,  # 1 heure
    'SESSION_SAVE_EVERY_REQUEST': False,
    
    # Templates
    'TEMPLATE_DEBUG': False,
    'TEMPLATE_LOADERS': [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ],
    
    # Middleware de performance
    'PERFORMANCE_MIDDLEWARE': True,
    'CACHE_MIDDLEWARE': True,
    'COMPRESSION_MIDDLEWARE': True,
    
    # Optimisations spécifiques
    'LAZY_LOADING': True,
    'IMAGE_OPTIMIZATION': True,
    'CSS_JS_MINIFICATION': True,
}

# Configuration du cache Redis (si disponible)
REDIS_CONFIG = {
    'HOST': os.getenv('REDIS_HOST', 'localhost'),
    'PORT': int(os.getenv('REDIS_PORT', 6379)),
    'DB': int(os.getenv('REDIS_DB', 0)),
    'PASSWORD': os.getenv('REDIS_PASSWORD', None),
    'SOCKET_TIMEOUT': 5,
    'SOCKET_CONNECT_TIMEOUT': 5,
    'RETRY_ON_TIMEOUT': True,
    'MAX_CONNECTIONS': 20,
}

# Configuration des optimisations de base de données
DATABASE_OPTIMIZATIONS = {
    'SQLITE': {
        'journal_mode': 'WAL',
        'synchronous': 'NORMAL',
        'cache_size': 10000,
        'temp_store': 'MEMORY',
        'mmap_size': 268435456,  # 256MB
        'page_size': 4096,
        'max_page_count': 1073741824,  # 1GB
    },
    'POSTGRESQL': {
        'max_connections': 100,
        'shared_buffers': '256MB',
        'effective_cache_size': '1GB',
        'work_mem': '4MB',
        'maintenance_work_mem': '64MB',
    },
    'MYSQL': {
        'max_connections': 100,
        'innodb_buffer_pool_size': '256M',
        'query_cache_size': '32M',
        'query_cache_type': 1,
    }
}

# Configuration des middlewares de performance
PERFORMANCE_MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'utilisateurs.middleware.PerformanceMiddleware',
    'utilisateurs.middleware.DatabaseOptimizationMiddleware',
    'utilisateurs.middleware.CacheOptimizationMiddleware',
]

# Configuration du cache
CACHE_CONFIG = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': PERFORMANCE_CONFIG['CACHE_TIMEOUT'],
        'OPTIONS': {
            'MAX_ENTRIES': PERFORMANCE_CONFIG['CACHE_MAX_ENTRIES'],
            'CULL_FREQUENCY': PERFORMANCE_CONFIG['CACHE_CULL_FREQUENCY'],
        }
    }
}

# Configuration des sessions
SESSION_CONFIG = {
    'ENGINE': PERFORMANCE_CONFIG['SESSION_ENGINE'],
    'CACHE_ALIAS': 'default',
    'COOKIE_AGE': PERFORMANCE_CONFIG['SESSION_COOKIE_AGE'],
    'SAVE_EVERY_REQUEST': PERFORMANCE_CONFIG['SESSION_SAVE_EVERY_REQUEST'],
    'EXPIRE_AT_BROWSER_CLOSE': False,
}

# Configuration des templates
TEMPLATE_CONFIG = {
    'DEBUG': PERFORMANCE_CONFIG['TEMPLATE_DEBUG'],
    'LOADERS': PERFORMANCE_CONFIG['TEMPLATE_LOADERS'],
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'core.context_processors.devise_active',
            'core.context_processors.devises_actives',
        ],
        'debug': PERFORMANCE_CONFIG['TEMPLATE_DEBUG'],
    }
}

# Configuration des fichiers statiques
STATIC_CONFIG = {
    'STORAGE': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    'COMPRESS': True,
    'COMPRESS_CSS_FILTERS': [
        'compressor.filters.css_default.CssAbsoluteFilter',
        'compressor.filters.cssmin.rCSSMinFilter',
    ],
    'COMPRESS_JS_FILTERS': [
        'compressor.filters.jsmin.JSMinFilter',
    ],
}

# Configuration des logs de performance
PERFORMANCE_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'performance': {
            'format': '[{asctime}] {levelname} {module} {funcName} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': Path(__file__).parent.parent / 'logs' / 'performance.log',
            'formatter': 'performance',
        },
        'performance_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'performance',
        },
    },
    'loggers': {
        'performance': {
            'handlers': ['performance_file', 'performance_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuration des optimisations de requêtes
QUERY_OPTIMIZATIONS = {
    'SELECT_RELATED': True,
    'PREFETCH_RELATED': True,
    'ONLY': True,
    'DEFER': True,
    'BULK_OPERATIONS': True,
    'BATCH_SIZE': 100,
    'QUERY_TIMEOUT': 30,  # secondes
}

# Configuration des optimisations de templates
TEMPLATE_OPTIMIZATIONS = {
    'FRAGMENT_CACHING': True,
    'TEMPLATE_FRAGMENT_TIMEOUT': 300,
    'TEMPLATE_LOADING_CACHE': True,
    'TEMPLATE_DEBUG': False,
}

# Configuration des optimisations de fichiers statiques
STATIC_OPTIMIZATIONS = {
    'COMPRESSION': True,
    'MINIFICATION': True,
    'BUNDLING': True,
    'CDN': False,
    'VERSIONING': True,
}

# Configuration des optimisations de sécurité
SECURITY_OPTIMIZATIONS = {
    'HTTPS_REDIRECT': False,  # À activer en production
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'X_FRAME_OPTIONS': 'DENY',
    'SECURE_HSTS_SECONDS': 31536000,  # 1 an
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
}

# Configuration des optimisations de développement
DEVELOPMENT_OPTIMIZATIONS = {
    'DEBUG_TOOLBAR': False,
    'PROFILING': True,
    'QUERY_COUNT': True,
    'MEMORY_USAGE': True,
    'PERFORMANCE_MONITORING': True,
}

# Configuration des optimisations de production
PRODUCTION_OPTIMIZATIONS = {
    'DEBUG': False,
    'COMPRESSION': True,
    'CACHING': True,
    'LOGGING': 'ERROR',
    'SECURITY': True,
    'PERFORMANCE_MONITORING': True,
}

def get_performance_config(environment='development'):
    """Récupérer la configuration de performance selon l'environnement"""
    if environment == 'production':
        return {
            **PERFORMANCE_CONFIG,
            **PRODUCTION_OPTIMIZATIONS,
        }
    else:
        return {
            **PERFORMANCE_CONFIG,
            **DEVELOPMENT_OPTIMIZATIONS,
        }

def get_cache_config(backend='default'):
    """Récupérer la configuration du cache selon le backend"""
    if backend == 'redis':
        return {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"redis://{REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}/{REDIS_CONFIG['DB']}",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PASSWORD': REDIS_CONFIG['PASSWORD'],
                'SOCKET_TIMEOUT': REDIS_CONFIG['SOCKET_TIMEOUT'],
                'SOCKET_CONNECT_TIMEOUT': REDIS_CONFIG['SOCKET_CONNECT_TIMEOUT'],
                'RETRY_ON_TIMEOUT': REDIS_CONFIG['RETRY_ON_TIMEOUT'],
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': REDIS_CONFIG['MAX_CONNECTIONS'],
                },
            }
        }
    else:
        return CACHE_CONFIG['default']

def get_database_optimizations(database_type='sqlite'):
    """Récupérer les optimisations de base de données selon le type"""
    return DATABASE_OPTIMIZATIONS.get(database_type.upper(), {})

def get_middleware_config(include_performance=True):
    """Récupérer la configuration des middlewares"""
    if include_performance:
        return PERFORMANCE_MIDDLEWARE
    else:
        return []

def get_logging_config(include_performance=True):
    """Récupérer la configuration des logs"""
    if include_performance:
        return PERFORMANCE_LOGGING
    else:
        return {}
