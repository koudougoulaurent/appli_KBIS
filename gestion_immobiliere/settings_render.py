# Configuration pour Render
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration de base
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-minimal-key-for-render')
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'appli-kbis.onrender.com', 'appli-kbis-3.onrender.com', '.onrender.com', '*', '0.0.0.0']
ROOT_URLCONF = 'gestion_immobiliere.urls'

# Applications
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
    'proprietes.apps.ProprietesConfig',
    'contrats.apps.ContratsConfig',
    'paiements.apps.PaiementsConfig',
    'notifications',
]

# Middleware
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

# Templates
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

# Configuration de sécurité
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

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

# *** CONFIGURATION PROGRESSIVE POSTGRESQL AVEC FALLBACK SQLITE ***
def get_database_config():
    """
    Configuration progressive de la base de données :
    1. Essaie PostgreSQL si DATABASE_URL est disponible
    2. Fallback vers SQLite si PostgreSQL échoue
    """
    # Vérifier si on est sur Render et si DATABASE_URL est disponible
    if os.environ.get('RENDER') and os.environ.get('DATABASE_URL'):
        try:
            import dj_database_url
            
            # Configuration PostgreSQL
            postgres_config = dj_database_url.parse(os.environ.get('DATABASE_URL'))
            
            # Ajouter des paramètres optimisés pour Render
            postgres_config.update({
                'OPTIONS': {
                    'sslmode': 'require',
                    'connect_timeout': 10,
                    'options': '-c default_transaction_isolation=read_committed'
                },
                'CONN_MAX_AGE': 60,  # Connexions persistantes
                'CONN_HEALTH_CHECKS': True,
            })
            
            print("✅ Configuration PostgreSQL détectée et configurée")
            return postgres_config
            
        except Exception as e:
            print(f"⚠️ Erreur configuration PostgreSQL: {e}")
            print("🔄 Fallback vers SQLite...")
    
    # Fallback vers SQLite
    print("📁 Utilisation de SQLite (fallback)")
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }

# Configuration de la base de données
DATABASES = {
    'default': get_database_config()
}

# *** DÉSACTIVER TOUTES LES MIGRATIONS POUR UTILISER --run-syncdb ***
# IMPORTANT: Pas de migrations, seulement syncdb pour créer les tables
MIGRATION_MODULES = {
    'core': None,
    'utilisateurs': None,
    'proprietes': None,
    'contrats': None,
    'paiements': None,
    'notifications': None,
}

# Désactiver complètement les migrations
USE_MIGRATIONS = False

# Configuration pour Render
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'appli-kbis.onrender.com', '.onrender.com', '*', '0.0.0.0']
