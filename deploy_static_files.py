#!/usr/bin/env python
"""
Script pour collecter et déployer les fichiers statiques sur Render
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def collect_static_files():
    """Collecter tous les fichiers statiques"""
    print("🚀 COLLECTE DES FICHIERS STATIQUES POUR RENDER")
    print("=" * 50)
    
    try:
        # Collecter les fichiers statiques
        print("📁 Collecte des fichiers statiques...")
        call_command('collectstatic', '--noinput', '--clear')
        print("✅ Fichiers statiques collectés avec succès")
        
        # Vérifier que l'image est bien collectée
        static_root = settings.STATIC_ROOT
        image_path = static_root / 'images' / 'company' / 'kbis-modern-building.svg'
        
        if image_path.exists():
            print(f"✅ Image trouvée: {image_path}")
            print(f"📏 Taille: {image_path.stat().st_size} bytes")
        else:
            print(f"❌ Image non trouvée: {image_path}")
            
        # Lister les fichiers collectés
        print("\n📋 Fichiers collectés dans staticfiles/:")
        for root, dirs, files in os.walk(static_root):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), static_root)
                print(f"   - {rel_path}")
        
        print("\n🎉 COLLECTE TERMINÉE !")
        print("📤 Prêt pour le déploiement sur Render")
        
    except Exception as e:
        print(f"❌ Erreur lors de la collecte: {e}")
        return False
    
    return True

def check_static_config():
    """Vérifier la configuration des fichiers statiques"""
    print("\n🔍 VÉRIFICATION DE LA CONFIGURATION")
    print("=" * 40)
    
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    
    # Vérifier que les dossiers existent
    for static_dir in settings.STATICFILES_DIRS:
        if static_dir.exists():
            print(f"✅ Dossier source trouvé: {static_dir}")
        else:
            print(f"❌ Dossier source manquant: {static_dir}")
    
    if settings.STATIC_ROOT.exists():
        print(f"✅ Dossier de collecte trouvé: {settings.STATIC_ROOT}")
    else:
        print(f"❌ Dossier de collecte manquant: {settings.STATIC_ROOT}")

if __name__ == "__main__":
    check_static_config()
    collect_static_files()
