"""
Configuration Gunicorn optimisée pour Render
"""
import multiprocessing
import os

# Configuration de base
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Max 4 workers sur Render
threads = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 120
keepalive = 5

# Configuration de logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuration de sécurité
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configuration de performance
worker_tmp_dir = "/dev/shm"  # Utiliser la RAM pour les fichiers temporaires
forwarded_allow_ips = "*"

# Configuration pour les fichiers statiques
static_map = {
    "/static": "staticfiles/",
    "/media": "media/"
}

# Configuration de mémoire
worker_memory_limit = 512  # 512MB par worker

# Configuration de processus
worker_max_requests_jitter = 50
worker_timeout = 120
graceful_timeout = 30
