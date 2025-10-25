"""
Point d'entrée pour Render.com
Redirige vers l'application Django WSGI
"""
import os
import sys
from django.core.wsgi import get_wsgi_application

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')

# Application WSGI Django
application = get_wsgi_application()

# Alias pour compatibilité
app = application
