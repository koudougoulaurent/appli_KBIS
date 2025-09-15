#!/usr/bin/env python
"""
Script de déploiement sécurisé pour Render
Inclut la sauvegarde automatique des données
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        if result.stdout:
            print(f"📝 Sortie: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Échec")
        print(f"📝 Erreur: {e.stderr}")
        return False

def create_render_yaml():
    """Crée le fichier render.yaml avec configuration de base de données persistante"""
    render_config = {
        'services': [
            {
                'type': 'web',
                'name': 'appli-kbis',
                'env': 'python',
                'plan': 'free',
                'buildCommand': 'pip install -r requirements.txt && python manage.py migrate && python backup_render.py',
                'startCommand': 'python manage.py runserver 0.0.0.0:$PORT',
                'envVars': [
                    {
                        'key': 'DATABASE_URL',
                        'fromDatabase': {
                            'name': 'appli-kbis-db',
                            'property': 'connectionString'
                        }
                    },
                    {
                        'key': 'SECRET_KEY',
                        'generateValue': True
                    },
                    {
                        'key': 'DEBUG',
                        'value': 'False'
                    },
                    {
                        'key': 'ALLOWED_HOSTS',
                        'value': 'appli-kbis.onrender.com,.onrender.com'
                    }
                ]
            }
        ],
        'databases': [
            {
                'name': 'appli-kbis-db',
                'plan': 'free'
            }
        ]
    }
    
    with open('render.yaml', 'w') as f:
        import yaml
        yaml.dump(render_config, f, default_flow_style=False)
    
    print("✅ Fichier render.yaml créé avec configuration de base de données persistante")

def create_requirements_render():
    """Crée le fichier requirements.txt pour Render"""
    requirements = [
        'Django>=4.2.0,<5.0',
        'djangorestframework>=3.14.0',
        'django-crispy-forms>=2.0',
        'crispy-bootstrap5>=0.7',
        'whitenoise>=6.0.0',
        'psycopg2-binary>=2.9.0',
        'Pillow>=9.0.0',
        'reportlab>=3.6.0',
        'django-select2>=8.0.0',
        'PyYAML>=6.0',
    ]
    
    with open('requirements_render.txt', 'w') as f:
        f.write('\n'.join(requirements))
    
    print("✅ Fichier requirements_render.txt créé")

def create_startup_script():
    """Crée un script de démarrage sécurisé"""
    startup_script = '''#!/bin/bash
# Script de démarrage sécurisé pour Render

echo "🚀 Démarrage de l'application..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
sleep 10

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate --noinput

# Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrer l'application
echo "🌐 Démarrage du serveur..."
python manage.py runserver 0.0.0.0:$PORT
'''
    
    with open('startup.sh', 'w') as f:
        f.write(startup_script)
    
    # Rendre le script exécutable
    os.chmod('startup.sh', 0o755)
    
    print("✅ Script de démarrage créé")

def main():
    """Fonction principale"""
    print("🚀 Configuration du déploiement sécurisé pour Render")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Créer les fichiers de configuration
    create_render_yaml()
    create_requirements_render()
    create_startup_script()
    
    print("\n✅ Configuration terminée!")
    print("\n📋 Prochaines étapes:")
    print("1. Connectez-vous à Render")
    print("2. Créez une nouvelle base de données PostgreSQL")
    print("3. Déployez l'application avec le fichier render.yaml")
    print("4. Configurez les variables d'environnement")
    print("5. L'application sera déployée avec persistance des données")

if __name__ == '__main__':
    main()
