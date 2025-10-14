import os
import django
from django.core.wsgi import get_wsgi_application

# Force le bon settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_render'

# Configuration pour éviter les problèmes d'utilisateur
os.environ.setdefault('GUNICORN_USER', '')
os.environ.setdefault('GUNICORN_GROUP', '')

django.setup()

# Initialiser la base de données
try:
    from init_database import init_database
    init_database()
except Exception as e:
    print(f"⚠️ Erreur lors de l'initialisation de la DB: {e}")
    print("⚠️ L'application peut fonctionner sans initialisation complète")

app = get_wsgi_application()
