"""
Point d'entrée pour Render - Redirige vers l'application Django
"""
import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')

# Configuration Django
django.setup()

# Application WSGI
app = get_wsgi_application()
