#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'initialisation des groupes de travail et comptes de test
pour l'application GESTIMMOB
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail, Utilisateur
from django.db import transaction

User = get_user_model()

def init_groupes_travail():
    """Initialise les groupes de travail avec leurs permissions"""
    
    groupes_config = {
        'CAISSE': {
            'description': 'Gestion des paiements et retraits',
            'permissions': {
                'modules': ['paiements', 'retraits'],
                'actions': ['read', 'write', 'validate'],
                'restrictions': ['no_delete']
            }
        },
        'CONTROLES': {
            'description': 'Contrôle et audit des opérations',
            'permissions': {
                'modules': ['paiements', 'contrats', 'proprietes', 'utilisateurs'],
                'actions': ['read', 'validate'],
                'restrictions': ['no_write', 'no_delete']
            }
        },
        'ADMINISTRATION': {
            'description': 'Gestion administrative complète',
            'permissions': {
                'modules': ['proprietes', 'contrats', 'bailleurs', 'locataires'],
                'actions': ['read', 'write', 'create'],
                'restrictions': ['no_delete']
            }
        },
        'PRIVILEGE': {
            'description': 'Accès complet au système',
            'permissions': {
                'modules': ['paiements', 'retraits', 'proprietes', 'contrats', 'bailleurs', 'locataires', 'utilisateurs', 'groupes'],
                'actions': ['read', 'write', 'create', 'delete', 'admin'],
                'restrictions': []
            }
        }
    }
    
    groupes_crees = []
    
    for nom_groupe, config in groupes_config.items():
        groupe, created = GroupeTravail.objects.get_or_create(
            nom=nom_groupe,
            defaults={
                'description': config['description'],
                'permissions': config['permissions'],
                'actif': True
            }
        )
        
        if created:
            print(f"✅ Groupe créé : {nom_groupe}")
        else:
            # Mettre à jour les permissions si le groupe existe déjà
            groupe.permissions = config['permissions']
            groupe.description = config['description']
            groupe.save()
            print(f"🔄 Groupe mis à jour : {nom_groupe}")
        
        groupes_crees.append(groupe)
    
    return groupes_crees

def creer_comptes_test():
    """Crée des comptes de test pour chaque groupe"""
    
    comptes_test = {
        'CAISSE': [
            {
                'username': 'caisse1',
                'first_name': 'Marie',
                'last_name': 'Dubois',
                'email': 'caisse1@gestimmob.com',
                'password': 'caisse123',
                'poste': 'Caissier',
                'departement': 'Finances',
                'date_embauche': date(2023, 1, 15)
            },
            {
                'username': 'caisse2',
                'first_name': 'Pierre',
                'last_name': 'Martin',
                'email': 'caisse2@gestimmob.com',
                'password': 'caisse123',
                'poste': 'Assistant Caissier',
                'departement': 'Finances',
                'date_embauche': date(2023, 3, 20)
            }
        ],
        'CONTROLES': [
            {
                'username': 'controle1',
                'first_name': 'Sophie',
                'last_name': 'Bernard',
                'email': 'controle1@gestimmob.com',
                'password': 'controle123',
                'poste': 'Contrôleur',
                'departement': 'Audit',
                'date_embauche': date(2022, 6, 10)
            },
            {
                'username': 'controle2',
                'first_name': 'Jean',
                'last_name': 'Petit',
                'email': 'controle2@gestimmob.com',
                'password': 'controle123',
                'poste': 'Auditeur',
                'departement': 'Audit',
                'date_embauche': date(2022, 9, 5)
            }
        ],
        'ADMINISTRATION': [
            {
                'username': 'admin1',
                'first_name': 'Claire',
                'last_name': 'Moreau',
                'email': 'admin1@gestimmob.com',
                'password': 'admin123',
                'poste': 'Administrateur',
                'departement': 'Administration',
                'date_embauche': date(2021, 12, 1)
            },
            {
                'username': 'admin2',
                'first_name': 'Thomas',
                'last_name': 'Leroy',
                'email': 'admin2@gestimmob.com',
                'password': 'admin123',
                'poste': 'Assistant Administratif',
                'departement': 'Administration',
                'date_embauche': date(2022, 2, 15)
            }
        ],
        'PRIVILEGE': [
            {
                'username': 'privilege1',
                'first_name': 'Marc',
                'last_name': 'Durand',
                'email': 'privilege1@gestimmob.com',
                'password': 'privilege123',
                'poste': 'Directeur',
                'departement': 'Direction',
                'date_embauche': date(2020, 1, 1),
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'privilege2',
                'first_name': 'Isabelle',
                'last_name': 'Roux',
                'email': 'privilege2@gestimmob.com',
                'password': 'privilege123',
                'poste': 'Directeur Adjoint',
                'departement': 'Direction',
                'date_embauche': date(2021, 3, 1),
                'is_staff': True,
                'is_superuser': False
            }
        ]
    }
    
    comptes_crees = []
    
    for nom_groupe, comptes in comptes_test.items():
        try:
            groupe = GroupeTravail.objects.get(nom=nom_groupe)
            print(f"\n📋 Création des comptes pour le groupe {nom_groupe}:")
            
            for compte_data in comptes:
                username = compte_data['username']
                
                # Vérifier si l'utilisateur existe déjà
                if Utilisateur.objects.filter(username=username).exists():
                    print(f"⚠️  Compte existant : {username}")
                    continue
                
                # Créer l'utilisateur
                user = Utilisateur.objects.create_user(
                    username=username,
                    email=compte_data['email'],
                    password=compte_data['password'],
                    first_name=compte_data['first_name'],
                    last_name=compte_data['last_name'],
                    groupe_travail=groupe,
                    poste=compte_data['poste'],
                    departement=compte_data['departement'],
                    date_embauche=compte_data['date_embauche'],
                    actif=True
                )
                
                # Définir les permissions spéciales pour PRIVILEGE
                if nom_groupe == 'PRIVILEGE':
                    user.is_staff = compte_data.get('is_staff', False)
                    user.is_superuser = compte_data.get('is_superuser', False)
                    user.save()
                
                print(f"✅ Compte créé : {username} ({compte_data['first_name']} {compte_data['last_name']})")
                comptes_crees.append(user)
                
        except GroupeTravail.DoesNotExist:
            print(f"❌ Groupe {nom_groupe} non trouvé")
    
    return comptes_crees

