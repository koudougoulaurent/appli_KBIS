# Configuration Gunicorn pour KBIS Immobilier
# Optimisée pour VPS avec PostgreSQL

import multiprocessing
import os

# Configuration du serveur
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Configuration des processus
preload_app = True
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = "kbis"
group = "kbis"

# Configuration des logs
accesslog = "/var/log/gunicorn/kbis_access.log"
errorlog = "/var/log/gunicorn/kbis_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuration de sécurité
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configuration de l'application
pythonpath = "/home/kbis/appli_KBIS"
chdir = "/home/kbis/appli_KBIS"
raw_env = [
    'DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production',
]

# Configuration des signaux
def when_ready(server):
    server.log.info("Serveur Gunicorn prêt à recevoir des connexions")

def worker_int(worker):
    worker.log.info("Worker reçu signal SIGINT")

def pre_fork(server, worker):
    server.log.info("Worker %s créé", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker %s initialisé", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker %s reçu signal SIGABRT", worker.pid)
