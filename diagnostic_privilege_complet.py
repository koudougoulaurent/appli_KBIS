#!/usr/bin/env python
"""
Script de diagnostic complet pour le groupe PRIVILEGE
Usage: python diagnostic_privilege_complet.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from utilisateurs.models import GroupeTravail, Utilisateur

def diagnostic_complet():
    """Diagnostic complet du système d'authentification"""
    print("🔍 DIAGNOSTIC COMPLET DU GROUPE PRIVILEGE")
    print("=" * 60)
    
    # 1. Vérifier les modèles Django natifs
    print("\n1️⃣ VÉRIFICATION DES GROUPES DJANGO NATIFS")
    print("-" * 40)
    
    try:
        groupes_django = Group.objects.all()
        print(f"   Groupes Django trouvés: {groupes_django.count()}")
        for groupe in groupes_django:
            print(f"   - {groupe.name} (ID: {groupe.id})")
            
        # Créer le groupe Django PRIVILEGE s'il n'existe pas
        groupe_django, created = Group.objects.get_or_create(name='PRIVILEGE')
        if created:
            print(f"   ✅ Groupe Django PRIVILEGE créé")
        else:
            print(f"   ℹ️  Groupe Django PRIVILEGE existe déjà")
            
    except Exception as e:
        print(f"   ❌ Erreur avec les groupes Django: {str(e)}")
    
    # 2. Vérifier le modèle GroupeTravail personnalisé
    print("\n2️⃣ VÉRIFICATION DU MODÈLE GROUPE_TRAVAIL")
    print("-" * 40)
    
    try:
        groupes_travail = GroupeTravail.objects.all()
        print(f"   Groupes de travail trouvés: {groupes_travail.count()}")
        for groupe in groupes_travail:
            print(f"   - {groupe.nom} (ID: {groupe.id}, Actif: {groupe.actif})")
            if groupe.permissions:
                print(f"     Permissions: {groupe.permissions}")
        
        # Créer le groupe PRIVILEGE s'il n'existe pas
        groupe_travail, created = GroupeTravail.objects.get_or_create(
            nom='PRIVILEGE',
            defaults={
                'description': 'Groupe avec privilèges étendus',
                'permissions': {
                    'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs', 'core'],
                    'actions_speciales': ['suppression_complete', 'gestion_profils']
                },
                'actif': True
            }
        )
        
        if created:
            print(f"   ✅ Groupe de travail PRIVILEGE créé")
        else:
            print(f"   ℹ️  Groupe de travail PRIVILEGE existe déjà")
            # Mettre à jour les permissions si nécessaire
            if not groupe_travail.permissions:
                groupe_travail.permissions = {
                    'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs', 'core'],
                    'actions_speciales': ['suppression_complete', 'gestion_profils']
                }
                groupe_travail.save()
                print(f"   ✅ Permissions mises à jour")
                
    except Exception as e:
        print(f"   ❌ Erreur avec les groupes de travail: {str(e)}")
    
    # 3. Vérifier l'utilisateur privilege1
    print("\n3️⃣ VÉRIFICATION DE L'UTILISATEUR PRIVILEGE1")
    print("-" * 40)
    
    try:
        utilisateur = Utilisateur.objects.get(username='privilege1')
        print(f"   ✅ Utilisateur trouvé: {utilisateur.username}")
        print(f"   - Nom complet: {utilisateur.get_nom_complet()}")
        print(f"   - Email: {utilisateur.email}")
        print(f"   - Est actif: {utilisateur.is_active}")
        print(f"   - Est staff: {utilisateur.is_staff}")
        print(f"   - Est superuser: {utilisateur.is_superuser}")
        
        if utilisateur.groupe_travail:
            print(f"   - Groupe de travail: {utilisateur.groupe_travail.nom}")
            print(f"   - Groupe actif: {utilisateur.groupe_travail.actif}")
        else:
            print(f"   ❌ Aucun groupe de travail assigné!")
            
    except Utilisateur.DoesNotExist:
        print(f"   ❌ Utilisateur privilege1 non trouvé!")
        print(f"   Création de l'utilisateur...")
        
        try:
            # Récupérer le groupe PRIVILEGE
            groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
            
            # Créer l'utilisateur
            utilisateur = Utilisateur.objects.create_user(
                username='privilege1',
                email='privilege1@gestionimmo.com',
                password='test123',
                first_name='Utilisateur',
                last_name='Privilege',
                is_staff=True,
                is_active=True,
                groupe_travail=groupe_privilege
            )
            
            # Ajouter l'utilisateur au groupe Django PRIVILEGE
            groupe_django = Group.objects.get(name='PRIVILEGE')
            utilisateur.groups.add(groupe_django)
            
            print(f"   ✅ Utilisateur privilege1 créé avec succès")
            
        except Exception as e:
            print(f"   ❌ Erreur lors de la création: {str(e)}")
            return False
    
    # 4. Test d'authentification
    print("\n4️⃣ TEST D'AUTHENTIFICATION")
    print("-" * 40)
    
    try:
        user_auth = authenticate(username='privilege1', password='test123')
        
        if user_auth:
            print(f"   ✅ Authentification réussie!")
            print(f"   - Utilisateur: {user_auth.username}")
            print(f"   - Est actif: {user_auth.is_active}")
            print(f"   - Est authentifié: {user_auth.is_authenticated}")
            
            # Vérifier les groupes Django
            groupes_django = user_auth.groups.all()
            print(f"   - Groupes Django: {[g.name for g in groupes_django]}")
            
            # Vérifier le groupe de travail
            if hasattr(user_auth, 'groupe_travail') and user_auth.groupe_travail:
                print(f"   - Groupe de travail: {user_auth.groupe_travail.nom}")
            else:
                print(f"   ⚠️  Aucun groupe de travail")
                
        else:
            print(f"   ❌ Échec de l'authentification!")
            print(f"   Vérification du mot de passe...")
            
            # Vérifier le mot de passe
            if utilisateur.check_password('test123'):
                print(f"   ✅ Mot de passe correct")
                print(f"   Problème possible: utilisateur non actif ou autre")
            else:
                print(f"   ❌ Mot de passe incorrect")
                # Remettre le bon mot de passe
                utilisateur.set_password('test123')
                utilisateur.save()
                print(f"   ✅ Mot de passe remis à jour")
                
    except Exception as e:
        print(f"   ❌ Erreur lors de l'authentification: {str(e)}")
    
    # 5. Vérifier les permissions
    print("\n5️⃣ VÉRIFICATION DES PERMISSIONS")
    print("-" * 40)
    
    try:
        if 'user_auth' in locals() and user_auth:
            # Permissions Django natives
            permissions = user_auth.user_permissions.all()
            print(f"   Permissions utilisateur directes: {permissions.count()}")
            
            # Permissions des groupes Django
            permissions_groupes = Permission.objects.filter(group__user=user_auth)
            print(f"   Permissions des groupes Django: {permissions_groupes.count()}")
            
            # Permissions du groupe de travail
            if hasattr(user_auth, 'groupe_travail') and user_auth.groupe_travail:
                modules = user_auth.groupe_travail.get_permissions_list()
                print(f"   Modules accessibles: {', '.join(modules)}")
            else:
                print(f"   ⚠️  Impossible de récupérer les modules accessibles")
                
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des permissions: {str(e)}")
    
    # 6. Test de connexion finale
    print("\n6️⃣ TEST DE CONNEXION FINAL")
    print("-" * 40)
    
    try:
        # Forcer la mise à jour de l'utilisateur
        utilisateur.refresh_from_db()
        
        # Vérifier que tout est en ordre
        if (utilisateur.is_active and 
            utilisateur.groupe_travail and 
            utilisateur.groupe_travail.nom == 'PRIVILEGE' and
            utilisateur.groupe_travail.actif):
            
            print(f"   ✅ Configuration utilisateur correcte")
            print(f"   ✅ Groupe PRIVILEGE actif et assigné")
            
            # Test d'authentification final
            user_final = authenticate(username='privilege1', password='test123')
            if user_final:
                print(f"   ✅ Authentification finale réussie!")
                print(f"   🎉 L'utilisateur peut maintenant se connecter!")
                return True
            else:
                print(f"   ❌ Authentification finale échouée")
                return False
        else:
            print(f"   ❌ Configuration utilisateur incorrecte")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test final: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🚀 DIAGNOSTIC COMPLET DU GROUPE PRIVILEGE")
    print("=" * 60)
    
    try:
        succes = diagnostic_complet()
        
        if succes:
            print(f"\n🎉 DIAGNOSTIC TERMINÉ AVEC SUCCÈS!")
            print(f"   Vous pouvez maintenant vous connecter avec:")
            print(f"   - Nom d'utilisateur: privilege1")
            print(f"   - Mot de passe: test123")
            print(f"   - Groupe: PRIVILEGE")
        else:
            print(f"\n❌ DIAGNOSTIC TERMINÉ AVEC DES PROBLÈMES")
            print(f"   Vérifiez les erreurs ci-dessus")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {str(e)}")
        print(f"   Vérifiez la configuration Django")

if __name__ == '__main__':
    main()
