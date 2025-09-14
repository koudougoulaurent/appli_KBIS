#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test permanents sur Render
Exécuter avec: python creer_utilisateurs_test.py
"""

import os
import django

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from django.contrib.auth.hashers import make_password

def creer_groupes():
    """Crée les groupes de travail s'ils n'existent pas"""
    print("🏢 Création des groupes de travail...")
    
    groupes_data = [
        {'nom': 'CAISSE', 'description': 'Gestion des paiements et retraits'},
        {'nom': 'CONTROLES', 'description': 'Contrôle et audit'},
        {'nom': 'ADMINISTRATION', 'description': 'Gestion administrative'},
        {'nom': 'PRIVILEGE', 'description': 'Accès complet'},
    ]
    
    groupes_crees = []
    for groupe_data in groupes_data:
        groupe, created = GroupeTravail.objects.update_or_create(
            nom=groupe_data['nom'],
            defaults={
                'description': groupe_data['description'],
                'actif': True,
                'permissions': {}
            }
        )
        groupes_crees.append(groupe)
        print(f"✅ Groupe: {groupe.nom}")
    
    return groupes_crees

def creer_utilisateurs_test(groupes):
    """Crée les utilisateurs de test"""
    print("\n👥 Création des utilisateurs de test...")
    
    # Récupérer les groupes
    groupe_caisse = next((g for g in groupes if g.nom == 'CAISSE'), None)
    groupe_controles = next((g for g in groupes if g.nom == 'CONTROLES'), None)
    groupe_admin = next((g for g in groupes if g.nom == 'ADMINISTRATION'), None)
    groupe_privilege = next((g for g in groupes if g.nom == 'PRIVILEGE'), None)
    
    utilisateurs_data = [
        # Super administrateur
        {
            'username': 'admin',
            'email': 'admin@gestimmob.com',
            'first_name': 'Super',
            'last_name': 'Administrateur',
            'groupe_travail': groupe_privilege,
            'is_staff': True,
            'is_superuser': True,
            'actif': True,
            'poste': 'Super Administrateur',
            'departement': 'Direction'
        },
        # Groupe CAISSE
        {
            'username': 'caisse1',
            'email': 'caisse1@gestimmob.com',
            'first_name': 'Marie',
            'last_name': 'Caissière',
            'groupe_travail': groupe_caisse,
            'is_staff': False,
            'is_superuser': False,
            'actif': True,
            'poste': 'Caissière',
            'departement': 'Finances'
        },
        {
            'username': 'caisse2',
            'email': 'caisse2@gestimmob.com',
            'first_name': 'Pierre',
            'last_name': 'Comptable',
            'groupe_travail': groupe_caisse,
            'is_staff': False,
            'is_superuser': False,
            'actif': True,
            'poste': 'Comptable',
            'departement': 'Finances'
        },
        # Groupe CONTROLES
        {
            'username': 'controle1',
            'email': 'controle1@gestimmob.com',
            'first_name': 'Sophie',
            'last_name': 'Contrôleuse',
            'groupe_travail': groupe_controles,
            'is_staff': False,
            'is_superuser': False,
            'actif': True,
            'poste': 'Contrôleuse',
            'departement': 'Audit'
        },
        {
            'username': 'controle2',
            'email': 'controle2@gestimmob.com',
            'first_name': 'Jean',
            'last_name': 'Auditeur',
            'groupe_travail': groupe_controles,
            'is_staff': False,
            'is_superuser': False,
            'actif': True,
            'poste': 'Auditeur',
            'departement': 'Audit'
        },
        # Groupe ADMINISTRATION
        {
            'username': 'admin1',
            'email': 'admin1@gestimmob.com',
            'first_name': 'Claire',
            'last_name': 'Administratrice',
            'groupe_travail': groupe_admin,
            'is_staff': True,
            'is_superuser': False,
            'actif': True,
            'poste': 'Administratrice',
            'departement': 'Administration'
        },
        {
            'username': 'admin2',
            'email': 'admin2@gestimmob.com',
            'first_name': 'Marc',
            'last_name': 'Gestionnaire',
            'groupe_travail': groupe_admin,
            'is_staff': True,
            'is_superuser': False,
            'actif': True,
            'poste': 'Gestionnaire',
            'departement': 'Administration'
        },
        # Groupe PRIVILEGE
        {
            'username': 'privilege1',
            'email': 'privilege1@gestimmob.com',
            'first_name': 'Alice',
            'last_name': 'Manager',
            'groupe_travail': groupe_privilege,
            'is_staff': True,
            'is_superuser': False,
            'actif': True,
            'poste': 'Manager',
            'departement': 'Direction'
        },
        {
            'username': 'privilege2',
            'email': 'privilege2@gestimmob.com',
            'first_name': 'David',
            'last_name': 'Directeur',
            'groupe_travail': groupe_privilege,
            'is_staff': True,
            'is_superuser': False,
            'actif': True,
            'poste': 'Directeur',
            'departement': 'Direction'
        }
    ]
    
    utilisateurs_crees = []
    mot_de_passe = 'password123'  # Mot de passe par défaut pour tous
    
    for user_data in utilisateurs_data:
        # Supprimer l'utilisateur s'il existe déjà
        Utilisateur.objects.filter(username=user_data['username']).delete()
        
        # Créer le nouvel utilisateur
        user = Utilisateur.objects.create(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            groupe_travail=user_data['groupe_travail'],
            is_staff=user_data['is_staff'],
            is_superuser=user_data['is_superuser'],
            actif=user_data['actif'],
            poste=user_data['poste'],
            departement=user_data['departement'],
            password=make_password(mot_de_passe)
        )
        
        utilisateurs_crees.append(user)
        print(f"✅ Utilisateur: {user.username} ({user.groupe_travail.nom})")
    
    return utilisateurs_crees, mot_de_passe

def main():
    """Fonction principale"""
    print("🚀 CRÉATION DES UTILISATEURS DE TEST PERMANENTS")
    print("=" * 60)
    
    try:
        # 1. Créer les groupes
        groupes = creer_groupes()
        
        # 2. Créer les utilisateurs
        utilisateurs, mot_de_passe = creer_utilisateurs_test(groupes)
        
        print("\n" + "=" * 60)
        print("🎉 UTILISATEURS DE TEST CRÉÉS AVEC SUCCÈS !")
        print("=" * 60)
        
        print(f"\n📊 Statistiques:")
        print(f"   - Groupes créés: {len(groupes)}")
        print(f"   - Utilisateurs créés: {len(utilisateurs)}")
        
        print(f"\n🔑 IDENTIFIANTS DE CONNEXION:")
        print(f"   Mot de passe pour tous: {mot_de_passe}")
        print(f"\n   👑 SUPER ADMINISTRATEUR:")
        print(f"      - admin / {mot_de_passe}")
        
        print(f"\n   💰 GROUPE CAISSE:")
        print(f"      - caisse1 / {mot_de_passe}")
        print(f"      - caisse2 / {mot_de_passe}")
        
        print(f"\n   🔍 GROUPE CONTROLES:")
        print(f"      - controle1 / {mot_de_passe}")
        print(f"      - controle2 / {mot_de_passe}")
        
        print(f"\n   📋 GROUPE ADMINISTRATION:")
        print(f"      - admin1 / {mot_de_passe}")
        print(f"      - admin2 / {mot_de_passe}")
        
        print(f"\n   ⭐ GROUPE PRIVILEGE:")
        print(f"      - privilege1 / {mot_de_passe}")
        print(f"      - privilege2 / {mot_de_passe}")
        
        print(f"\n🌐 INSTRUCTIONS:")
        print(f"   1. Allez sur votre site Render")
        print(f"   2. Sélectionnez un groupe de travail")
        print(f"   3. Connectez-vous avec un des identifiants ci-dessus")
        print(f"   4. Testez toutes les fonctionnalités !")
        
        print(f"\n✅ Ces utilisateurs sont permanents jusqu'au déploiement final !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
