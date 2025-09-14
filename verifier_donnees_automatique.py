#!/usr/bin/env python3
"""
Script de création automatique des données permanentes pour Render
Crée tous les utilisateurs de test, groupes et types de biens nécessaires
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien
import logging

logger = logging.getLogger(__name__)

def creer_donnees_permanentes():
    """Crée toutes les données permanentes nécessaires pour l'application"""
    try:
        print("🚀 CRÉATION DES DONNÉES PERMANENTES POUR RENDER")
        print("=" * 50)
        
        # 1. Créer les groupes de travail avec permissions détaillées
        print("\n📋 Création des groupes de travail...")
        groupes_data = [
            {
                'nom': 'CAISSE',
                'description': 'Gestion des paiements et retraits',
                'permissions': {
                    'modules': ['paiements', 'retraits', 'recus'],
                    'actions': ['voir', 'creer', 'modifier', 'valider'],
                    'restrictions': ['pas_suppression']
                }
            },
            {
                'nom': 'CONTROLES',
                'description': 'Contrôle et audit des opérations',
                'permissions': {
                    'modules': ['paiements', 'retraits', 'contrats', 'proprietes'],
                    'actions': ['voir', 'auditer', 'rapporter'],
                    'restrictions': ['lecture_seule']
                }
            },
            {
                'nom': 'ADMINISTRATION',
                'description': 'Gestion administrative complète',
                'permissions': {
                    'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'],
                    'actions': ['voir', 'creer', 'modifier', 'supprimer'],
                    'restrictions': ['pas_superuser']
                }
            },
            {
                'nom': 'PRIVILEGE',
                'description': 'Accès complet à toutes les fonctionnalités',
                'permissions': {
                    'modules': ['tous'],
                    'actions': ['tous'],
                    'restrictions': ['aucune']
                }
            },
        ]
        
        for groupe_data in groupes_data:
            groupe, created = GroupeTravail.objects.update_or_create(
                nom=groupe_data['nom'],
                defaults={
                    'description': groupe_data['description'],
                    'actif': True,
                    'permissions': groupe_data['permissions']
                }
            )
            if created:
                print(f"✅ Groupe créé: {groupe.nom} - {groupe.description}")
            else:
                print(f"ℹ️  Groupe existant: {groupe.nom}")
        
        # 2. Créer les types de biens complets
        print("\n🏠 Création des types de biens...")
        types_data = [
            # Résidentiel
            {'nom': 'Appartement', 'description': 'Appartement en immeuble collectif'},
            {'nom': 'Maison', 'description': 'Maison individuelle avec jardin'},
            {'nom': 'Studio', 'description': 'Studio meublé pour célibataires'},
            {'nom': 'Duplex', 'description': 'Duplex sur deux niveaux'},
            {'nom': 'Penthouse', 'description': 'Penthouse de luxe en étage'},
            {'nom': 'Villa', 'description': 'Villa avec piscine et jardin'},
            {'nom': 'Château', 'description': 'Château ou manoir historique'},
            {'nom': 'Ferme', 'description': 'Ferme ou propriété rurale'},
            {'nom': 'Loft', 'description': 'Loft industriel rénové'},
            {'nom': 'T3', 'description': 'Appartement 3 pièces'},
            {'nom': 'T4', 'description': 'Appartement 4 pièces'},
            {'nom': 'T5+', 'description': 'Appartement 5 pièces et plus'},
            
            # Commercial
            {'nom': 'Bureau', 'description': 'Local commercial ou bureau'},
            {'nom': 'Commerce', 'description': 'Local commercial de vente'},
            {'nom': 'Entrepôt', 'description': 'Entrepôt ou local industriel'},
            {'nom': 'Garage', 'description': 'Garage ou parking privé'},
            {'nom': 'Cave', 'description': 'Cave ou cellier'},
            {'nom': 'Terrain', 'description': 'Terrain constructible'},
            {'nom': 'Parking', 'description': 'Place de parking'},
            {'nom': 'Box', 'description': 'Box de stockage'},
            
            # Spécialisé
            {'nom': 'Chambre', 'description': 'Chambre individuelle'},
            {'nom': 'Colocation', 'description': 'Colocation partagée'},
            {'nom': 'Résidence', 'description': 'Résidence étudiante'},
            {'nom': 'Hôtel', 'description': 'Hôtel ou établissement hôtelier'},
            {'nom': 'Restaurant', 'description': 'Restaurant ou bar'},
            {'nom': 'Autre', 'description': 'Autre type de bien'},
        ]
        
        for type_data in types_data:
            type_bien, created = TypeBien.objects.update_or_create(
                nom=type_data['nom'],
                defaults=type_data
            )
            if created:
                print(f"✅ Type créé: {type_bien.nom}")
            else:
                print(f"ℹ️  Type existant: {type_bien.nom}")
        
        # 3. Créer tous les utilisateurs de test
        print("\n👥 Création des utilisateurs de test...")
        
        # Récupérer les groupes
        groupe_caisse = GroupeTravail.objects.get(nom='CAISSE')
        groupe_controles = GroupeTravail.objects.get(nom='CONTROLES')
        groupe_admin = GroupeTravail.objects.get(nom='ADMINISTRATION')
        groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
        
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
                'departement': 'Direction',
                'telephone': '+225 07 00 00 00 01'
            },
            # Utilisateurs CAISSE
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
                'departement': 'Finances',
                'telephone': '+225 07 00 00 00 02'
            },
            {
                'username': 'caisse2',
                'email': 'caisse2@gestimmob.com',
                'first_name': 'Fatou',
                'last_name': 'Traoré',
                'groupe_travail': groupe_caisse,
                'is_staff': False,
                'is_superuser': False,
                'actif': True,
                'poste': 'Agent de caisse',
                'departement': 'Finances',
                'telephone': '+225 07 00 00 00 03'
            },
            # Utilisateurs CONTROLES
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
                'departement': 'Audit',
                'telephone': '+225 07 00 00 00 04'
            },
            {
                'username': 'audit1',
                'email': 'audit1@gestimmob.com',
                'first_name': 'Jean',
                'last_name': 'Auditeur',
                'groupe_travail': groupe_controles,
                'is_staff': False,
                'is_superuser': False,
                'actif': True,
                'poste': 'Auditeur',
                'departement': 'Audit',
                'telephone': '+225 07 00 00 00 05'
            },
            # Utilisateurs ADMINISTRATION
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
                'departement': 'Administration',
                'telephone': '+225 07 00 00 00 06'
            },
            {
                'username': 'gestion1',
                'email': 'gestion1@gestimmob.com',
                'first_name': 'Paul',
                'last_name': 'Gestionnaire',
                'groupe_travail': groupe_admin,
                'is_staff': True,
                'is_superuser': False,
                'actif': True,
                'poste': 'Gestionnaire',
                'departement': 'Administration',
                'telephone': '+225 07 00 00 00 07'
            },
            # Utilisateurs PRIVILEGE
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
                'departement': 'Direction',
                'telephone': '+225 07 00 00 00 08'
            },
            {
                'username': 'directeur',
                'email': 'directeur@gestimmob.com',
                'first_name': 'Directeur',
                'last_name': 'Général',
                'groupe_travail': groupe_privilege,
                'is_staff': True,
                'is_superuser': True,
                'actif': True,
                'poste': 'Directeur Général',
                'departement': 'Direction',
                'telephone': '+225 07 00 00 00 09'
            },
            # Utilisateur de démonstration
            {
                'username': 'demo',
                'email': 'demo@gestimmob.com',
                'first_name': 'Démo',
                'last_name': 'Utilisateur',
                'groupe_travail': groupe_privilege,
                'is_staff': True,
                'is_superuser': False,
                'actif': True,
                'poste': 'Utilisateur Démo',
                'departement': 'Démonstration',
                'telephone': '+225 07 00 00 00 10'
            }
        ]
        
        for user_data in utilisateurs_data:
            user, created = Utilisateur.objects.update_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'groupe_travail': user_data['groupe_travail'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                    'actif': user_data['actif'],
                    'poste': user_data['poste'],
                    'departement': user_data['departement'],
                    'telephone': user_data['telephone'],
                    'password': make_password('password123')
                }
            )
            if created:
                print(f"✅ Utilisateur créé: {user.username} ({user.first_name} {user.last_name}) - {user.poste}")
            else:
                print(f"ℹ️  Utilisateur existant: {user.username}")
        
        # 4. Résumé final
        print("\n📊 RÉSUMÉ DE LA CRÉATION DES DONNÉES")
        print("=" * 40)
        print(f"✅ Groupes de travail: {GroupeTravail.objects.count()}")
        print(f"✅ Types de biens: {TypeBien.objects.count()}")
        print(f"✅ Utilisateurs: {Utilisateur.objects.count()}")
        print(f"✅ Utilisateurs actifs: {Utilisateur.objects.filter(actif=True).count()}")
        
        print("\n🔑 INFORMATIONS DE CONNEXION")
        print("=" * 30)
        print("Tous les utilisateurs ont le mot de passe: password123")
        print("\nUtilisateurs principaux:")
        print("• admin (Super Administrateur)")
        print("• directeur (Directeur Général)")
        print("• privilege1 (Manager)")
        print("• admin1 (Administratrice)")
        print("• caisse1 (Caissière)")
        print("• controle1 (Contrôleuse)")
        print("• demo (Utilisateur Démo)")
        
        print("\n🎉 CRÉATION DES DONNÉES PERMANENTES TERMINÉE AVEC SUCCÈS !")
        print("L'application est maintenant prête à être utilisée sur Render.")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    creer_donnees_permanentes()