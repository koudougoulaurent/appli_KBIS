"""
Configuration des optimisations de performance avancées
pour l'application de gestion immobilière
"""

# Activer les optimisations de performance
ENABLE_PERFORMANCE_OPTIMIZATIONS = True

# Configuration du cache avancé
CACHE_OPTIMIZATIONS = {
    'ENABLE_PAGE_CACHING': True,
    'PAGE_CACHE_TIMEOUT': 300,  # 5 minutes
    'ENABLE_FRAGMENT_CACHING': True,
    'FRAGMENT_CACHE_TIMEOUT': 600,  # 10 minutes
    'ENABLE_QUERY_CACHING': True,
    'QUERY_CACHE_TIMEOUT': 1800,  # 30 minutes
}

# Configuration des optimisations de base de données
DATABASE_OPTIMIZATIONS = {
    'ENABLE_QUERY_OPTIMIZATION': True,
    'ENABLE_INDEX_OPTIMIZATION': True,
    'ENABLE_CONNECTION_POOLING': True,
    'BATCH_SIZE': 100,
    'QUERY_TIMEOUT': 30,
}

# Configuration des optimisations de templates
TEMPLATE_OPTIMIZATIONS = {
    'ENABLE_TEMPLATE_CACHING': True,
    'ENABLE_TEMPLATE_COMPILATION': True,
    'TEMPLATE_DEBUG': False,
}

# Configuration des optimisations de fichiers statiques
STATIC_OPTIMIZATIONS = {
    'ENABLE_COMPRESSION': True,
    'ENABLE_MINIFICATION': True,
    'ENABLE_BUNDLING': True,
    'ENABLE_CDN': False,
}

# Configuration des optimisations de middleware
MIDDLEWARE_OPTIMIZATIONS = {
    'ENABLE_PERFORMANCE_MONITORING': True,
    'ENABLE_CACHE_OPTIMIZATION': True,
    'ENABLE_DATABASE_OPTIMIZATION': True,
}

# Configuration des optimisations côté client
CLIENT_OPTIMIZATIONS = {
    'ENABLE_LAZY_LOADING': True,
    'ENABLE_IMAGE_OPTIMIZATION': True,
    'ENABLE_NAVIGATION_OPTIMIZATION': True,
    'ENABLE_FORM_OPTIMIZATION': True,
    'ENABLE_TABLE_OPTIMIZATION': True,
    'ENABLE_SEARCH_OPTIMIZATION': True,
}

# Configuration des métriques de performance
PERFORMANCE_METRICS = {
    'ENABLE_WEB_VITALS': True,
    'ENABLE_QUERY_COUNTING': True,
    'ENABLE_RESPONSE_TIME_MONITORING': True,
    'ENABLE_MEMORY_USAGE_MONITORING': True,
}

# Configuration des optimisations de développement
DEVELOPMENT_OPTIMIZATIONS = {
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_PROFILING': True,
    'ENABLE_PERFORMANCE_LOGGING': True,
}

# Configuration des optimisations de production
PRODUCTION_OPTIMIZATIONS = {
    'ENABLE_COMPRESSION': True,
    'ENABLE_CACHING': True,
    'ENABLE_LOGGING': False,
    'ENABLE_SECURITY': True,
}

def get_optimization_config(environment='development'):
    """Récupérer la configuration d'optimisation selon l'environnement"""
    base_config = {
        'ENABLE_PERFORMANCE_OPTIMIZATIONS': ENABLE_PERFORMANCE_OPTIMIZATIONS,
        'CACHE_OPTIMIZATIONS': CACHE_OPTIMIZATIONS,
        'DATABASE_OPTIMIZATIONS': DATABASE_OPTIMIZATIONS,
        'TEMPLATE_OPTIMIZATIONS': TEMPLATE_OPTIMIZATIONS,
        'STATIC_OPTIMIZATIONS': STATIC_OPTIMIZATIONS,
        'MIDDLEWARE_OPTIMIZATIONS': MIDDLEWARE_OPTIMIZATIONS,
        'CLIENT_OPTIMIZATIONS': CLIENT_OPTIMIZATIONS,
        'PERFORMANCE_METRICS': PERFORMANCE_METRICS,
    }
    
    if environment == 'production':
        base_config.update(PRODUCTION_OPTIMIZATIONS)
    else:
        base_config.update(DEVELOPMENT_OPTIMIZATIONS)
    
    return base_config

def is_optimization_enabled(optimization_type):
    """Vérifier si une optimisation spécifique est activée"""
    config = get_optimization_config()
    
    if optimization_type == 'cache':
        return config['CACHE_OPTIMIZATIONS']['ENABLE_PAGE_CACHING']
    elif optimization_type == 'database':
        return config['DATABASE_OPTIMIZATIONS']['ENABLE_QUERY_OPTIMIZATION']
    elif optimization_type == 'templates':
        return config['TEMPLATE_OPTIMIZATIONS']['ENABLE_TEMPLATE_CACHING']
    elif optimization_type == 'static':
        return config['STATIC_OPTIMIZATIONS']['ENABLE_COMPRESSION']
    elif optimization_type == 'middleware':
        return config['MIDDLEWARE_OPTIMIZATIONS']['ENABLE_PERFORMANCE_MONITORING']
    elif optimization_type == 'client':
        return config['CLIENT_OPTIMIZATIONS']['ENABLE_LAZY_LOADING']
    elif optimization_type == 'metrics':
        return config['PERFORMANCE_METRICS']['ENABLE_WEB_VITALS']
    
    return False
