# Configuration Gunicorn pour KBIS IMMOBILIER - Production VPS
import multiprocessing
import os

# Configuration du serveur
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Configuration des processus
preload_app = True
daemon = False
pidfile = "/var/run/gunicorn/kbis_immobilier.pid"
user = "www-data"
group = "www-data"

# Configuration des logs
accesslog = "/var/log/gunicorn/kbis_immobilier_access.log"
errorlog = "/var/log/gunicorn/kbis_immobilier_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuration de sécurité
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configuration de la mémoire
worker_tmp_dir = "/dev/shm"

# Configuration SSL (si nécessaire)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Configuration des variables d'environnement
raw_env = [
    'DJANGO_SETTINGS_MODULE=gestimmob.settings.production',
]

# Configuration du reload automatique (désactivé en production)
reload = False

# Configuration des signaux
graceful_timeout = 30
forwarded_allow_ips = "*"