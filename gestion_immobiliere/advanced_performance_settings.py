"""
Configuration avancée des optimisations de performance
pour l'application de gestion immobilière
"""

# Configuration du cache Redis (si disponible)
REDIS_CACHE_CONFIG = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/1',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'KEY_PREFIX': 'gestimmob',
    'TIMEOUT': 300,
}

# Configuration du cache de base de données
DATABASE_CACHE_CONFIG = {
    'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    'LOCATION': 'cache_table',
    'TIMEOUT': 300,
    'OPTIONS': {
        'MAX_ENTRIES': 1000,
        'CULL_FREQUENCY': 3,
    }
}

# Configuration des optimisations de requêtes
QUERY_OPTIMIZATIONS = {
    'ENABLE_QUERY_ANALYSIS': True,
    'SLOW_QUERY_THRESHOLD': 0.1,  # secondes
    'ENABLE_QUERY_CACHING': True,
    'QUERY_CACHE_TIMEOUT': 600,  # 10 minutes
    'ENABLE_QUERY_PRELOADING': True,
    'BATCH_SIZE': 50,
}

# Configuration des optimisations de templates
TEMPLATE_OPTIMIZATIONS = {
    'ENABLE_TEMPLATE_CACHING': True,
    'TEMPLATE_CACHE_TIMEOUT': 1800,  # 30 minutes
    'ENABLE_TEMPLATE_COMPILATION': True,
    'ENABLE_TEMPLATE_MINIFICATION': True,
    'ENABLE_TEMPLATE_COMPRESSION': True,
}

# Configuration des optimisations de fichiers statiques
STATIC_OPTIMIZATIONS = {
    'ENABLE_STATIC_COMPRESSION': True,
    'ENABLE_STATIC_MINIFICATION': True,
    'ENABLE_STATIC_BUNDLING': True,
    'ENABLE_STATIC_CACHING': True,
    'STATIC_CACHE_TIMEOUT': 31536000,  # 1 an
    'ENABLE_CDN': False,
    'CDN_URL': None,
}

# Configuration des optimisations de session
SESSION_OPTIMIZATIONS = {
    'SESSION_ENGINE': 'django.contrib.sessions.backends.cached_db',
    'SESSION_CACHE_ALIAS': 'default',
    'SESSION_COOKIE_AGE': 3600,  # 1 heure
    'SESSION_SAVE_EVERY_REQUEST': False,
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': False,
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
}

# Configuration des optimisations de base de données
DATABASE_OPTIMIZATIONS = {
    'CONN_MAX_AGE': 60,
    'ATOMIC_REQUESTS': True,
    'AUTOCOMMIT': True,
    'OPTIONS': {
        'timeout': 30,
        'check_same_thread': False,
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }
}

# Configuration des optimisations de middleware
MIDDLEWARE_OPTIMIZATIONS = {
    'ENABLE_GZIP_COMPRESSION': True,
    'ENABLE_ETAG_CACHING': True,
    'ENABLE_LAST_MODIFIED_CACHING': True,
    'ENABLE_CONDITIONAL_GET': True,
    'ENABLE_HTTP_CACHING': True,
    'CACHE_CONTROL_MAX_AGE': 3600,  # 1 heure
}

# Configuration des optimisations côté client
CLIENT_OPTIMIZATIONS = {
    'ENABLE_LAZY_LOADING': True,
    'ENABLE_IMAGE_OPTIMIZATION': True,
    'ENABLE_IMAGE_LAZY_LOADING': True,
    'ENABLE_IMAGE_WEBP_CONVERSION': True,
    'ENABLE_NAVIGATION_OPTIMIZATION': True,
    'ENABLE_FORM_OPTIMIZATION': True,
    'ENABLE_TABLE_OPTIMIZATION': True,
    'ENABLE_SEARCH_OPTIMIZATION': True,
    'ENABLE_INFINITE_SCROLL': True,
    'ENABLE_VIRTUAL_SCROLLING': True,
}

# Configuration des métriques de performance
PERFORMANCE_METRICS = {
    'ENABLE_WEB_VITALS': True,
    'ENABLE_QUERY_COUNTING': True,
    'ENABLE_RESPONSE_TIME_MONITORING': True,
    'ENABLE_MEMORY_USAGE_MONITORING': True,
    'ENABLE_CPU_USAGE_MONITORING': True,
    'ENABLE_DATABASE_MONITORING': True,
    'ENABLE_CACHE_MONITORING': True,
    'ENABLE_ERROR_MONITORING': True,
}

# Configuration des optimisations de développement
DEVELOPMENT_OPTIMIZATIONS = {
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_QUERY_DEBUGGING': False,
    'ENABLE_TEMPLATE_DEBUGGING': False,
    'ENABLE_SQL_LOGGING': False,
    'ENABLE_CACHE_DEBUGGING': False,
}

# Configuration des optimisations de production
PRODUCTION_OPTIMIZATIONS = {
    'ENABLE_HTTPS_REDIRECT': True,
    'ENABLE_SECURITY_HEADERS': True,
    'ENABLE_CORS_OPTIMIZATION': True,
    'ENABLE_CSRF_OPTIMIZATION': True,
    'ENABLE_SESSION_OPTIMIZATION': True,
    'ENABLE_PASSWORD_OPTIMIZATION': True,
}

# Configuration des optimisations de monitoring
MONITORING_OPTIMIZATIONS = {
    'ENABLE_PERFORMANCE_LOGGING': True,
    'ENABLE_ERROR_LOGGING': True,
    'ENABLE_ACCESS_LOGGING': True,
    'ENABLE_SECURITY_LOGGING': True,
    'ENABLE_AUDIT_LOGGING': True,
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': 'json',
}

# Configuration des optimisations de sécurité
SECURITY_OPTIMIZATIONS = {
    'ENABLE_RATE_LIMITING': True,
    'RATE_LIMIT_REQUESTS': 100,  # par minute
    'RATE_LIMIT_WINDOW': 60,  # secondes
    'ENABLE_IP_WHITELISTING': False,
    'ENABLE_USER_AGENT_FILTERING': False,
    'ENABLE_REFERER_CHECKING': False,
}

# Configuration des optimisations de backup
BACKUP_OPTIMIZATIONS = {
    'ENABLE_AUTOMATIC_BACKUP': True,
    'BACKUP_FREQUENCY': 'daily',
    'BACKUP_RETENTION': 30,  # jours
    'BACKUP_COMPRESSION': True,
    'BACKUP_ENCRYPTION': True,
    'BACKUP_STORAGE': 'local',  # ou 's3', 'gcs', etc.
}

# Configuration des optimisations de déploiement
DEPLOYMENT_OPTIMIZATIONS = {
    'ENABLE_ZERO_DOWNTIME_DEPLOYMENT': True,
    'ENABLE_ROLLBACK_CAPABILITY': True,
    'ENABLE_HEALTH_CHECKS': True,
    'ENABLE_LOAD_BALANCING': False,
    'ENABLE_AUTO_SCALING': False,
}

# Configuration des optimisations de maintenance
MAINTENANCE_OPTIMIZATIONS = {
    'ENABLE_AUTOMATIC_MAINTENANCE': True,
    'MAINTENANCE_WINDOW': '02:00-04:00',  # UTC
    'ENABLE_DATABASE_VACUUM': True,
    'ENABLE_CACHE_CLEANUP': True,
    'ENABLE_LOG_ROTATION': True,
    'ENABLE_TEMP_FILE_CLEANUP': True,
}
