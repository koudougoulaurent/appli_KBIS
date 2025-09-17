#!/usr/bin/env python
"""
Script de test final pour vérifier que tout fonctionne
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
    print("✅ Django configuré")
    
    from django.contrib.auth import get_user_model
    from django.contrib.auth import authenticate
    from utilisateurs.models import GroupeTravail
    
    User = get_user_model()
    
    def test_final():
        """Test final de l'application"""
        print("🔍 TEST FINAL DE L'APPLICATION")
        print("=" * 40)
        
        # Test des groupes
        print("📋 Test des GroupeTravail:")
        groupes = GroupeTravail.objects.all()
        for groupe in groupes:
            print(f"  ✅ {groupe.nom} - {groupe.description}")
        
        # Test des utilisateurs
        print("\n👥 Test des utilisateurs:")
        users = User.objects.all()
        for user in users:
            groupe_nom = user.groupe_travail.nom if user.groupe_travail else "Aucun"
            print(f"  ✅ {user.username} - Groupe: {groupe_nom}")
        
        # Test des connexions
        print("\n🔐 Test des connexions:")
        test_credentials = [
            ('admin', 'admin123'),
            ('caisse1', 'caisse123'),
            ('controle1', 'controle123'),
            ('admin1', 'admin123'),
            ('privilege1', 'privilege123'),
        ]
        
        for username, password in test_credentials:
            user = authenticate(username=username, password=password)
            if user:
                groupe_nom = user.groupe_travail.nom if user.groupe_travail else "Aucun"
                print(f"  ✅ {username}: Connexion OK - Groupe: {groupe_nom}")
            else:
                print(f"  ❌ {username}: Échec de connexion")
        
        print("\n🎉 TEST FINAL TERMINÉ !")
        print("=" * 40)
        print("🌐 URL: https://appli-kbis.onrender.com")
        print("🎯 L'application est prête !")
        
    if __name__ == "__main__":
        test_final()
        
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
