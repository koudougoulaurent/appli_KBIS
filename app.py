import os
import django
from django.core.wsgi import get_wsgi_application

# Force le bon settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_render'
django.setup()

# Pas de migrations - toutes désactivées dans settings_render.py
print("✅ Migrations désactivées - Application prête à démarrer")

app = get_wsgi_application()