def afficher_resume():
    """Affiche un résumé de l'initialisation"""
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE L'INITIALISATION")
    print("="*60)
    
    # Statistiques des groupes
    groupes = GroupeTravail.objects.all()
    print(f"\n🏢 Groupes de travail : {groupes.count()}")
    for groupe in groupes:
        utilisateurs_count = groupe.utilisateurs.count()
        print(f"   • {groupe.nom}: {utilisateurs_count} utilisateur(s)")
    
    # Statistiques des utilisateurs
    total_utilisateurs = Utilisateur.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    print(f"\n👥 Utilisateurs : {total_utilisateurs} total, {utilisateurs_actifs} actifs")
    
    # Comptes de test par groupe
    print(f"\n🔑 Comptes de test disponibles :")
    for groupe in groupes:
        utilisateurs = groupe.utilisateurs.filter(actif=True)
        if utilisateurs.exists():
            print(f"\n   📋 {groupe.nom}:")
            for user in utilisateurs:
                print(f"      • {user.username} / {user.get_full_name()}")
                print(f"        Mot de passe : {groupe.nom.lower()}123")
    
    print(f"\n🚀 URL de connexion : http://127.0.0.1:8000/")
    print(f"📝 Première page : Sélection du groupe de travail")
    
    print(f"\n" + "="*60)

def main():
    """Fonction principale d'initialisation"""
    
    print("🚀 Initialisation des groupes de travail et comptes de test")
    print("="*60)
    
    try:
        with transaction.atomic():
            # Initialiser les groupes de travail
            print("\n1️⃣ Initialisation des groupes de travail...")
            groupes = init_groupes_travail()
            
            # Créer les comptes de test
            print("\n2️⃣ Création des comptes de test...")
            comptes = creer_comptes_test()
            
            # Afficher le résumé
            afficher_resume()
            
            print("\n✅ Initialisation terminée avec succès !")
            print("🎉 Vous pouvez maintenant vous connecter avec les comptes créés.")
            
    except Exception as e:
        print(f"\n❌ ERREUR lors de l'initialisation : {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 Prochaines étapes :")
        print("   1. Démarrer le serveur : python manage.py runserver")
        print("   2. Aller sur : http://127.0.0.1:8000/")
        print("   3. Sélectionner un groupe de travail")
        print("   4. Se connecter avec un compte de test")
    else:
        print("\n🔧 Veuillez vérifier la configuration et réessayer.") 