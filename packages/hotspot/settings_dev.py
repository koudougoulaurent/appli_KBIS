"""
Configuration de développement pour le package hotspot
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les settings principaux
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Importer la configuration principale
from gestion_immobiliere.settings import *

# Configuration spécifique au développement
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Base de données SQLite pour le développement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration de sécurité assouplie pour le développement
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False