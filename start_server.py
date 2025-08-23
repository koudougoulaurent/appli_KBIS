#!/usr/bin/env python
"""
Script simple pour démarrer le serveur Django et diagnostiquer les problèmes
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
    print("✅ Django configuré avec succès")
except Exception as e:
    print(f"❌ Erreur lors de la configuration Django: {e}")
    sys.exit(1)

try:
    from django.core.management import execute_from_command_line
    print("✅ Gestion Django importée avec succès")
except Exception as e:
    print(f"❌ Erreur lors de l'import de la gestion Django: {e}")
    sys.exit(1)

try:
    # Vérifier la configuration
    from django.conf import settings
    print(f"✅ Configuration Django chargée")
    print(f"   - DEBUG: {settings.DEBUG}")
    print(f"   - ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"   - DATABASES: {list(settings.DATABASES.keys())}")
    
    # Vérifier les modèles
    from core.models import HardDeleteLog
    print(f"✅ Modèle HardDeleteLog accessible")
    
    # Vérifier les URLs
    from django.urls import reverse
    try:
        url = reverse('core:secure_deletion_dashboard')
        print(f"✅ URL dashboard accessible: {url}")
    except Exception as e:
        print(f"⚠ URL dashboard non accessible: {e}")
    
except Exception as e:
    print(f"❌ Erreur lors de la vérification: {e}")
    sys.exit(1)

print("\n🚀 Tentative de démarrage du serveur...")
print("Appuyez sur Ctrl+C pour arrêter le serveur")

try:
    # Démarrer le serveur
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
except KeyboardInterrupt:
    print("\n✅ Serveur arrêté par l'utilisateur")
except Exception as e:
    print(f"\n❌ Erreur lors du démarrage du serveur: {e}")
    import traceback
    traceback.print_exc()






