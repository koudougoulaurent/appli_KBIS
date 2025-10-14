import os
import django
from django.core.wsgi import get_wsgi_application

# Force le bon settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_render'
django.setup()

# Exécuter le script de migration
try:
    from fix_migration import fix_migrations
    fix_migrations()
except Exception as e:
    print(f"⚠️ Erreur lors de la résolution des migrations: {e}")
    print("⚠️ L'application peut fonctionner sans les migrations")

app = get_wsgi_application()
