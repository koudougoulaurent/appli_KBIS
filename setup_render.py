#!/usr/bin/env python3
"""
Script de configuration initiale pour Render avec support PostgreSQL progressif
"""
import os
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

def get_database_info():
    """Récupère les informations sur la base de données"""
    from django.conf import settings
    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']
    
    if 'postgresql' in engine:
        return "PostgreSQL", db_config.get('NAME', 'N/A')
    elif 'sqlite' in engine:
        return "SQLite", db_config.get('NAME', 'N/A')
    else:
        return "Autre", db_config.get('NAME', 'N/A')

def test_database_connection():
    """Teste la connexion à la base de données"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Connexion base de données réussie: {result}")
            return True
    except Exception as e:
        print(f"❌ Erreur connexion base de données: {e}")
        return False

def create_superuser():
    """Créer le superutilisateur"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='System'
            )
            print("OK Superutilisateur cree: admin/admin123")
        else:
            print("INFO Superutilisateur existe deja")
    except Exception as e:
        print(f"ERREUR creation superutilisateur: {e}")

def create_groups():
    """Créer les groupes de travail"""
    try:
        from utilisateurs.models import GroupeTravail
        
        groups = [
            {
                'nom': 'ADMINISTRATION', 
                'description': 'Gestion administrative et comptable complète',
                'permissions': {'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs', 'core', 'notifications'], 'actions': ['view', 'add', 'change', 'delete', 'admin']},
                'actif': True
            },
            {
                'nom': 'CAISSE', 
                'description': 'Gestion des paiements et encaissements',
                'permissions': {'modules': ['paiements', 'proprietes'], 'actions': ['view', 'add', 'change']},
                'actif': True
            },
            {
                'nom': 'CONTROLES', 
                'description': 'Contrôles et vérifications des données',
                'permissions': {'modules': ['proprietes', 'contrats', 'paiements'], 'actions': ['view']},
                'actif': True
            },
            {
                'nom': 'PRIVILEGE', 
                'description': 'Accès privilégié aux fonctionnalités avancées',
                'permissions': {'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs', 'core'], 'actions': ['view', 'add', 'change']},
                'actif': True
            },
        ]
        
        for group_data in groups:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults={
                    'description': group_data['description'],
                    'permissions': group_data['permissions'],
                    'actif': group_data['actif']
                }
            )
            if created:
                print(f"OK GroupeTravail cree: {group_data['nom']}")
            else:
                print(f"INFO GroupeTravail existe deja: {group_data['nom']}")
                
    except Exception as e:
        print(f"ERREUR creation groupes: {e}")

def create_type_biens():
    """Créer les types de biens"""
    try:
        from proprietes.models import TypeBien
        
        types_data = [
            {'nom': 'Appartement', 'description': 'Logement individuel dans un immeuble collectif'},
            {'nom': 'Maison', 'description': 'Logement individuel de plain-pied ou à étages'},
            {'nom': 'Studio', 'description': 'Logement d\'une seule pièce avec kitchenette'},
            {'nom': 'T1', 'description': 'Logement d\'une pièce principale + cuisine séparée'},
            {'nom': 'T2', 'description': 'Logement de deux pièces principales + cuisine'},
            {'nom': 'T3', 'description': 'Logement de trois pièces principales + cuisine'},
            {'nom': 'T4', 'description': 'Logement de quatre pièces principales + cuisine'},
            {'nom': 'T5+', 'description': 'Logement de cinq pièces ou plus + cuisine'},
            {'nom': 'Bureau', 'description': 'Espace de travail professionnel'},
            {'nom': 'Local commercial', 'description': 'Espace commercial pour commerces et services'},
            {'nom': 'Entrepôt', 'description': 'Espace de stockage et logistique'},
            {'nom': 'Parking', 'description': 'Place de stationnement'},
            {'nom': 'Cave', 'description': 'Espace de stockage souterrain'},
            {'nom': 'Grenier', 'description': 'Espace de stockage sous toit'},
            {'nom': 'Terrain', 'description': 'Parcelle de terrain constructible ou non'},
            {'nom': 'Immeuble', 'description': 'Bâtiment collectif avec plusieurs logements'},
            {'nom': 'Résidence', 'description': 'Ensemble immobilier résidentiel'},
            {'nom': 'Villa', 'description': 'Maison individuelle de standing'},
            {'nom': 'Duplex', 'description': 'Logement sur deux niveaux'},
            {'nom': 'Loft', 'description': 'Logement aménagé dans un ancien local industriel'}
        ]
        
        for type_data in types_data:
            type_bien, created = TypeBien.objects.get_or_create(
                nom=type_data['nom'],
                defaults={'description': type_data['description']}
            )
            if created:
                print(f"OK TypeBien cree: {type_bien.nom}")
            else:
                print(f"INFO TypeBien existe deja: {type_bien.nom}")
                
    except Exception as e:
        print(f"ERREUR creation types biens: {e}")

