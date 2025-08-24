#!/usr/bin/env python
"""
Script de réparation automatique pour le groupe PRIVILEGE
Usage: python reparer_privilege_auto.py
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

def reparer_groupe_privilege():
    """Réparation automatique du groupe PRIVILEGE"""
    print("🔧 RÉPARATION AUTOMATIQUE DU GROUPE PRIVILEGE")
    print("=" * 60)
    
    try:
        # 1. Créer/réparer le groupe Django PRIVILEGE
        print("\n1️⃣ RÉPARATION DU GROUPE DJANGO PRIVILEGE")
        groupe_django, created = Group.objects.get_or_create(name='PRIVILEGE')
        if created:
            print("   ✅ Groupe Django PRIVILEGE créé")
        else:
            print("   ℹ️  Groupe Django PRIVILEGE existe déjà")
        
        # 2. Créer/réparer le groupe de travail PRIVILEGE
        print("\n2️⃣ RÉPARATION DU GROUPE DE TRAVAIL PRIVILEGE")
        groupe_travail, created = GroupeTravail.objects.get_or_create(
            nom='PRIVILEGE',
            defaults={
                'description': 'Groupe avec privilèges étendus pour la gestion complète du système',
                'permissions': {
                    'modules': [
                        'proprietes',
                        'contrats', 
                        'paiements',
                        'utilisateurs',
                        'notifications',
                        'core'
                    ],
                    'actions_speciales': [
                        'suppression_complete',
                        'gestion_profils',
                        'acces_toutes_donnees',
                        'modification_systeme'
                    ]
                },
                'actif': True
            }
        )
        
        if created:
            print("   ✅ Groupe de travail PRIVILEGE créé")
        else:
            print("   ℹ️  Groupe de travail PRIVILEGE existe déjà")
            # Mettre à jour les permissions si elles sont vides
            if not groupe_travail.permissions:
                groupe_travail.permissions = {
                    'modules': [
                        'proprietes',
                        'contrats', 
                        'paiements',
                        'utilisateurs',
                        'notifications',
                        'core'
                    ],
                    'actions_speciales': [
                        'suppression_complete',
                        'gestion_profils',
                        'acces_toutes_donnees',
                        'modification_systeme'
                    ]
                }
                groupe_travail.save()
                print("   ✅ Permissions mises à jour")
        
        # 3. Créer/réparer l'utilisateur privilege1
        print("\n3️⃣ RÉPARATION DE L'UTILISATEUR PRIVILEGE1")
        
        try:
            utilisateur = Utilisateur.objects.get(username='privilege1')
            print("   ℹ️  Utilisateur privilege1 existe déjà")
            
            # Mettre à jour les informations
            utilisateur.is_active = True
            utilisateur.is_staff = True
            utilisateur.groupe_travail = groupe_travail
            utilisateur.set_password('test123')
            utilisateur.save()
            print("   ✅ Utilisateur mis à jour")
            
        except Utilisateur.DoesNotExist:
            print("   Création de l'utilisateur privilege1...")
            utilisateur = Utilisateur.objects.create_user(
                username='privilege1',
                email='privilege1@gestionimmo.com',
                password='test123',
                first_name='Utilisateur',
                last_name='Privilege',
                is_staff=True,
                is_active=True,
                groupe_travail=groupe_travail,
                poste='Utilisateur Test',
                departement='Test',
                telephone='+33123456789',
                adresse='123 Rue de Test, 75001 Paris'
            )
            print("   ✅ Utilisateur privilege1 créé")
        
        # 4. Ajouter l'utilisateur au groupe Django
        print("\n4️⃣ AJOUT AU GROUPE DJANGO")
        if groupe_django not in utilisateur.groups.all():
            utilisateur.groups.add(groupe_django)
            print("   ✅ Utilisateur ajouté au groupe Django PRIVILEGE")
        else:
            print("   ℹ️  Utilisateur déjà dans le groupe Django PRIVILEGE")
        
        # 5. Test de connexion
        print("\n5️⃣ TEST DE CONNEXION")
        user_auth = authenticate(username='privilege1', password='test123')
        
        if user_auth:
            print("   ✅ Authentification réussie!")
            print("   ✅ Utilisateur peut se connecter!")
            
            # Vérifier les groupes
            groupes_django = user_auth.groups.all()
            print(f"   Groupes Django: {[g.name for g in groupes_django]}")
            
            if hasattr(user_auth, 'groupe_travail') and user_auth.groupe_travail:
                print(f"   Groupe de travail: {user_auth.groupe_travail.nom}")
                print(f"   Groupe actif: {user_auth.groupe_travail.actif}")
                
                modules = user_auth.groupe_travail.get_permissions_list()
                print(f"   Modules accessibles: {', '.join(modules)}")
            
            return True
            
        else:
            print("   ❌ Échec de l'authentification")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la réparation: {str(e)}")
        return False

def verifier_reparation():
    """Vérifie que la réparation a bien fonctionné"""
    print("\n🔍 VÉRIFICATION DE LA RÉPARATION")
    print("=" * 40)
    
    try:
        # Vérifier l'utilisateur
        utilisateur = Utilisateur.objects.get(username='privilege1')
        print(f"✅ Utilisateur: {utilisateur.username}")
        print(f"   - Actif: {utilisateur.is_active}")
        print(f"   - Staff: {utilisateur.is_staff}")
        print(f"   - Groupe travail: {utilisateur.groupe_travail.nom if utilisateur.groupe_travail else 'Aucun'}")
        
        # Vérifier le groupe de travail
        if utilisateur.groupe_travail:
            print(f"✅ Groupe de travail: {utilisateur.groupe_travail.nom}")
            print(f"   - Actif: {utilisateur.groupe_travail.actif}")
            print(f"   - Permissions: {utilisateur.groupe_travail.permissions}")
        
        # Vérifier les groupes Django
        groupes_django = utilisateur.groups.all()
        print(f"✅ Groupes Django: {[g.name for g in groupes_django]}")
        
        # Test d'authentification final
        user_auth = authenticate(username='privilege1', password='test123')
        if user_auth:
            print("✅ Authentification: SUCCÈS")
            return True
        else:
            print("❌ Authentification: ÉCHEC")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🚀 RÉPARATION AUTOMATIQUE DU GROUPE PRIVILEGE")
    print("=" * 60)
    
    try:
        # Réparer le système
        reparation_ok = reparer_groupe_privilege()
        
        if reparation_ok:
            # Vérifier la réparation
            verification_ok = verifier_reparation()
            
            if verification_ok:
                print(f"\n🎉 RÉPARATION RÉUSSIE!")
                print(f"   Vous pouvez maintenant vous connecter avec:")
                print(f"   - Nom d'utilisateur: privilege1")
                print(f"   - Mot de passe: test123")
                print(f"   - Groupe: PRIVILEGE")
                
                print(f"\n📋 RÉSUMÉ DES CORRECTIONS:")
                print(f"   ✅ Groupe Django PRIVILEGE créé/réparé")
                print(f"   ✅ Groupe de travail PRIVILEGE créé/réparé")
                print(f"   ✅ Utilisateur privilege1 créé/réparé")
                print(f"   ✅ Permissions configurées")
                print(f"   ✅ Authentification testée")
                
            else:
                print(f"\n⚠️  RÉPARATION PARTIELLE")
                print(f"   Vérifiez les erreurs ci-dessus")
                
        else:
            print(f"\n❌ RÉPARATION ÉCHOUÉE")
            print(f"   Vérifiez les erreurs ci-dessus")
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {str(e)}")
        print(f"   Vérifiez la configuration Django")

if __name__ == '__main__':
    main()
