#!/usr/bin/env python
"""
Script de vérification automatique des données
S'exécute à chaque démarrage pour s'assurer que les données essentielles existent
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien
from django.contrib.auth.hashers import make_password

def verifier_et_creer_donnees():
    """Vérifie et crée les données essentielles si elles n'existent pas"""
    
    print("🔍 VÉRIFICATION AUTOMATIQUE DES DONNÉES")
    print("=" * 50)
    
    # 1. Vérifier les groupes de travail
    groupes_requis = ['CAISSE', 'CONTROLES', 'ADMINISTRATION', 'PRIVILEGE']
    groupes_manquants = []
    
    for nom_groupe in groupes_requis:
        if not GroupeTravail.objects.filter(nom=nom_groupe, actif=True).exists():
            groupes_manquants.append(nom_groupe)
    
    if groupes_manquants:
        print(f"⚠️  Groupes manquants: {', '.join(groupes_manquants)}")
        creer_groupes_manquants(groupes_manquants)
    else:
        print("✅ Tous les groupes de travail sont présents")
    
    # 2. Vérifier les types de biens
    types_requis = ['Appartement', 'Maison', 'Studio', 'Loft', 'Villa']
    types_manquants = []
    
    for nom_type in types_requis:
        if not TypeBien.objects.filter(nom=nom_type).exists():
            types_manquants.append(nom_type)
    
    if types_manquants:
        print(f"⚠️  Types de biens manquants: {', '.join(types_manquants)}")
        creer_types_manquants(types_manquants)
    else:
        print("✅ Tous les types de biens sont présents")
    
    # 3. Vérifier les utilisateurs de test
    if not Utilisateur.objects.filter(username='admin').exists():
        print("⚠️  Utilisateur admin manquant")
        creer_utilisateurs_test()
    else:
        print("✅ Utilisateur admin présent")
    
    print("\n" + "=" * 50)
    print("📊 STATISTIQUES FINALES:")
    print(f"   - Groupes: {GroupeTravail.objects.filter(actif=True).count()}")
    print(f"   - Types de biens: {TypeBien.objects.count()}")
    print(f"   - Utilisateurs: {Utilisateur.objects.count()}")
    print("✅ Vérification terminée !")

def creer_groupes_manquants(groupes_manquants):
    """Crée les groupes de travail manquants"""
    
    descriptions = {
        'CAISSE': 'Gestion des paiements et retraits',
        'CONTROLES': 'Contrôle et audit',
        'ADMINISTRATION': 'Gestion administrative',
        'PRIVILEGE': 'Accès complet'
    }
    
    for nom in groupes_manquants:
        groupe, created = GroupeTravail.objects.update_or_create(
            nom=nom,
            defaults={
                'description': descriptions.get(nom, ''),
                'actif': True,
                'permissions': {}
            }
        )
        if created:
            print(f"✅ Groupe créé: {nom}")
        else:
            print(f"🔄 Groupe réactivé: {nom}")

def creer_types_manquants(types_manquants):
    """Crée les types de biens manquants"""
    
    descriptions = {
        'Appartement': 'Appartement en immeuble',
        'Maison': 'Maison individuelle',
        'Studio': 'Studio meublé',
        'Loft': 'Loft industriel',
        'Villa': 'Villa avec jardin'
    }
    
    for nom in types_manquants:
        type_bien, created = TypeBien.objects.update_or_create(
            nom=nom,
            defaults={'description': descriptions.get(nom, '')}
        )
        if created:
            print(f"✅ Type créé: {nom}")

def creer_utilisateurs_test():
    """Crée les utilisateurs de test manquants"""
    
    try:
        groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
        groupe_caisse = GroupeTravail.objects.get(nom='CAISSE')
        groupe_controles = GroupeTravail.objects.get(nom='CONTROLES')
        groupe_admin = GroupeTravail.objects.get(nom='ADMINISTRATION')
        
        utilisateurs_data = [
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
                    'password': make_password('password123')
                }
            )
            if created:
                print(f"✅ Utilisateur créé: {user.username}")
            else:
                print(f"ℹ️  Utilisateur existant: {user.username}")
                
    except Exception as e:
        print(f"❌ Erreur lors de la création des utilisateurs: {e}")

if __name__ == '__main__':
    verifier_et_creer_donnees()
