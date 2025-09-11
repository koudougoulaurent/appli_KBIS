# Guide de Déploiement sur LWS (LWS Hosting)

## 📋 Prérequis

1. **Compte LWS** : Créez un compte sur [lws.fr](https://www.lws.fr)
2. **Plan recommandé** : 
   - **Débutant** : Plan "Python" ou "Développeur" (environ 3-5€/mois)
   - **Production** : Plan "Business" ou "Pro" avec base de données MySQL/PostgreSQL

## 🚀 Étapes de Déploiement

### 1. Préparation du Projet

#### A. Vérification des dépendances
Votre projet utilise déjà les bonnes dépendances :
- Django 4.2.7+
- SQLite (inclus) ou MySQL/PostgreSQL
- ReportLab pour les PDF
- Bootstrap pour l'interface

#### B. Configuration pour LWS
- Créer un fichier `settings_lws.py`
- Configurer la base de données
- Optimiser pour l'hébergement partagé

### 2. Upload sur LWS

#### A. Via FTP/SFTP (Recommandé)
```bash
# Utiliser FileZilla, WinSCP ou un client FTP
# Se connecter avec vos identifiants LWS
# Uploader tout le dossier du projet dans /www/
```

#### B. Via Git (si supporté)
```bash
# Dans le terminal LWS
git clone https://github.com/koudougoulaurent/appli_KBIS.git
cd appli_KBIS
```

### 3. Configuration de l'Environnement

#### A. Installation des dépendances
```bash
# Dans le terminal LWS
pip install -r requirements_production.txt
```

#### B. Configuration de la base de données
```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

### 4. Configuration du Serveur Web

#### A. Fichier .htaccess (Apache)
Créer le fichier `.htaccess` dans le dossier racine :

```apache
# Configuration pour Django sur LWS
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /appli_KBIS/wsgi.py/$1 [QSA,L]

# Configuration des fichiers statiques
Alias /static/ /www/appli_KBIS/staticfiles/
Alias /media/ /www/appli_KBIS/media/

# Sécurité
<Files "wsgi.py">
    Require all granted
</Files>

# Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>
```

#### B. Fichier wsgi.py
Modifier le fichier `wsgi.py` existant :

```python
import os
import sys

# Ajouter le chemin du projet
path = '/www/appli_KBIS'
if path not in sys.path:
    sys.path.append(path)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_lws')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 5. Configuration des Fichiers Statiques

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

## 📦 Packages Requis pour LWS

### Packages Python (requirements_production.txt)
```
Django>=4.2.7,<5.0
django-bootstrap5>=2.0
django-crispy-forms>=2.0
crispy-bootstrap5>=0.7
djangorestframework>=3.14.0
reportlab>=4.0.0
xhtml2pdf>=0.2.5
Pillow>=10.0.0
django-extensions>=3.2.0
whitenoise>=6.5.0
python-decouple>=3.8
```

### Packages Système (fournis par LWS)
- Python 3.8+ ou 3.9+
- Apache avec mod_wsgi
- MySQL/PostgreSQL (selon le plan)
- SQLite (toujours disponible)

## ⚙️ Configuration Spécifique LWS

### Fichier settings_lws.py
```python
"""
Configuration Django optimisée pour LWS Hosting.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurité
SECRET_KEY = os.environ.get('SECRET_KEY', 'votre-clé-secrète-production')
DEBUG = False

# Hosts autorisés
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'votre-domaine.com',
    'www.votre-domaine.com',
    '.lws.fr',  # Sous-domaines LWS
]

# Applications
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

# Base de données - SQLite par défaut
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 30,
        },
    }
}

# Pour MySQL (si vous avez un plan avec base de données)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'votre_nom_bdd',
#         'USER': 'votre_utilisateur',
#         'PASSWORD': 'votre_mot_de_passe',
#         'HOST': 'localhost',
#         'PORT': '3306',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

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

# Modèle utilisateur personnalisé
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
            'filename': BASE_DIR / 'logs' / 'django_lws.log',
            'formatter': 'verbose',
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
```

## 🔧 Scripts de Déploiement LWS

### Script de déploiement automatique
```bash
#!/bin/bash
# deploy_lws.sh

echo "🚀 Déploiement de l'application sur LWS..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Êtes-vous dans le bon répertoire ?"
    exit 1
fi

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements_production.txt

# Migrations
echo "🗄️ Exécution des migrations..."
python manage.py makemigrations
python manage.py migrate

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Création du superutilisateur (optionnel)
echo "👤 Création du superutilisateur..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com

echo "✅ Déploiement terminé !"
echo "🌐 Votre application est accessible sur votre domaine LWS"
```

## 🐛 Dépannage LWS

### Problèmes Courants

#### 1. Erreur 500 - Internal Server Error
- Vérifier les logs dans `/www/appli_KBIS/logs/`
- Vérifier la configuration du fichier `.htaccess`
- Vérifier les permissions des fichiers (755 pour les dossiers, 644 pour les fichiers)

#### 2. Fichiers statiques non chargés
```bash
# Re-collecter les fichiers statiques
python manage.py collectstatic --noinput

# Vérifier les permissions
chmod -R 755 staticfiles/
```

#### 3. Erreurs de base de données
```bash
# Vérifier les migrations
python manage.py showmigrations
python manage.py migrate --fake-initial
```

#### 4. Problèmes de permissions
```bash
# Corriger les permissions
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
chmod 755 manage.py
```

#### 5. Erreur "No module named 'django'"
```bash
# Vérifier l'installation de Django
pip list | grep Django
pip install Django>=4.2.7
```

## 📊 Avantages de LWS pour votre projet

### ✅ Points Forts
1. **Hébergement Python/Django** : Support natif
2. **Base de données** : MySQL/PostgreSQL disponibles
3. **SSL gratuit** : Certificats Let's Encrypt
4. **Support technique** : Assistance en français
5. **Prix compétitifs** : Plans à partir de 3€/mois
6. **Performance** : Serveurs en France

### 🎯 Recommandations
1. **Plan minimum** : "Python" (3-5€/mois)
2. **Base de données** : MySQL pour la production
3. **Domaine** : Utiliser votre propre domaine
4. **Sauvegarde** : Configurer les sauvegardes automatiques

## 🔒 Sécurité sur LWS

### Configuration Recommandée
1. **HTTPS** : Activer SSL/TLS
2. **Clé secrète** : Changer la SECRET_KEY
3. **Permissions** : Configurer correctement les droits
4. **Firewall** : Utiliser les outils de sécurité LWS

## 📈 Optimisation Performance

### Recommandations
1. **Cache** : Activer le cache Django
2. **Fichiers statiques** : Utiliser WhiteNoise
3. **Base de données** : Optimiser les requêtes
4. **Images** : Compresser les images

## 🆘 Support LWS

### Ressources
- [Documentation LWS](https://www.lws.fr/faq/)
- [Support technique](https://www.lws.fr/support/)
- [Forum communautaire](https://www.lws.fr/forum/)

### Contact
- **Support technique** : Via l'espace client LWS
- **Documentation** : FAQ LWS
- **Communauté** : Forum LWS

---

## ✅ Checklist de Déploiement LWS

- [ ] Compte LWS créé et plan activé
- [ ] Code uploadé via FTP/SFTP
- [ ] Dépendances installées
- [ ] Fichier `.htaccess` configuré
- [ ] Fichier `wsgi.py` modifié
- [ ] Configuration `settings_lws.py` créée
- [ ] Base de données migrée
- [ ] Fichiers statiques collectés
- [ ] Superutilisateur créé
- [ ] Tests de fonctionnement effectués
- [ ] SSL/HTTPS configuré
- [ ] Sauvegardes configurées

**🎉 Votre application Django est maintenant déployée sur LWS !**

## 💰 Coûts Estimés

- **Plan Python** : 3-5€/mois
- **Base de données MySQL** : +2-3€/mois
- **Domaine personnalisé** : 10-15€/an
- **Total mensuel** : 5-8€/mois

**Excellent rapport qualité/prix pour un hébergement Django professionnel !**

