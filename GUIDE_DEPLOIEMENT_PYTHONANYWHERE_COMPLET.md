# Guide de Déploiement Complet sur PythonAnywhere (Gratuit)

## 📋 Packages Nécessaires

### Installation des Packages

```bash
# Se connecter à PythonAnywhere et installer les packages
pip3.10 install --user -r requirements_pythonanywhere.txt
```

### Liste Complète des Packages

#### 🎯 Packages Essentiels
- **Django>=4.2.7,<5.0** - Framework principal
- **django-bootstrap5>=2.0** - Interface utilisateur
- **django-crispy-forms>=2.0** - Formulaires stylés
- **crispy-bootstrap5>=0.7** - Templates Bootstrap pour crispy
- **djangorestframework>=3.14.0** - API REST
- **whitenoise>=6.5.0** - ⭐ ESSENTIEL pour servir les fichiers statiques

#### 📄 Génération PDF
- **reportlab>=4.0.0** - Génération de PDF
- **xhtml2pdf>=0.2.5** - Conversion HTML vers PDF
- **Pillow>=10.0.0** - Traitement d'images
- **fonttools>=4.0.0** - Gestion des polices
- **PyPDF2>=3.0.0** - Compression PDF

#### 🔧 Utilitaires
- **django-extensions>=3.2.0** - Extensions Django
- **django-cors-headers>=4.0.0** - CORS
- **django-environ>=0.10.0** - Variables d'environnement
- **python-decouple>=3.8** - Configuration
- **python-dotenv>=1.0.0** - Fichiers .env

## 🚀 Étapes de Déploiement

### 1. Préparation du Projet

```bash
# Dans votre projet local, créer un fichier .env
echo "DEBUG=False" > .env
echo "SECRET_KEY=votre-secret-key-securise" >> .env
echo "ALLOWED_HOSTS=votre-nom.pythonanywhere.com" >> .env
```

### 2. Upload sur PythonAnywhere

1. **Créer un compte gratuit** sur [pythonanywhere.com](https://pythonanywhere.com)
2. **Uploader votre projet** via l'interface web ou Git
3. **Se connecter au Bash Console**

### 3. Installation des Dépendances

```bash
# Dans le Bash Console de PythonAnywhere
cd /home/votre-nom/votre-projet
pip3.10 install --user -r requirements_pythonanywhere.txt
```

### 4. Configuration de la Base de Données

```bash
# Migrations
python3.10 manage.py makemigrations
python3.10 manage.py migrate

# Créer un superutilisateur
python3.10 manage.py createsuperuser

# Collecter les fichiers statiques
python3.10 manage.py collectstatic --noinput
```

### 5. Configuration WSGI

Créer/modifier le fichier `/var/www/votre-nom_pythonanywhere_com_wsgi.py` :

```python
import os
import sys

# Ajouter le chemin de votre projet
path = '/home/votre-nom/votre-projet'
if path not in sys.path:
    sys.path.append(path)

# Configuration Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_production'

# Import de l'application Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 6. Configuration des Fichiers Statiques

Dans l'onglet **Web** de PythonAnywhere :

- **Static files**: `/static/` → `/home/votre-nom/votre-projet/staticfiles/`
- **Media files**: `/media/` → `/home/votre-nom/votre-projet/media/`

## ⚙️ Configuration de Production

### Settings de Production pour PythonAnywhere

Créer `gestion_immobiliere/settings_production.py` :

```python
from .settings import *
import os

# Sécurité
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'votre-secret-key-securise')

# Hosts autorisés
ALLOWED_HOSTS = [
    'votre-nom.pythonanywhere.com',
    'www.votre-nom.pythonanywhere.com',
]

# Base de données (SQLite pour le gratuit)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Fichiers statiques avec WhiteNoise
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware avec WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ⭐ ESSENTIEL
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Logging pour PythonAnywhere
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}
```

## 🔧 Commandes de Déploiement

### Script de Déploiement Automatique

Créer `deploy_pythonanywhere.sh` :

```bash
#!/bin/bash
echo "🚀 Déploiement sur PythonAnywhere..."

# Installation des packages
echo "📦 Installation des packages..."
pip3.10 install --user -r requirements_pythonanywhere.txt

# Migrations
echo "🗄️ Application des migrations..."
python3.10 manage.py makemigrations
python3.10 manage.py migrate

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python3.10 manage.py collectstatic --noinput

# Création du superutilisateur (si nécessaire)
echo "👤 Création du superutilisateur..."
python3.10 manage.py createsuperuser --noinput --username admin --email admin@example.com

echo "✅ Déploiement terminé !"
echo "🌐 Votre application est disponible sur : https://votre-nom.pythonanywhere.com"
```

## 📊 Limitations du Plan Gratuit

### ⚠️ Restrictions PythonAnywhere Gratuit
- **3 applications web** maximum
- **512 MB RAM** par application
- **1 CPU** par application
- **Pas de tâches cron** (scheduled tasks)
- **Pas d'accès SSH** (seulement Bash Console)
- **Trafic limité** (100 secondes CPU/jour)

### 🎯 Optimisations Recommandées
1. **Utiliser SQLite** (inclus, pas de coût)
2. **Activer WhiteNoise** pour les fichiers statiques
3. **Désactiver DEBUG** en production
4. **Optimiser les requêtes** de base de données
5. **Utiliser le cache** Django

## 🐛 Résolution des Problèmes Courants

### Erreur "No module named"
```bash
# Vérifier l'installation
pip3.10 list --user

# Réinstaller si nécessaire
pip3.10 install --user --upgrade nom-du-package
```

### Erreur de fichiers statiques
```bash
# Vérifier WhiteNoise
python3.10 manage.py collectstatic --noinput

# Vérifier la configuration
python3.10 manage.py check --deploy
```

### Erreur de base de données
```bash
# Vérifier les migrations
python3.10 manage.py showmigrations

# Appliquer les migrations
python3.10 manage.py migrate
```

## 📈 Monitoring et Maintenance

### Vérification de l'Application
```bash
# Tester l'application
python3.10 manage.py check --deploy

# Vérifier les logs
tail -f /var/log/votre-nom.pythonanywhere.com.error.log
```

### Sauvegarde de la Base de Données
```bash
# Sauvegarder SQLite
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

## 🎉 Résultat Final

Après déploiement, votre application sera accessible sur :
- **URL principale** : `https://votre-nom.pythonanywhere.com`
- **Interface admin** : `https://votre-nom.pythonanywhere.com/admin/`
- **API REST** : `https://votre-nom.pythonanywhere.com/api/`

## 📞 Support

En cas de problème :
1. Vérifier les logs dans l'onglet **Web** de PythonAnywhere
2. Consulter la documentation PythonAnywhere
3. Vérifier la configuration WSGI
4. Tester en local avec les mêmes settings

---

**Note** : Ce guide est optimisé pour le plan gratuit de PythonAnywhere. Pour des applications plus importantes, considérez un plan payant ou un autre hébergeur.
