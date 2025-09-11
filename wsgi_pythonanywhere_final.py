import os
import sys

path = '/home/laurenzo/appli_KBIS'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_pythonanywhere')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()