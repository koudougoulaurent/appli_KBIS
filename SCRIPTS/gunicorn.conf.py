# Configuration Gunicorn pour Render
import os

# Configuration de base
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
workers = 2
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Configuration des processus
worker_class = 'sync'
worker_connections = 1000

# Configuration des logs
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configuration de sécurité
user = None  # Pas d'utilisateur spécifique
group = None  # Pas de groupe spécifique

# Configuration Django
wsgi_module = 'app:app'