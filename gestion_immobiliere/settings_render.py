# Import des settings de base
from .settings import *

# Configuration pour Render
import os

# Base de données SQLite pour Render
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Désactiver les migrations problématiques seulement
MIGRATION_MODULES = {
    'core': None,  # Désactiver les migrations core qui causent des conflits
}

# Configuration pour Render
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'appli-kbis.onrender.com', '.onrender.com', '*', '0.0.0.0']
