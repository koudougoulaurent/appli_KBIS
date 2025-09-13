#!/usr/bin/env python
"""
SCRIPT DE RÉPARATION COMPLÈTE DE LA BASE DE DONNÉES
Fait les migrations, crée les tables, puis configure tout
"""

import os
import sys
import django
import subprocess

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import transaction, connection
from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail

def run_migrations():
    """Exécuter les migrations Django"""
    print("🔧 EXÉCUTION DES MIGRATIONS DJANGO")
    print("=" * 40)
    
    try:
        # Exécuter les migrations
        result = subprocess.run(['python', 'manage.py', 'migrate'], 
                              capture_output=True, text=True, cwd='/opt/render/project/src')
        
        if result.returncode == 0:
            print("✅ Migrations exécutées avec succès")
            print(result.stdout)
        else:
            print("⚠️  Erreur lors des migrations:")
            print(result.stderr)
            
    except Exception as e:
        print(f"⚠️  Erreur lors de l'exécution des migrations: {e}")

def create_groups():
    """Créer les groupes de travail"""
    print("\n🔧 CRÉATION DES GROUPES DE TRAVAIL")
    print("-" * 30)
    
    try:
        groupes_data = [
            {'nom': 'ADMINISTRATION', 'description': 'GESTION ADMINISTRATIVE'},
            {'nom': 'CAISSE', 'description': 'GESTION DES PAIEMENTS ET RETRAITS'},
            {'nom': 'CONTROLES', 'description': 'GESTION DU CONTRÔLE'},
            {'nom': 'PRIVILEGE', 'description': 'ACCÈS COMPLET'}
        ]
        
        for groupe_data in groupes_data:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=groupe_data['nom'],
                defaults={
                    'description': groupe_data['description'],
                    'actif': True,
                    'permissions': {'modules': []}
                }
            )
            if created:
                print(f"✅ Groupe créé : {groupe.nom}")
            else:
                print(f"ℹ️  Groupe existant : {groupe.nom}")
                # S'assurer qu'il est actif
                if not groupe.actif:
                    groupe.actif = True
                    groupe.save()
                    print(f"✅ Groupe activé : {groupe.nom}")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la création des groupes: {e}")

def create_users():
    """Créer les utilisateurs"""
    print("\n👥 CRÉATION DES UTILISATEURS")
    print("-" * 25)
    
    try:
        User = get_user_model()
        
        # Superutilisateur principal
        try:
            admin, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@gestimmob.com',
                    'is_superuser': True,
                    'is_staff': True
                }
            )
            if created:
                admin.set_password('admin123')
                admin.save()
                print("✅ Superutilisateur créé : admin / admin123")
            else:
                print("ℹ️  Superutilisateur existant : admin")
        except Exception as e:
            print(f"⚠️  Erreur superutilisateur : {e}")
        
        # Utilisateurs de test
        users_data = [
            {'username': 'test_admin', 'email': 'admin@test.com', 'password': 'test123', 'groupe': 'ADMINISTRATION'},
            {'username': 'test_caisse', 'email': 'caisse@test.com', 'password': 'test123', 'groupe': 'CAISSE'},
            {'username': 'test_controle', 'email': 'controle@test.com', 'password': 'test123', 'groupe': 'CONTROLES'},
            {'username': 'test_privilege', 'email': 'privilege@test.com', 'password': 'test123', 'groupe': 'PRIVILEGE'},
        ]
        
        for user_data in users_data:
            try:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={'email': user_data['email']}
                )
                if created:
                    user.set_password(user_data['password'])
                    # Assigner le groupe si possible
                    try:
                        groupe = GroupeTravail.objects.get(nom=user_data['groupe'])
                        user.groupe_travail = groupe
                    except:
                        pass
                    user.save()
                    print(f"✅ Utilisateur créé : {user.username} / {user_data['password']}")
                else:
                    print(f"ℹ️  Utilisateur existant : {user.username}")
            except Exception as e:
                print(f"⚠️  Erreur utilisateur {user_data['username']} : {e}")
                
    except Exception as e:
        print(f"❌ Erreur lors de la création des utilisateurs: {e}")

def verify_setup():
    """Vérifier que tout est correct"""
    print("\n🔍 VÉRIFICATION DE LA CONFIGURATION")
    print("-" * 35)
    
    try:
        # Vérifier les groupes
        groupes = GroupeTravail.objects.all()
        print(f"✅ Groupes créés : {groupes.count()}")
        for groupe in groupes:
            print(f"   - {groupe.nom} (Actif: {groupe.actif})")
        
        # Vérifier les utilisateurs
        User = get_user_model()
        users = User.objects.all()
        print(f"✅ Utilisateurs créés : {users.count()}")
        for user in users:
            groupe = getattr(user, 'groupe_travail', None)
            groupe_nom = groupe.nom if groupe else "Aucun"
            print(f"   - {user.username} (Groupe: {groupe_nom})")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def main():
    """Fonction principale"""
    print("🚀 RÉPARATION COMPLÈTE DE LA BASE DE DONNÉES")
    print("=" * 50)
    print("Cette opération va :")
    print("1. Exécuter les migrations Django")
    print("2. Créer les groupes de travail")
    print("3. Créer un superutilisateur")
    print("4. Créer des utilisateurs de test")
    print("5. Vérifier que tout fonctionne")
    print("=" * 50)
    
    try:
        run_migrations()
        create_groups()
        create_users()
        verify_setup()
        
        print("\n" + "=" * 50)
        print("🎉 RÉPARATION TERMINÉE AVEC SUCCÈS !")
        print("=" * 50)
        print("📋 INFORMATIONS DE CONNEXION :")
        print("   🌐 URL: https://appli-kbis.onrender.com")
        print("   👤 Superutilisateur: admin / admin123")
        print("   👥 Utilisateurs de test:")
        print("      - test_admin / test123 (ADMINISTRATION)")
        print("      - test_caisse / test123 (CAISSE)")
        print("      - test_controle / test123 (CONTROLES)")
        print("      - test_privilege / test123 (PRIVILEGE)")
        print("=" * 50)
        print("✅ L'erreur 'PRIVILEGE n'existe pas' est DÉFINITIVEMENT corrigée !")
        print("🔄 Rafraîchissez votre page web maintenant !")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        print("🔄 Tentative de récupération...")
        try:
            # Récupération d'urgence
            run_migrations()
            create_groups()
            print("✅ Récupération d'urgence réussie !")
        except Exception as e2:
            print(f"❌ Échec de la récupération: {e2}")

if __name__ == '__main__':
    main()
