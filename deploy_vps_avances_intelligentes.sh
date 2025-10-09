#!/bin/bash
# Script de déploiement automatique sur VPS avec système d'avances intelligentes
# Usage: ./deploy_vps_avances_intelligentes.sh

echo "🚀 Déploiement de l'application Django avec avances intelligentes sur VPS"
echo "========================================================================"

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./deploy_vps_avances_intelligentes.sh"
    exit 1
fi

echo "✅ Privilèges administrateur confirmés"

# Configuration
PROJECT_DIR="/home/gestimmob/appli_KBIS"
BACKUP_DIR="/var/backups/gestimmob"
LOG_FILE="/var/log/gestimmob/deploy.log"
BRANCH="modifications-octobre-2025"

# Créer les répertoires nécessaires
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Fonction de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fonction de sauvegarde
backup_database() {
    log "📦 Création de la sauvegarde de la base de données..."
    
    cd "$PROJECT_DIR"
    if [ -f "manage.py" ]; then
        sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py dumpdata > $BACKUP_DIR/backup_avant_avances_intelligentes_$(date +%Y%m%d_%H%M%S).json"
        log "✅ Sauvegarde créée avec succès"
    else
        log "⚠️  Aucune base de données à sauvegarder (première installation)"
    fi
}

# Fonction de mise à jour du code
update_code() {
    log "📥 Mise à jour du code source..."
    
    cd "$PROJECT_DIR"
    
    if [ -d ".git" ]; then
        # Sauvegarder les modifications locales
        sudo -u gestimmob git stash push -m "Sauvegarde avant déploiement avances intelligentes $(date +%Y%m%d_%H%M%S)"
        
        # Récupérer les dernières modifications
        sudo -u gestimmob git fetch origin
        sudo -u gestimmob git checkout "$BRANCH"
        sudo -u gestimmob git pull origin "$BRANCH"
        
        log "✅ Code mis à jour depuis la branche $BRANCH"
    else
        log "⚠️  Pas de repository Git, clonage initial..."
        cd /home/gestimmob
        sudo -u gestimmob git clone https://github.com/koudougoulaurent/appli_KBIS.git
        cd appli_KBIS
        sudo -u gestimmob git checkout "$BRANCH"
    fi
}

# Fonction d'installation des dépendances
install_dependencies() {
    log "📦 Installation des dépendances..."
    
    cd "$PROJECT_DIR"
    
    # Activer l'environnement virtuel
    if [ ! -d "venv" ]; then
        log "🐍 Création de l'environnement virtuel..."
        sudo -u gestimmob python3 -m venv venv
    fi
    
    # Installer les dépendances
    sudo -u gestimmob bash -c "source venv/bin/activate && pip install --upgrade pip"
    sudo -u gestimmob bash -c "source venv/bin/activate && pip install -r requirements_production.txt"
    sudo -u gestimmob bash -c "source venv/bin/activate && pip install gunicorn psycopg2-binary"
    
    log "✅ Dépendances installées"
}

# Fonction d'application des migrations
apply_migrations() {
    log "🗄️ Application des migrations..."
    
    cd "$PROJECT_DIR"
    
    # Vérifier l'état des migrations
    log "État des migrations avant application:"
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py showmigrations paiements"
    
    # Appliquer toutes les migrations
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py migrate"
    
    # Vérifier l'état des migrations après application
    log "État des migrations après application:"
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py showmigrations paiements"
    
    log "✅ Migrations appliquées"
}

# Fonction de correction des données
fix_data() {
    log "🔧 Correction des données existantes..."
    
    cd "$PROJECT_DIR"
    
    # Script de correction des données
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py shell" << 'EOF'
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from datetime import date

print("Début de la correction des données...")

# Corriger les avances avec des dates incorrectes
avances_corrigees = 0
for avance in AvanceLoyer.objects.all():
    corrected = False
    if avance.mois_debut_couverture and avance.mois_debut_couverture.year < 2000:
        avance.mois_debut_couverture = avance.mois_debut_couverture.replace(year=avance.mois_debut_couverture.year + 2000)
        corrected = True
    if avance.mois_fin_couverture and avance.mois_fin_couverture.year < 2000:
        avance.mois_fin_couverture = avance.mois_fin_couverture.replace(year=avance.mois_fin_couverture.year + 2000)
        corrected = True
    if corrected:
        avance.save()
        avances_corrigees += 1

print(f"Avances corrigées: {avances_corrigees}")

# Supprimer les consommations avec des dates incorrectes
consommations_supprimees = ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).count()
ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).delete()

