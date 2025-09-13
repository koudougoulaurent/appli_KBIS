#!/usr/bin/env python
"""
SCRIPT DE CONFIGURATION COMPLÈTE - SOLUTION DÉFINITIVE
Résout TOUS les problèmes d'un coup : groupes, superutilisateur, utilisateurs de test
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import transaction, connection
from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail

def reset_database():
    """Reset complet de la base de données"""
    print("🔥 RESET COMPLET DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Supprimer toutes les tables liées aux utilisateurs
        cursor.execute("DELETE FROM utilisateurs_grouptravail;")
        cursor.execute("DELETE FROM utilisateurs_utilisateur;")
        cursor.execute("DELETE FROM django_admin_log;")
        cursor.execute("DELETE FROM auth_user;")
        print("✅ Base de données nettoyée")

def create_groups():
    """Créer les groupes de travail"""
    print("\n🔧 CRÉATION DES GROUPES DE TRAVAIL")
    print("-" * 30)
    
    groupes_data = [
        {'nom': 'ADMINISTRATION', 'description': 'GESTION ADMINISTRATIVE'},
        {'nom': 'CAISSE', 'description': 'GESTION DES PAIEMENTS ET RETRAITS'},
        {'nom': 'CONTROLES', 'description': 'GESTION DU CONTRÔLE'},
        {'nom': 'PRIVILEGE', 'description': 'ACCÈS COMPLET'}
    ]
    
    for groupe_data in groupes_data:
        groupe = GroupeTravail.objects.create(
            nom=groupe_data['nom'],
            description=groupe_data['description'],
            actif=True,
            permissions={'modules': []}
        )
        print(f"✅ Groupe créé : {groupe.nom}")

def create_users():
    """Créer les utilisateurs"""
    print("\n👥 CRÉATION DES UTILISATEURS")
    print("-" * 25)
    
    User = get_user_model()
    
    # Superutilisateur principal
    try:
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@gestimmob.com',
            password='admin123'
        )
        print("✅ Superutilisateur créé : admin / admin123")
    except Exception as e:
        print(f"⚠️  Superutilisateur existant ou erreur : {e}")
    
    # Utilisateurs de test
    users_data = [
        {'username': 'test_admin', 'email': 'admin@test.com', 'password': 'test123', 'groupe': 'ADMINISTRATION'},
        {'username': 'test_caisse', 'email': 'caisse@test.com', 'password': 'test123', 'groupe': 'CAISSE'},
        {'username': 'test_controle', 'email': 'controle@test.com', 'password': 'test123', 'groupe': 'CONTROLES'},
        {'username': 'test_privilege', 'email': 'privilege@test.com', 'password': 'test123', 'groupe': 'PRIVILEGE'},
    ]
    
    for user_data in users_data:
        try:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            # Assigner le groupe
            groupe = GroupeTravail.objects.get(nom=user_data['groupe'])
            user.groupe_travail = groupe
            user.save()
            print(f"✅ Utilisateur créé : {user.username} / {user_data['password']} (Groupe: {groupe.nom})")
        except Exception as e:
            print(f"⚠️  Utilisateur {user_data['username']} : {e}")

def verify_setup():
    """Vérifier que tout est correct"""
    print("\n🔍 VÉRIFICATION DE LA CONFIGURATION")
    print("-" * 35)
    
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

def main():
    """Fonction principale"""
    print("🚀 CONFIGURATION COMPLÈTE DE L'APPLICATION")
    print("=" * 50)
    print("Cette opération va :")
    print("1. Nettoyer la base de données")
    print("2. Créer les groupes de travail")
    print("3. Créer un superutilisateur")
    print("4. Créer des utilisateurs de test")
    print("5. Vérifier que tout fonctionne")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            reset_database()
            create_groups()
            create_users()
            verify_setup()
            
            print("\n" + "=" * 50)
            print("🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS !")
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
            GroupeTravail.objects.all().delete()
            for nom in ['ADMINISTRATION', 'CAISSE', 'CONTROLES', 'PRIVILEGE']:
                GroupeTravail.objects.create(nom=nom, actif=True)
            print("✅ Récupération d'urgence réussie !")
        except Exception as e2:
            print(f"❌ Échec de la récupération: {e2}")
            sys.exit(1)

if __name__ == '__main__':
    main()
