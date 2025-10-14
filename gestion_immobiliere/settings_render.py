# Import des settings de base
from .settings import *

# Configuration pour Render
import os

# Base de données SQLite pour Render (temporaire)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Désactiver toutes les migrations pour éviter les conflits
MIGRATION_MODULES = {
    'paiements': None,
    'proprietes': None,
    'contrats': None,
    'utilisateurs': None,
    'notifications': None,
    'core': None,
    'admin': None,
    'auth': None,
    'contenttypes': None,
    'sessions': None,
    'messages': None,
    'staticfiles': None,
    'humanize': None,
}
