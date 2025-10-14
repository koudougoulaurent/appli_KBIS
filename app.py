"""
Point d'entrée pour Render
"""
import os
import django
from django.core.wsgi import get_wsgi_application

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')

# Initialisation Django
django.setup()

# Application WSGI
app = get_wsgi_application()
