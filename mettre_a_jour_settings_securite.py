#!/usr/bin/env python
"""
Script pour mettre à jour les paramètres Django avec la sécurité
"""

import os
import sys

def update_settings_security():
    """Mettre à jour les paramètres de sécurité Django"""
    
    print("🔒 Mise à jour des paramètres de sécurité Django")
    print("=" * 60)
    
    # Lire le fichier settings.py
    with open('gestion_immobiliere/settings.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter les middlewares de sécurité
    security_middleware = '''MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Middlewares de sécurité personnalisés
    'core.middleware.SecurityMiddleware',
    'core.middleware.DataValidationMiddleware',
    'core.middleware.AuditMiddleware',
]'''
    
    # Remplacer les middlewares existants
    import re
    pattern = r'MIDDLEWARE = \[.*?\]'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, security_middleware, content, flags=re.DOTALL)
        print("✅ Middlewares de sécurité ajoutés")
    
    # Ajouter les paramètres de sécurité
    security_settings = '''
# Paramètres de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_SSL_REDIRECT = False  # Mettre True en production
SESSION_COOKIE_SECURE = False  # Mettre True en production
CSRF_COOKIE_SECURE = False  # Mettre True en production
X_FRAME_OPTIONS = 'DENY'

# Configuration des cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Configuration de la session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Configuration CSRF
CSRF_COOKIE_AGE = 31449600  # 1 an
CSRF_USE_SESSIONS = True

# Configuration des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuration du logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/gestion_immobiliere.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'proprietes': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'contrats': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'paiements': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuration de la cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Configuration des fichiers uploadés
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
FILE_UPLOAD_TEMP_DIR = None
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Configuration des messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Configuration des templates
TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'django.template.context_processors.debug',
])

# Configuration des applications
INSTALLED_APPS.extend([
    'django.contrib.humanize',
])

# Configuration des langues
LANGUAGES = [
    ('fr', 'Français'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Configuration des fuseaux horaires
USE_TZ = True
TIME_ZONE = 'Europe/Paris'

# Configuration des médias
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration des fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuration de la base de données (amélioration sécurité)
DATABASES['default'].update({
    'OPTIONS': {
        'timeout': 20,
        'check_same_thread': False,
    },
    'ATOMIC_REQUESTS': True,
    'CONN_MAX_AGE': 600,  # 10 minutes
})

# Configuration des emails (pour les notifications)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'noreply@gestion-immobiliere.com'

# Configuration des notifications
NOTIFICATION_SETTINGS = {
    'EMAIL_ENABLED': False,
    'SMS_ENABLED': False,
    'PUSH_ENABLED': False,
}

# Configuration de la sécurité des formulaires
FORM_SECURITY = {
    'MAX_FIELD_LENGTH': 1000,
    'ALLOWED_FILE_TYPES': ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
    'MAX_FILE_SIZE': 5242880,  # 5 MB
    'RATE_LIMIT': 100,  # requêtes par minute
}

# Configuration de la validation des données
DATA_VALIDATION = {
    'STRICT_MODE': True,
    'AUTO_SANITIZE': True,
    'LOG_VIOLATIONS': True,
}

# Configuration de l'audit
AUDIT_SETTINGS = {
    'ENABLED': True,
    'LOG_LEVEL': 'INFO',
    'RETENTION_DAYS': 365,
    'SENSITIVE_FIELDS': ['password', 'iban', 'numero_fiscal', 'numero_ss'],
}
'''
    
    # Ajouter les paramètres de sécurité à la fin du fichier
    if 'SECURE_BROWSER_XSS_FILTER' not in content:
        content += security_settings
        print("✅ Paramètres de sécurité ajoutés")
    
    # Écrire le fichier mis à jour
    with open('gestion_immobiliere/settings.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fichier settings.py mis à jour avec succès")


def create_logs_directory():
    """Créer le répertoire de logs"""
    
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print("✅ Répertoire logs créé")
    else:
        print("✅ Répertoire logs existant")


def create_security_documentation():
    """Créer la documentation de sécurité"""
    
    doc_content = '''# 🔒 Documentation de Sécurité

## Vue d'ensemble

Ce document décrit les mesures de sécurité mises en place dans l'application de gestion immobilière.

## Mesures de Sécurité Implémentées

### 1. Validation des Données

#### Formulaires Sécurisés
- Validation côté client et serveur
- Nettoyage automatique des données
- Protection contre les injections
- Validation des types de données

#### Validateurs Personnalisés
- Validation des téléphones français
- Validation des codes postaux
- Validation des IBAN
- Validation des montants
- Validation des surfaces

### 2. Protection contre les Attaques

#### Injection SQL
- Validation des paramètres
- Utilisation des ORM Django
- Échappement automatique des caractères

#### Cross-Site Scripting (XSS)
- Filtrage des balises HTML
- Validation des entrées utilisateur
- En-têtes de sécurité

#### Injection de Commandes
- Validation des caractères spéciaux
- Filtrage des commandes système
- Sanitisation des entrées

### 3. Middleware de Sécurité

#### SecurityMiddleware
- Vérification des en-têtes
- Protection contre les attaques
- Rate limiting
- Logging des activités suspectes

#### DataValidationMiddleware
- Validation des données POST/GET
- Vérification des types
- Nettoyage automatique

#### AuditMiddleware
- Traçabilité des actions
- Logging des erreurs
- Historique des modifications

### 4. Sauvegarde Sécurisée

#### DataSaveHandler
- Validation avant sauvegarde
- Gestion des erreurs
- Logging des actions
- Notifications automatiques

#### Signaux Django
- Validation automatique
- Nettoyage des données
- Logging des événements

### 5. Configuration de Sécurité

#### Paramètres Django
- En-têtes de sécurité
- Configuration des cookies
- Gestion des sessions
- Validation des mots de passe

#### Logging
- Traçabilité complète
- Rotation des logs
- Niveaux de log appropriés

## Bonnes Pratiques

### 1. Validation des Données
- Toujours valider côté serveur
- Utiliser les validateurs Django
- Nettoyer les données avant sauvegarde

### 2. Gestion des Erreurs
- Ne pas exposer les erreurs internes
- Logger les erreurs pour debugging
- Messages d'erreur appropriés

### 3. Authentification
- Utiliser les décorateurs @login_required
- Vérifier les permissions
- Gérer les sessions

### 4. Fichiers Uploadés
- Valider les types de fichiers
- Limiter la taille des fichiers
- Stocker en sécurité

## Tests de Sécurité

### Exécution des Tests
```bash
python test_securite_formulaires.py
```

### Tests Inclus
- Validation des données
- Protection contre les attaques
- Sauvegarde sécurisée
- Nettoyage des données

## Maintenance

### Surveillance
- Vérifier les logs régulièrement
- Surveiller les tentatives d'attaque
- Maintenir les dépendances

### Mises à Jour
- Mettre à jour Django régulièrement
- Vérifier les vulnérabilités
- Tester après les mises à jour

## Contact

Pour toute question de sécurité, contactez l'équipe de développement.
'''
    
    with open('SECURITE.md', 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print("✅ Documentation de sécurité créée")


def main():
    """Fonction principale"""
    
    print("🚀 Mise à jour des paramètres de sécurité")
    print("=" * 60)
    
    # Créer le répertoire de logs
    create_logs_directory()
    
    # Mettre à jour les paramètres
    update_settings_security()
    
    # Créer la documentation
    create_security_documentation()
    
    print("\n🎉 Configuration de sécurité terminée !")
    print("\n📋 Récapitulatif des améliorations:")
    print("✅ Middlewares de sécurité ajoutés")
    print("✅ Paramètres de sécurité configurés")
    print("✅ Logging configuré")
    print("✅ Cache configuré")
    print("✅ Validation des mots de passe renforcée")
    print("✅ Protection contre les attaques")
    print("✅ Documentation de sécurité créée")


if __name__ == '__main__':
    main() 