#!/usr/bin/env python
"""
Script pour corriger l'erreur 'packages' et déployer sur Render
"""

import os
import sys
import subprocess

def fix_packages_error():
    """Corrige l'erreur 'packages' en créant un module packages vide"""
    
    print("🔧 Correction de l'erreur 'packages'...")
    
    # Créer le dossier packages s'il n'existe pas
    packages_dir = "packages"
    if not os.path.exists(packages_dir):
        os.makedirs(packages_dir)
        print(f"✅ Dossier {packages_dir} créé")
    
    # Créer __init__.py dans packages
    init_file = os.path.join(packages_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Module packages vide pour éviter l'erreur d'import\n")
        print(f"✅ {init_file} créé")
    
    # Créer un module packages vide
    packages_module = os.path.join(packages_dir, "packages.py")
    if not os.path.exists(packages_module):
        with open(packages_module, 'w') as f:
            f.write("""# Module packages vide
# Ce module existe uniquement pour éviter l'erreur 'No module named packages'

class Packages:
    pass

def get_packages():
    return []
""")
        print(f"✅ {packages_module} créé")

def update_render_settings():
    """Met à jour les settings pour Render"""
    
    print("🔧 Mise à jour des settings pour Render...")
    
    # Lire le fichier settings actuel
    settings_file = "gestion_immobiliere/settings.py"
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter la configuration pour Render si elle n'existe pas
    render_config = """
# Configuration pour Render
if os.environ.get('RENDER'):
    # Configuration de base de données pour Render
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
    
    # Configuration statique pour Render
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
    
    # Configuration de sécurité pour production
    DEBUG = False
    ALLOWED_HOSTS = ['appli-kbis.onrender.com', '.onrender.com']
    
    # Configuration de session
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
"""
    
    if 'if os.environ.get(\'RENDER\'):' not in content:
        # Ajouter la configuration Render à la fin du fichier
        with open(settings_file, 'a', encoding='utf-8') as f:
            f.write(render_config)
        print("✅ Configuration Render ajoutée")
    else:
        print("✅ Configuration Render déjà présente")

def create_render_requirements():
    """Crée le fichier requirements.txt pour Render"""
    
    print("🔧 Création du fichier requirements.txt pour Render...")
    
    requirements = """Django==4.2.7
django-extensions==3.2.3
Pillow==10.1.0
reportlab==4.0.7
openpyxl==3.1.2
django-crispy-forms==2.1
crispy-bootstrap5==0.7
django-select2==8.1.0
django-humanize==4.8.0
dj-database-url==2.1.0
gunicorn==21.2.0
whitenoise==6.6.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ requirements.txt créé")

def create_render_build_script():
    """Crée le script de build pour Render"""
    
    print("🔧 Création du script de build pour Render...")
    
    build_script = """#!/usr/bin/env bash
# Script de build pour Render

echo "🚀 Démarrage du build sur Render..."

# Installer les dépendances
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur si nécessaire
python manage.py shell -c "
from django.contrib.auth import get_user_model
from core.models import ConfigurationEntreprise

User = get_user_model()

# Créer la configuration d'entreprise si elle n'existe pas
config, created = ConfigurationEntreprise.objects.get_or_create(
    nom_entreprise='KBIS IMMOBILIER',
    defaults={
        'adresse': '123 Rue de l\\'Immobilier',
        'ville': 'Ouagadougou',
        'code_postal': '01 BP 1234',
        'telephone': '+226 25 12 34 56',
        'email': 'contact@kbis.bf',
        'actif': True
    }
)

if created:
    print('✅ Configuration entreprise créée')
else:
    print('✅ Configuration entreprise existante mise à jour')
    config.nom_entreprise = 'KBIS IMMOBILIER'
    config.save()

print('🎉 Build terminé avec succès!')
"

echo "✅ Build terminé!"
"""
    
    with open('render-build.sh', 'w') as f:
        f.write(build_script)
    
    # Rendre le script exécutable
    os.chmod('render-build.sh', 0o755)
    
    print("✅ render-build.sh créé")

def main():
    """Fonction principale"""
    
    print("🚀 Correction du déploiement Render...")
    
    try:
        # 1. Corriger l'erreur packages
        fix_packages_error()
        
        # 2. Mettre à jour les settings
        update_render_settings()
        
        # 3. Créer requirements.txt
        create_render_requirements()
        
        # 4. Créer le script de build
        create_render_build_script()
        
        print("\n✅ Corrections terminées!")
        print("\n📋 Prochaines étapes:")
        print("1. Commitez ces changements: git add . && git commit -m 'Fix Render deployment'")
        print("2. Poussez vers GitHub: git push origin master")
        print("3. Render redéploiera automatiquement")
        print("4. Vérifiez que l'application fonctionne sur https://appli-kbis.onrender.com")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