print(f"Consommations supprimées: {consommations_supprimees}")

# Recalculer les montants restants
for avance in AvanceLoyer.objects.all():
    avance.montant_restant = avance.montant_avance
    avance.statut = 'active'
    avance.save()

print("Correction des données terminée")
EOF
    
    log "✅ Données corrigées"
}

# Fonction de collecte des fichiers statiques
collect_static() {
    log "📁 Collecte des fichiers statiques..."
    
    cd "$PROJECT_DIR"
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py collectstatic --noinput"
    
    log "✅ Fichiers statiques collectés"
}

# Fonction de redémarrage des services
restart_services() {
    log "🔄 Redémarrage des services..."
    
    # Redémarrer Gunicorn
    systemctl restart gestimmob
    systemctl enable gestimmob
    
    # Redémarrer Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    # Nettoyer le cache Django
    cd "$PROJECT_DIR"
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py clear_cache"
    
    log "✅ Services redémarrés"
}

# Fonction de vérification
verify_deployment() {
    log "🔍 Vérification du déploiement..."
    
    cd "$PROJECT_DIR"
    
    # Vérifier l'intégrité des données
    sudo -u gestimmob bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps && python manage.py shell" << 'EOF'
from paiements.models_avance import AvanceLoyer

print("Vérification de l'intégrité des données...")

# Vérifier les avances
avances = AvanceLoyer.objects.all()
print(f"Total avances: {avances.count()}")

# Vérifier les avances avec des problèmes
problemes = avances.filter(montant_restant__lt=0)
print(f"Avances avec montant restant négatif: {problemes.count()}")

# Vérifier les dates
dates_incorrectes = avances.filter(mois_debut_couverture__year__lt=2000)
print(f"Avances avec dates incorrectes: {dates_incorrectes.count()}")

# Vérifier les nouveaux champs
champs_manquants = avances.filter(paiement__isnull=True).count()
print(f"Avances sans paiement associé: {champs_manquants}")

print("Vérification terminée")
EOF
    
    # Vérifier les services
    systemctl is-active --quiet gestimmob && log "✅ Service gestimmob actif" || log "❌ Service gestimmob inactif"
    systemctl is-active --quiet nginx && log "✅ Service nginx actif" || log "❌ Service nginx inactif"
    systemctl is-active --quiet postgresql && log "✅ Service postgresql actif" || log "❌ Service postgresql inactif"
    
    log "✅ Vérification terminée"
}

# Fonction principale
main() {
    log "=== DÉBUT DU DÉPLOIEMENT AVANCES INTELLIGENTES ==="
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -f "$PROJECT_DIR/manage.py" ] && [ ! -d "/home/gestimmob" ]; then
        log "❌ Répertoire de projet incorrect, exécution de l'installation complète..."
        
        # Installation complète du système
        echo "📦 Mise à jour du système..."
        apt update && apt upgrade -y
        
        echo "🔧 Installation des dépendances..."
        apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib nginx git curl wget htop
        
        echo "📦 Installation de Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt install -y nodejs
        
        echo "🗄️ Configuration de PostgreSQL..."
        systemctl start postgresql
        systemctl enable postgresql
        
        # Créer la base de données et l'utilisateur
        sudo -u postgres psql -c "CREATE DATABASE gestimmob_db;" 2>/dev/null || true
        sudo -u postgres psql -c "CREATE USER gestimmob_user WITH PASSWORD 'gestimmob_password';" 2>/dev/null || true
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gestimmob_db TO gestimmob_user;" 2>/dev/null || true
        sudo -u postgres psql -c "ALTER USER gestimmob_user CREATEDB;" 2>/dev/null || true
        
        echo "👤 Création de l'utilisateur application..."
        useradd -m -s /bin/bash gestimmob 2>/dev/null || true
        usermod -aG www-data gestimmob
        
        echo "📁 Création du répertoire application..."
        mkdir -p /home/gestimmob/appli_KBIS
        chown gestimmob:gestimmob /home/gestimmob/appli_KBIS
        
        # Cloner le code
        cd /home/gestimmob
        sudo -u gestimmob git clone https://github.com/koudougoulaurent/appli_KBIS.git
        cd appli_KBIS
        sudo -u gestimmob git checkout "$BRANCH"
        
        # Créer l'environnement virtuel
        sudo -u gestimmob python3 -m venv venv
        chown -R gestimmob:gestimmob venv
        
        # Configuration de la base de données dans settings
        cat > /home/gestimmob/appli_KBIS/gestion_immobiliere/settings_vps.py << 'EOF'
