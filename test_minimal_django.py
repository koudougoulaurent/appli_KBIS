#!/usr/bin/env python
"""Test minimal de Django pour identifier le problème 'packages'"""

import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    import django
    from django.conf import settings
    print("✅ Django et settings importés")
    
    # Test de configuration avec setup
    print("🔄 Tentative de django.setup()...")
    django.setup()
    print("✅ Django configuré avec succès!")
    
except Exception as e:
    print(f"❌ Erreur lors de django.setup(): {e}")
    import traceback
    traceback.print_exc()
    
    # Essayer de diagnostiquer le problème
    print("\n🔍 Diagnostic du problème...")
    
    # Vérifier les imports des applications une par une
    for app in ['core', 'proprietes', 'paiements', 'contrats', 'utilisateurs', 'notifications', 'bailleurs']:
        try:
            print(f"🔄 Test import {app}...")
            __import__(app)
            print(f"✅ {app} importé")
        except Exception as e2:
            print(f"❌ Erreur import {app}: {e2}")
            # Afficher plus de détails pour l'erreur
            if 'packages' in str(e2):
                print(f"   🔍 Erreur 'packages' détectée dans {app}")
                # Essayer d'importer les modules de l'app un par un
                try:
                    __import__(f'{app}.models')
                    print(f"   ✅ {app}.models importé")
                except Exception as e3:
                    print(f"   ❌ Erreur {app}.models: {e3}")
                
                try:
                    __import__(f'{app}.views')
                    print(f"   ✅ {app}.views importé")
                except Exception as e4:
                    print(f"   ❌ Erreur {app}.views: {e4}")
                
                try:
                    __import__(f'{app}.urls')
                    print(f"   ✅ {app}.urls importé")
                except Exception as e5:
                    print(f"   ❌ Erreur {app}.urls: {e5}")
    
    # Essayer de diagnostiquer le problème dans les settings
    print("\n🔍 Diagnostic des settings...")
    try:
        print(f"Settings module: {settings.SETTINGS_MODULE}")
        print(f"Installed apps: {settings.INSTALLED_APPS}")
    except Exception as e6:
        print(f"❌ Erreur lors de l'accès aux settings: {e6}")
    
    # Essayer de diagnostiquer le problème dans les imports des modèles
    print("\n🔍 Diagnostic des imports des modèles...")
    for app in ['core', 'proprietes', 'paiements', 'contrats', 'utilisateurs', 'notifications', 'bailleurs']:
        try:
            print(f"🔄 Test import {app}.models...")
            __import__(f'{app}.models')
            print(f"✅ {app}.models importé")
        except Exception as e7:
            print(f"❌ Erreur import {app}.models: {e7}")
            if 'packages' in str(e7):
                print(f"   🔍 Erreur 'packages' détectée dans {app}.models")
                # Essayer d'importer les modèles un par un
                try:
                    from importlib import import_module
                    module = import_module(f'{app}.models')
                    print(f"   📋 Modules disponibles dans {app}.models:")
                    for name in dir(module):
                        if not name.startswith('_'):
                            print(f"      - {name}")
                except Exception as e8:
                    print(f"   ❌ Erreur lors de l'exploration de {app}.models: {e8}")
