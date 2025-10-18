"""
Settings minimal pour tester l'application
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', '%g+gmad@&-r4yyp4ss+y1^1ktigscq&!mtno^c#_$%sa9&p)a=')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'appli-kbis.onrender.com', 'appli-kbis-3.onrender.com', '.onrender.com', '*', '0.0.0.0']
ROOT_URLCONF = 'gestion_immobiliere.urls'

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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_immobiliere.urls'

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

WSGI_APPLICATION = 'gestion_immobiliere.wsgi.application'

# Configuration de base de données par défaut
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration du modèle d'utilisateur personnalisé
AUTH_USER_MODEL = 'utilisateurs.Utilisateur'

LOGIN_URL = '/utilisateurs/connexion-groupes/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/utilisateurs/connexion-groupes/'

# Configuration de Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuration de sécurité pour le développement
if DEBUG:
    # En développement, on peut désactiver certaines vérifications de sécurité
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
else:
    # En production, activer toutes les mesures de sécurité
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Configuration pour la production (Render, VPS, etc.)
if os.environ.get('RENDER') or os.environ.get('DJANGO_SETTINGS_MODULE') == 'gestion_immobiliere.settings_production':
    # Configuration de base de données pour la production
    try:
        import dj_database_url
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        # Validation de DATABASE_URL
        if DATABASE_URL and DATABASE_URL.strip() and not DATABASE_URL.startswith("b'") and not DATABASE_URL.startswith("b\""):
            try:
                DATABASES = {
                    'default': dj_database_url.parse(DATABASE_URL)
                }
            except Exception as e:
                print(f"Erreur parsing DATABASE_URL: {e}")
                # Fallback vers SQLite en cas d'erreur
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': BASE_DIR / 'db.sqlite3',
                    }
                }
        else:
            # Fallback vers SQLite si pas de DATABASE_URL valide
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
    except ImportError:
        # Si dj_database_url n'est pas installé, utiliser SQLite
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    
    # Configuration statique pour la production
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
    
# Configuration de sécurité pour production
if os.environ.get('RENDER'):
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    ALLOWED_HOSTS = ['appli-kbis.onrender.com', 'appli-kbis-3.onrender.com', '.onrender.com', 'localhost', '127.0.0.1']
    
    # Configuration de session
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
