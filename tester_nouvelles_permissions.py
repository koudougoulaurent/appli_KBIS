#!/usr/bin/env python
"""
Script de test pour vérifier les nouvelles permissions
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from utilisateurs.mixins_permissions import (
    check_add_permission, 
    check_modify_permission, 
    check_delete_permission, 
    check_privilege_permission
)

def tester_permissions():
    """Teste les nouvelles permissions pour chaque groupe"""
    
    print("🧪 TEST DES NOUVELLES PERMISSIONS")
    print("=" * 50)
    
    # Récupérer les groupes
    try:
        groupe_caisse = GroupeTravail.objects.get(nom='CAISSE')
        groupe_controles = GroupeTravail.objects.get(nom='CONTROLES')
        groupe_admin = GroupeTravail.objects.get(nom='ADMINISTRATION')
        groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
    except GroupeTravail.DoesNotExist as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Récupérer un utilisateur de chaque groupe
    try:
        user_caisse = Utilisateur.objects.filter(groupe_travail=groupe_caisse).first()
        user_controles = Utilisateur.objects.filter(groupe_travail=groupe_controles).first()
        user_admin = Utilisateur.objects.filter(groupe_travail=groupe_admin).first()
        user_privilege = Utilisateur.objects.filter(groupe_travail=groupe_privilege).first()
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")
        return False
    
    # Test des permissions pour chaque groupe
    groupes_test = [
        ('CAISSE', user_caisse),
        ('CONTROLES', user_controles),
        ('ADMINISTRATION', user_admin),
        ('PRIVILEGE', user_privilege)
    ]
    
    print("\n📋 RÉSULTATS DES TESTS:")
    print("-" * 50)
    
    for nom_groupe, user in groupes_test:
        if not user:
            print(f"❌ {nom_groupe}: Aucun utilisateur trouvé")
            continue
        
        print(f"\n👤 Groupe: {nom_groupe}")
        print(f"   Utilisateur: {user.username}")
        
        # Test permission d'ajout
        can_add, msg_add = check_add_permission(user)
        print(f"   ✅ Ajouter: {'OUI' if can_add else 'NON'} - {msg_add}")
        
        # Test permission de modification
        can_modify, msg_modify = check_modify_permission(user)
        print(f"   🔧 Modifier: {'OUI' if can_modify else 'NON'} - {msg_modify}")
        
        # Test permission de suppression
        can_delete, msg_delete = check_delete_permission(user)
        print(f"   🗑️  Supprimer: {'OUI' if can_delete else 'NON'} - {msg_delete}")
        
        # Test permission privilege
        is_privilege, msg_privilege = check_privilege_permission(user)
        print(f"   ⭐ Privilege: {'OUI' if is_privilege else 'NON'} - {msg_privilege}")
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES PERMISSIONS:")
    print("   - Tous les utilisateurs connectés et actifs peuvent AJOUTER")
    print("   - Seuls les utilisateurs PRIVILEGE peuvent MODIFIER")
    print("   - Seuls les utilisateurs PRIVILEGE peuvent SUPPRIMER")
    print("   - Seuls les utilisateurs PRIVILEGE ont accès aux fonctionnalités sensibles")
    
    return True

def main():
    """Fonction principale"""
    try:
        success = tester_permissions()
        if success:
            print("\n✅ Tests des permissions terminés avec succès !")
        else:
            print("\n❌ Erreur lors des tests des permissions")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