def create_devises():
    """Créer les devises"""
    try:
        from core.models import Devise
        
        devises_data = [
            {'code': 'XOF', 'nom': 'Franc CFA', 'symbole': 'FCFA', 'actif': True},
            {'code': 'EUR', 'nom': 'Euro', 'symbole': '€', 'actif': True},
            {'code': 'USD', 'nom': 'Dollar US', 'symbole': '$', 'actif': True},
            {'code': 'CAD', 'nom': 'Dollar Canadien', 'symbole': 'C$', 'actif': False},
            {'code': 'GBP', 'nom': 'Livre Sterling', 'symbole': '£', 'actif': False}
        ]
        
        for devise_data in devises_data:
            devise, created = Devise.objects.get_or_create(
                code=devise_data['code'],
                defaults={
                    'nom': devise_data['nom'],
                    'symbole': devise_data['symbole'],
                    'actif': devise_data['actif']
                }
            )
            if created:
                print(f"OK Devise creee: {devise.code} - {devise.nom}")
            else:
                print(f"INFO Devise existe deja: {devise.code}")
                
    except Exception as e:
        print(f"ERREUR creation devises: {e}")

def create_configuration_entreprise():
    """Créer la configuration entreprise"""
    try:
        from core.models import ConfigurationEntreprise, Devise
        
        devise_principale = Devise.objects.filter(code='XOF').first()
        config, created = ConfigurationEntreprise.objects.get_or_create(
            nom_entreprise="KBIS Immobilier",
            defaults={
                'adresse': "Adresse de l'entreprise",
                'telephone': "+226 XX XX XX XX",
                'email': "contact@kbis-immobilier.com",
                'site_web': "https://kbis-immobilier.com",
                'devise_principale': devise_principale,
                'actif': True
            }
        )
        
        if created:
            print("OK Configuration entreprise creee")
        else:
            print("INFO Configuration entreprise existe deja")
            
    except Exception as e:
        print(f"ERREUR creation configuration: {e}")

def setup_database():
    """Configuration complète de la base de données avec support PostgreSQL progressif"""
    try:
        print("🚀 CONFIGURATION DE LA BASE DE DONNÉES")
        print("=" * 50)
        
        # Afficher les informations de la base de données
        db_type, db_name = get_database_info()
        print(f"📊 Base de données: {db_type} - {db_name}")
        
        # Tester la connexion
        if not test_database_connection():
            print("❌ Impossible de se connecter à la base de données")
            return False
        
        # Synchroniser la base de données
        print("🔄 Synchronisation de la base de données...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
        print("✅ Base de données synchronisée")
        
        # Créer les groupes
        print("Creation des groupes de travail...")
        create_groups()
        
        # Créer les types de biens
        print("Creation des types de biens...")
        create_type_biens()
        
        # Créer les devises
        print("Creation des devises...")
        create_devises()
        
        # Créer la configuration entreprise
        print("Creation de la configuration entreprise...")
        create_configuration_entreprise()
        
        # Créer le superutilisateur
        print("Creation du superutilisateur...")
        create_superuser()
        
        print("Configuration terminee avec succes!")
        print("Toutes les donnees des champs select sont maintenant disponibles!")
        
    except Exception as e:
        print(f"ERREUR configuration: {e}")

if __name__ == "__main__":
    setup_database()
