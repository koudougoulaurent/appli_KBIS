from .settings import * # Importe toutes les configurations de base

# ===========================================
# PARAMÈTRES SPÉCIFIQUES À PYTHONANYWHERE
# ===========================================

DEBUG = False # Toujours False en production !

ALLOWED_HOSTS = [
    'laurenzo.pythonanywhere.com',  # Votre domaine PythonAnywhere
    '.pythonanywhere.com'           # Tous les sous-domaines PythonAnywhere
]

# ===========================================
# CONFIGURATION DES FICHIERS STATIQUES ET MÉDIA
# ===========================================

# Chemin absolu vers le répertoire où collectstatic va copier les fichiers statiques
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# URL pour servir les fichiers statiques
STATIC_URL = '/static/'

# Répertoires où Django cherchera des fichiers statiques supplémentaires
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Chemin absolu vers le répertoire où les fichiers média seront stockés
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL pour servir les fichiers média
MEDIA_URL = '/media/'

# ===========================================
# CONFIGURATION WHITENOISE (pour servir les fichiers statiques en production)
# ===========================================
# Assurez-vous que 'whitenoise.middleware.WhiteNoiseMiddleware' est ajouté
# au début de votre liste MIDDLEWARE dans settings.py (fichier de base)
# et que WhiteNoise est installé (pip install whitenoise)

# ===========================================
# SÉCURITÉ (Recommandé pour la production)
# ===========================================

# Clé secrète (à gérer via des variables d'environnement ou PythonAnywhere)
# SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'votre_clé_secrète_par_défaut_très_longue_et_aléatoire')
# Pour PythonAnywhere, vous pouvez la définir directement dans l'onglet "Web"
# ou utiliser python-decouple/django-environ avec un fichier .env non versionné.

# Redirection HTTPS (si PythonAnywhere est configuré pour HTTPS)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# HSTS (HTTP Strict Transport Security) - à activer avec prudence
# SECURE_HSTS_SECONDS = 31536000 # 1 an
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# ===========================================
# LOGGING (Exemple de configuration simple pour PythonAnywhere)
# ===========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
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
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'gestion_immobiliere': { # Remplacez par le nom de votre projet principal
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}