#!/usr/bin/env python
"""
Script d'initialisation automatique pour Render
S'exécute au démarrage pour créer les groupes et utilisateurs de test
"""

import os
import django

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien
from django.contrib.auth.hashers import make_password

def init_groupes():
    """Initialise les groupes de travail"""
    print("🏢 Initialisation des groupes de travail...")
    
    groupes_data = [
        {'nom': 'CAISSE', 'description': 'Gestion des paiements et retraits'},
        {'nom': 'CONTROLES', 'description': 'Contrôle et audit'},
        {'nom': 'ADMINISTRATION', 'description': 'Gestion administrative'},
        {'nom': 'PRIVILEGE', 'description': 'Accès complet'},
    ]
    
    for groupe_data in groupes_data:
        groupe, created = GroupeTravail.objects.update_or_create(
            nom=groupe_data['nom'],
            defaults={
                'description': groupe_data['description'],
                'actif': True,
                'permissions': {}
            }
        )
        if created:
            print(f"✅ Groupe créé: {groupe.nom}")
        else:
            print(f"ℹ️  Groupe existant: {groupe.nom}")
    
    return GroupeTravail.objects.all()

def init_types_bien():
    """Initialise les types de biens"""
    print("🏠 Initialisation des types de biens...")
    
    types_data = [
        {'nom': 'Appartement', 'description': 'Appartement en immeuble'},
        {'nom': 'Maison', 'description': 'Maison individuelle'},
        {'nom': 'Studio', 'description': 'Studio meublé'},
        {'nom': 'Loft', 'description': 'Loft industriel'},
        {'nom': 'Villa', 'description': 'Villa avec jardin'},
        {'nom': 'Duplex', 'description': 'Duplex sur deux niveaux'},
        {'nom': 'Penthouse', 'description': 'Penthouse de luxe'},
        {'nom': 'Château', 'description': 'Château ou manoir'},
        {'nom': 'Ferme', 'description': 'Ferme ou propriété rurale'},
        {'nom': 'Bureau', 'description': 'Local commercial ou bureau'},
        {'nom': 'Commerce', 'description': 'Local commercial'},
        {'nom': 'Entrepôt', 'description': 'Entrepôt ou local industriel'},
        {'nom': 'Garage', 'description': 'Garage ou parking'},
        {'nom': 'Terrain', 'description': 'Terrain constructible'},
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
    
    return TypeBien.objects.all()

def init_utilisateurs_test(groupes):
    """Initialise les utilisateurs de test"""
    print("👥 Initialisation des utilisateurs de test...")
    
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
    
    mot_de_passe = 'password123'
    
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
                'password': make_password(mot_de_passe)
            }
        )
        if created:
            print(f"✅ Utilisateur créé: {user.username} ({user.groupe_travail.nom})")
        else:
            print(f"ℹ️  Utilisateur existant: {user.username}")
    
    return mot_de_passe

def main():
    """Fonction principale d'initialisation"""
    print("🚀 INITIALISATION AUTOMATIQUE POUR RENDER")
    print("=" * 50)
    
    try:
        # 1. Initialiser les groupes
        groupes = init_groupes()
        
        # 2. Initialiser les types de biens
        types_bien = init_types_bien()
        
        # 3. Initialiser les utilisateurs de test
        mot_de_passe = init_utilisateurs_test(groupes)
        
        print("\n" + "=" * 50)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS !")
        print("=" * 50)
        
        print(f"\n📊 Statistiques:")
        print(f"   - Groupes: {GroupeTravail.objects.count()}")
        print(f"   - Types de biens: {TypeBien.objects.count()}")
        print(f"   - Utilisateurs: {Utilisateur.objects.count()}")
        
        print(f"\n🔑 Identifiants de test:")
        print(f"   Mot de passe: {mot_de_passe}")
        print(f"   - admin / {mot_de_passe} (Super Admin)")
        print(f"   - caisse1 / {mot_de_passe} (Groupe Caisse)")
        print(f"   - controle1 / {mot_de_passe} (Groupe Contrôles)")
        print(f"   - admin1 / {mot_de_passe} (Groupe Administration)")
        print(f"   - privilege1 / {mot_de_passe} (Groupe Privilege)")
        
        print(f"\n🌐 L'application est prête à être utilisée !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    main()
