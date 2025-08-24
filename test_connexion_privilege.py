#!/usr/bin/env python
"""
Script pour tester la connexion de l'utilisateur privilege1
Usage: python test_connexion_privilege.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import authenticate
from utilisateurs.models import GroupeTravail, Utilisateur

def test_connexion_privilege():
    """Teste la connexion de l'utilisateur privilege1"""
    print("🔐 Test de connexion pour l'utilisateur privilege1")
    print("=" * 50)
    
    # Test 1: Vérifier que l'utilisateur existe
    try:
        utilisateur = Utilisateur.objects.get(username='privilege1')
        print(f"✅ Utilisateur trouvé: {utilisateur.username}")
        print(f"   Nom complet: {utilisateur.get_nom_complet()}")
        print(f"   Email: {utilisateur.email}")
        print(f"   Est actif: {utilisateur.is_active}")
        print(f"   Est staff: {utilisateur.is_staff}")
        
    except Utilisateur.DoesNotExist:
        print("❌ Utilisateur privilege1 non trouvé!")
        print("   Exécutez d'abord: python creer_utilisateur_privilege.py")
        return False
    
    # Test 2: Vérifier le groupe
    if utilisateur.groupe_travail:
        print(f"   Groupe: {utilisateur.groupe_travail.nom}")
        print(f"   Groupe actif: {utilisateur.groupe_travail.actif}")
        
        if utilisateur.groupe_travail.nom == 'PRIVILEGE':
            print("   ✅ Groupe PRIVILEGE confirmé")
        else:
            print(f"   ⚠️  Groupe incorrect: {utilisateur.groupe_travail.nom}")
    else:
        print("   ❌ Aucun groupe assigné!")
        return False
    
    # Test 3: Authentification
    print(f"\n🔑 Test d'authentification...")
    user_auth = authenticate(username='privilege1', password='test123')
    
    if user_auth:
        print("   ✅ Authentification réussie!")
        print(f"   Utilisateur connecté: {user_auth.username}")
        print(f"   Groupe: {user_auth.get_groupe_display()}")
        
        # Test 4: Vérifier les permissions
        print(f"\n🔒 Test des permissions...")
        print(f"   Est utilisateur privilégié: {user_auth.is_privilege_user()}")
        print(f"   Peut gérer les profils: {user_auth.can_manage_profiles()}")
        
        modules = user_auth.get_accessible_modules()
        print(f"   Modules accessibles: {', '.join(modules)}")
        
        return True
        
    else:
        print("   ❌ Échec de l'authentification!")
        print("   Vérifiez le nom d'utilisateur et le mot de passe")
        return False

def verifier_groupe_privilege():
    """Vérifie que le groupe PRIVILEGE existe et est configuré"""
    print(f"\n🏢 Vérification du groupe PRIVILEGE...")
    
    try:
        groupe = GroupeTravail.objects.get(nom='PRIVILEGE')
        print(f"   ✅ Groupe PRIVILEGE trouvé")
        print(f"   Description: {groupe.description}")
        print(f"   Actif: {groupe.actif}")
        
        permissions = groupe.permissions
        if 'modules' in permissions:
            modules = permissions['modules']
            print(f"   Modules autorisés: {', '.join(modules)}")
        
        return True
        
    except GroupeTravail.DoesNotExist:
        print("   ❌ Groupe PRIVILEGE non trouvé!")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test de connexion pour l'utilisateur privilege1")
    print("=" * 60)
    
    # Vérifier le groupe
    groupe_ok = verifier_groupe_privilege()
    
    if not groupe_ok:
        print("\n❌ Le groupe PRIVILEGE n'existe pas!")
        print("   Exécutez d'abord: python creer_utilisateur_privilege.py")
        sys.exit(1)
    
    # Tester la connexion
    connexion_ok = test_connexion_privilege()
    
    if connexion_ok:
        print(f"\n🎉 Test de connexion réussi!")
        print(f"   Vous pouvez maintenant vous connecter avec:")
        print(f"   - Nom d'utilisateur: privilege1")
        print(f"   - Mot de passe: test123")
        print(f"   - Groupe: PRIVILEGE")
    else:
        print(f"\n❌ Test de connexion échoué!")
        print(f"   Vérifiez la configuration de l'utilisateur")

if __name__ == '__main__':
    main()
