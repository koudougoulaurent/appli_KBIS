#!/usr/bin/env python
"""
Script pour attribuer les permissions nécessaires à l'utilisateur admin
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from paiements.models import Paiement

def attribuer_permissions_admin():
    """Attribuer les permissions nécessaires à l'utilisateur admin"""
    
    print("🔐 ATTRIBUTION DES PERMISSIONS À L'UTILISATEUR ADMIN")
    print("=" * 60)
    
    User = get_user_model()
    
    # Récupérer l'utilisateur admin
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✅ Utilisateur admin trouvé: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur admin non trouvé")
        return False
    
    # Vérifier les groupes existants
    print("\n📋 GROUPES EXISTANTS:")
    print("-" * 30)
    groupes = Group.objects.all()
    for groupe in groupes:
        print(f"   • {groupe.name}")
    
    # Créer ou récupérer le groupe PRIVILEGE
    try:
        groupe_privilege = Group.objects.get(name='PRIVILEGE')
        print(f"\n✅ Groupe PRIVILEGE trouvé: {groupe_privilege.name}")
    except Group.DoesNotExist:
        groupe_privilege = Group.objects.create(name='PRIVILEGE')
        print(f"\n✅ Groupe PRIVILEGE créé: {groupe_privilege.name}")
    
    # Créer ou récupérer le groupe ADMINISTRATION
    try:
        groupe_admin = Group.objects.create(name='ADMINISTRATION')
        print(f"✅ Groupe ADMINISTRATION créé: {groupe_admin.name}")
    except:
        groupe_admin = Group.objects.get(name='ADMINISTRATION')
        print(f"✅ Groupe ADMINISTRATION trouvé: {groupe_admin.name}")
    
    # Créer ou récupérer le groupe COMPTABILITE
    try:
        groupe_compta = Group.objects.create(name='COMPTABILITE')
        print(f"✅ Groupe COMPTABILITE créé: {groupe_compta.name}")
    except:
        groupe_compta = Group.objects.get(name='COMPTABILITE')
        print(f"✅ Groupe COMPTABILITE trouvé: {groupe_compta.name}")
    
    # Attribuer l'utilisateur admin à tous les groupes
    admin_user.groups.add(groupe_privilege)
    admin_user.groups.add(groupe_admin)
    admin_user.groups.add(groupe_compta)
    
    print(f"\n✅ Utilisateur admin ajouté aux groupes:")
    for groupe in admin_user.groups.all():
        print(f"   • {groupe.name}")
    
    # Vérifier les permissions sur les paiements
    print(f"\n🔍 PERMISSIONS SUR LES PAIEMENTS:")
    print("-" * 30)
    
    content_type = ContentType.objects.get_for_model(Paiement)
    permissions_paiement = Permission.objects.filter(content_type=content_type)
    
    for perm in permissions_paiement:
        print(f"   • {perm.codename} - {perm.name}")
    
    # Attribuer toutes les permissions de paiement au groupe PRIVILEGE
    for perm in permissions_paiement:
        groupe_privilege.permissions.add(perm)
    
    print(f"\n✅ Toutes les permissions de paiement attribuées au groupe PRIVILEGE")
    
    # Vérifier que l'utilisateur admin a bien les permissions
    print(f"\n🔐 VÉRIFICATION DES PERMISSIONS:")
    print("-" * 30)
    
    user_permissions = admin_user.get_all_permissions()
    paiement_permissions = [perm for perm in user_permissions if 'paiement' in perm]
    
    for perm in paiement_permissions:
        print(f"   ✅ {perm}")
    
    print(f"\n" + "=" * 60)
    print("🎯 PERMISSIONS ATTRIBUÉES AVEC SUCCÈS !")
    print("\n💡 Maintenant vous devriez voir les boutons de validation !")
    
    return True

if __name__ == '__main__':
    attribuer_permissions_admin()
