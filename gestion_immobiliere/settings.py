"""
Settings minimal pour tester l'application
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-test-key-for-local-development-only'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'appli-kbis.onrender.com', '.onrender.com', '*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Pour les filtres de formatage des nombres
    'rest_framework',  # Pour l'API REST
    'crispy_forms',  # Pour les formulaires stylés
    'crispy_bootstrap5',  # Pour l'intégration Bootstrap 5
    'core',
    'utilisateurs',
    'proprietes',
    'contrats',
    'paiements',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_immobiliere.wsgi.application'

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

# Configuration pour Render
if os.environ.get('RENDER'):
    # Configuration de base de données pour Render
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
    
    # Configuration statique pour Render
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
    
    # Configuration de sécurité pour production
    DEBUG = False
    ALLOWED_HOSTS = ['appli-kbis.onrender.com', '.onrender.com']
    
    # Configuration de session
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
