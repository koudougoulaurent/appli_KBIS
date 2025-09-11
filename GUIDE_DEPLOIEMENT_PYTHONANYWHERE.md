# Guide de Déploiement sur PythonAnywhere

## 📋 Prérequis

1. **Compte PythonAnywhere** : Créez un compte sur [pythonanywhere.com](https://www.pythonanywhere.com)
2. **Plan recommandé** : "Hacker" (gratuit) pour commencer, puis "Beginner" ou "Web Developer" pour la production

## 🚀 Étapes de Déploiement

### 1. Préparation du Projet

#### A. Mise à jour du fichier requirements.txt
```bash
# Installer les dépendances manquantes localement d'abord
pip install reportlab xhtml2pdf pillow django-crispy-forms django-bootstrap5 djangorestframework
pip freeze > requirements.txt
```

#### B. Configuration pour la production
- Créer un fichier `settings_production.py`
- Configurer les variables d'environnement
- Désactiver le mode DEBUG

### 2. Upload sur PythonAnywhere

#### A. Via Git (Recommandé)
```bash
# Sur PythonAnywhere, dans le terminal
git clone https://github.com/koudougoulaurent/appli_KBIS.git
cd appli_KBIS
```

#### B. Via Upload de fichiers
- Utiliser l'interface web de PythonAnywhere
- Uploader le dossier complet du projet

### 3. Configuration de l'Environnement

#### A. Installation des dépendances
```bash
# Dans le terminal PythonAnywhere
pip3.10 install --user -r requirements.txt
```

#### B. Configuration de la base de données
```bash
# Migrations
python3.10 manage.py makemigrations
python3.10 manage.py migrate

# Créer un superutilisateur
python3.10 manage.py createsuperuser
```

### 4. Configuration du Serveur Web

#### A. Fichier WSGI
Créer le fichier `/var/www/votre_username_pythonanywhere_com_wsgi.py` :

```python
import os
import sys

# Ajouter le chemin du projet
path = '/home/votre_username/appli_KBIS'
if path not in sys.path:
    sys.path.append(path)

# Configuration Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_production'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### B. Configuration des fichiers statiques
```bash
# Collecter les fichiers statiques
python3.10 manage.py collectstatic --noinput
```

### 5. Configuration des Domaines

#### A. Domaine personnalisé (optionnel)
- Dans l'onglet "Web" de PythonAnywhere
- Ajouter votre domaine personnalisé
- Configurer les enregistrements DNS

#### B. Sous-domaine PythonAnywhere
- Utiliser le sous-domaine fourni : `votre_username.pythonanywhere.com`

## 📦 Packages Requis

### Packages Python
```
Django>=4.2.7
django-bootstrap5>=2.0
django-crispy-forms>=2.0
crispy-bootstrap5>=0.7
djangorestframework>=3.14.0
reportlab>=4.0.0
xhtml2pdf>=0.2.5
Pillow>=10.0.0
django-extensions>=3.2.0
whitenoise>=6.5.0
gunicorn>=21.2.0
```

### Packages Système (installés automatiquement)
- Python 3.10
- SQLite3
- Git

## ⚙️ Configuration de Production

### Variables d'Environnement
```python
# Dans settings_production.py
import os

DEBUG = False
ALLOWED_HOSTS = ['votre_username.pythonanywhere.com', 'votre-domaine.com']

# Base de données (SQLite par défaut)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Sécurité
SECRET_KEY = os.environ.get('SECRET_KEY', 'votre-clé-secrète-production')
```

## 🔧 Scripts de Déploiement

### Script de déploiement automatique
```bash
#!/bin/bash
# deploy.sh

echo "🚀 Déploiement de l'application sur PythonAnywhere..."

# Mise à jour du code
git pull origin master

# Installation des dépendances
pip3.10 install --user -r requirements.txt

# Migrations
python3.10 manage.py makemigrations
python3.10 manage.py migrate

# Collecte des fichiers statiques
python3.10 manage.py collectstatic --noinput

# Redémarrage du serveur web
touch /var/www/votre_username_pythonanywhere_com_wsgi.py

echo "✅ Déploiement terminé !"
```

## 🐛 Dépannage

### Problèmes Courants

#### 1. Erreur 500
- Vérifier les logs dans l'onglet "Web" de PythonAnywhere
- Vérifier la configuration WSGI
- Vérifier les permissions des fichiers

#### 2. Fichiers statiques non chargés
```bash
# Re-collecter les fichiers statiques
python3.10 manage.py collectstatic --noinput
```

#### 3. Erreurs de base de données
```bash
# Vérifier les migrations
python3.10 manage.py showmigrations
python3.10 manage.py migrate --fake-initial
```

#### 4. Problèmes de permissions
```bash
# Vérifier les permissions
chmod 755 /home/votre_username/appli_KBIS
chmod 644 /home/votre_username/appli_KBIS/*.py
```

## 📊 Monitoring et Maintenance

### Logs
- Consulter les logs dans l'onglet "Web" de PythonAnywhere
- Logs d'erreur Django dans `/home/votre_username/logs/`

### Sauvegarde
```bash
# Sauvegarde de la base de données
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

### Mise à jour
```bash
# Mise à jour du code
git pull origin master
pip3.10 install --user -r requirements.txt
python3.10 manage.py migrate
python3.10 manage.py collectstatic --noinput
touch /var/www/votre_username_pythonanywhere_com_wsgi.py
```

## 🔒 Sécurité

### Recommandations
1. **Changer la clé secrète** : Générer une nouvelle `SECRET_KEY` pour la production
2. **HTTPS** : Configurer SSL/TLS (gratuit sur PythonAnywhere)
3. **Variables d'environnement** : Utiliser des variables d'environnement pour les données sensibles
4. **Firewall** : Configurer les règles de pare-feu si nécessaire

### Configuration HTTPS
- Dans l'onglet "Web" de PythonAnywhere
- Activer "Force HTTPS"
- Configurer les certificats SSL

## 📈 Optimisation

### Performance
1. **Cache** : Activer le cache Django
2. **Base de données** : Optimiser les requêtes
3. **Fichiers statiques** : Utiliser un CDN si nécessaire

### Monitoring
- Utiliser les outils de monitoring de PythonAnywhere
- Configurer des alertes pour les erreurs

## 🆘 Support

### Ressources
- [Documentation PythonAnywhere](https://help.pythonanywhere.com/)
- [Documentation Django](https://docs.djangoproject.com/)
- [Forum PythonAnywhere](https://www.pythonanywhere.com/forums/)

### Contact
- Support PythonAnywhere : support@pythonanywhere.com
- Documentation du projet : Voir les fichiers README.md

---

## ✅ Checklist de Déploiement

- [ ] Compte PythonAnywhere créé
- [ ] Code uploadé (Git ou fichiers)
- [ ] Dépendances installées
- [ ] Base de données migrée
- [ ] Fichier WSGI configuré
- [ ] Fichiers statiques collectés
- [ ] Configuration de production appliquée
- [ ] Tests de fonctionnement effectués
- [ ] HTTPS configuré
- [ ] Monitoring mis en place

**🎉 Votre application est maintenant déployée sur PythonAnywhere !**

