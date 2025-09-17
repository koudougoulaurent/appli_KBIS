#!/usr/bin/env python
"""
Script de diagnostic pour identifier le problème 'No module named packages'
"""

import os
import sys
import traceback

# Ajouter le répertoire du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Teste les imports un par un pour identifier le problème"""
    
    print("🔍 Diagnostic du problème 'No module named packages'")
    print("=" * 60)
    
    # Test 1: Import des settings
    print("\n1. Test import settings...")
    try:
        from gestion_immobiliere import settings
        print("✅ Settings importé avec succès")
    except Exception as e:
        print(f"❌ Erreur import settings: {e}")
        traceback.print_exc()
        return
    
    # Test 2: Import des apps
    print("\n2. Test import des applications...")
    apps = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications']
    
    for app in apps:
        try:
            module = __import__(app)
            print(f"✅ {app} importé avec succès")
        except Exception as e:
            print(f"❌ Erreur import {app}: {e}")
            if 'packages' in str(e):
                print(f"   🎯 PROBLÈME TROUVÉ dans {app}!")
                traceback.print_exc()
    
    # Test 3: Import des modèles
    print("\n3. Test import des modèles...")
    try:
        import core.models
        print("✅ Modèles core importés")
    except Exception as e:
        print(f"❌ Erreur modèles core: {e}")
        if 'packages' in str(e):
            print("   🎯 PROBLÈME TROUVÉ dans core.models!")
            traceback.print_exc()
    
    try:
        import utilisateurs.models
        print("✅ Modèles utilisateurs importés")
    except Exception as e:
        print(f"❌ Erreur modèles utilisateurs: {e}")
        if 'packages' in str(e):
            print("   🎯 PROBLÈME TROUVÉ dans utilisateurs.models!")
            traceback.print_exc()
    
    # Test 4: Import des vues
    print("\n4. Test import des vues...")
    try:
        import core.views
        print("✅ Vues core importées")
    except Exception as e:
        print(f"❌ Erreur vues core: {e}")
        if 'packages' in str(e):
            print("   🎯 PROBLÈME TROUVÉ dans core.views!")
            traceback.print_exc()
    
    try:
        import utilisateurs.views
        print("✅ Vues utilisateurs importées")
    except Exception as e:
        print(f"❌ Erreur vues utilisateurs: {e}")
        if 'packages' in str(e):
            print("   🎯 PROBLÈME TROUVÉ dans utilisateurs.views!")
            traceback.print_exc()

if __name__ == "__main__":
    test_imports()