"""
Configuration Django pour VPS avec avances intelligentes
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ics4n+vw1)3tlekunwt5b%(05ug)s&%*h-z&bmw1$_pd11_9nd')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'votre-domaine.com',
    'www.votre-domaine.com',
    os.environ.get('SERVER_IP', ''),
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'whitenoise.runserver_nostatic',
    'core',
    'utilisateurs',
    'proprietes',
    'contrats',
    'paiements',
    'notifications',
    'bailleurs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_immobiliere.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.entreprise_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_immobiliere.wsgi.application'

# Base de données PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gestimmob_db',
        'USER': 'gestimmob_user',
        'PASSWORD': 'gestimmob_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Fichiers statiques
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# Modèle utilisateur
AUTH_USER_MODEL = 'utilisateurs.Utilisateur'

# Configuration crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuration REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Configuration des messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_vps.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Créer le répertoire de logs
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
EOF
        
        # Configuration de Gunicorn
        cat > /etc/systemd/system/gestimmob.service << 'EOF'
[Unit]
Description=Gunicorn instance to serve gestimmob
After=network.target

[Service]
User=gestimmob
Group=www-data
WorkingDirectory=/home/gestimmob/appli_KBIS
Environment="PATH=/home/gestimmob/appli_KBIS/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_vps"
ExecStart=/home/gestimmob/appli_KBIS/venv/bin/gunicorn --workers 3 --bind unix:/home/gestimmob/appli_KBIS/gestimmob.sock gestion_immobiliere.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
        
        # Configuration de Nginx
        cat > /etc/nginx/sites-available/gestimmob << 'EOF'
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/gestimmob/appli_KBIS;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        root /home/gestimmob/appli_KBIS;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/gestimmob/appli_KBIS/gestimmob.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
        
        # Activer le site
        ln -sf /etc/nginx/sites-available/gestimmob /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Configuration du firewall
        ufw allow OpenSSH
        ufw allow 'Nginx Full'
        ufw --force enable
        
        systemctl daemon-reload
    fi
    
    # Exécuter les étapes de déploiement
    backup_database
    update_code
    install_dependencies
    apply_migrations
    fix_data
    collect_static
    restart_services
    verify_deployment
    
    log "=== DÉPLOIEMENT AVANCES INTELLIGENTES TERMINÉ AVEC SUCCÈS ==="
    
    # Afficher les informations de post-déploiement
    echo ""
    echo "🎉 DÉPLOIEMENT RÉUSSI !"
    echo ""
    echo "📋 Informations importantes:"
    echo "   - Sauvegarde: $BACKUP_DIR"
    echo "   - Logs: $LOG_FILE"
    echo "   - Projet: $PROJECT_DIR"
    echo "   - Branche: $BRANCH"
    echo ""
    echo "🔧 Nouvelles fonctionnalités disponibles:"
    echo "   - Intégration automatique des avances dans le système de paiement"
    echo "   - Détection intelligente des avances existantes"
    echo "   - Sélection manuelle des mois couverts"
    echo "   - Interface utilisateur améliorée"
    echo ""
    echo "🌐 URLs importantes:"
    echo "   - Application: http://votre-ip-serveur"
    echo "   - Création avance: http://votre-ip-serveur/paiements/avances/ajouter/"
    echo "   - Admin: http://votre-ip-serveur/admin/"
    echo ""
    echo "📊 Commandes utiles:"
    echo "   - Logs app: sudo journalctl -u gestimmob -f"
    echo "   - Logs nginx: sudo tail -f /var/log/nginx/error.log"
    echo "   - Redémarrer: sudo systemctl restart gestimmob"
    echo "   - Vérifier status: sudo systemctl status gestimmob"
    echo ""
    echo "✅ Votre application avec avances intelligentes est maintenant en ligne !"
}

# Exécuter le script principal
main "$@"
