"""
Commande Django pour créer des utilisateurs de test
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from utilisateurs.models import Utilisateur, GroupeTravail
from datetime import date

class Command(BaseCommand):
    help = 'Crée des utilisateurs de test pour l\'application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Création des utilisateurs de test pour GESTIMMOB'))
        
        # Créer les groupes de travail
        self.create_groups()
        
        # Créer les utilisateurs de test
        self.create_test_users()
        
        # Afficher la liste des utilisateurs
        self.display_users()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Création terminée avec succès !'))

    def create_groups(self):
        """Créer les groupes de travail s'ils n'existent pas"""
        self.stdout.write('🔧 Création des groupes de travail...')
        
        groups_data = [
            {
                'nom': 'CAISSE',
                'description': 'Groupe pour la gestion de la caisse et des paiements',
                'permissions': {
                    'modules': ['paiements', 'retraits', 'recapitulatifs'],
                    'actions': ['view', 'add', 'change', 'delete']
                }
            },
            {
                'nom': 'CONTROLES',
                'description': 'Groupe pour les contrôles et validations',
                'permissions': {
                    'modules': ['paiements', 'contrats', 'proprietes'],
                    'actions': ['view', 'change']
                }
            },
            {
                'nom': 'ADMINISTRATION',
                'description': 'Groupe pour l\'administration générale',
                'permissions': {
                    'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'],
                    'actions': ['view', 'add', 'change']
                }
            },
            {
                'nom': 'PRIVILEGE',
                'description': 'Groupe avec tous les privilèges',
                'permissions': {
                    'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements', 'retraits', 'recapitulatifs'],
                    'actions': ['view', 'add', 'change', 'delete']
                }
            }
        ]
        
        for group_data in groups_data:
            group, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults=group_data
            )
            if created:
                self.stdout.write(f'   ✅ Groupe {group.nom} créé')
            else:
                self.stdout.write(f'   ℹ️  Groupe {group.nom} existe déjà')

    def create_test_users(self):
        """Créer des utilisateurs de test"""
        self.stdout.write('\n👥 Création des utilisateurs de test...')
        
        # Récupérer les groupes
        groupe_caisse = GroupeTravail.objects.get(nom='CAISSE')
        groupe_controles = GroupeTravail.objects.get(nom='CONTROLES')
        groupe_admin = GroupeTravail.objects.get(nom='ADMINISTRATION')
        groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
        
        users_data = [
            # Superutilisateur
            {
                'username': 'admin',
                'email': 'admin@gestimmob.com',
                'password': 'admin123',
                'first_name': 'Administrateur',
                'last_name': 'Système',
                'is_staff': True,
                'is_superuser': True,
                'groupe_travail': groupe_privilege,
                'poste': 'Administrateur Système',
                'departement': 'IT',
                'telephone': '+225 07 12 34 56 78',
                'adresse': 'Abidjan, Côte d\'Ivoire'
            },
            # Groupe CAISSE
            {
                'username': 'caisse1',
                'email': 'caisse1@gestimmob.com',
                'password': 'caisse123',
                'first_name': 'Marie',
                'last_name': 'Kouassi',
                'groupe_travail': groupe_caisse,
                'poste': 'Agent de Caisse',
                'departement': 'Finance',
                'telephone': '+225 07 23 45 67 89',
                'adresse': 'Cocody, Abidjan'
            },
            {
                'username': 'caisse2',
                'email': 'caisse2@gestimmob.com',
                'password': 'caisse123',
                'first_name': 'Jean',
                'last_name': 'Traoré',
                'groupe_travail': groupe_caisse,
                'poste': 'Responsable Caisse',
                'departement': 'Finance',
                'telephone': '+225 07 34 56 78 90',
                'adresse': 'Plateau, Abidjan'
            },
            # Groupe CONTROLES
            {
                'username': 'controle1',
                'email': 'controle1@gestimmob.com',
                'password': 'controle123',
                'first_name': 'Fatou',
                'last_name': 'Diabaté',
                'groupe_travail': groupe_controles,
                'poste': 'Contrôleur',
                'departement': 'Contrôle',
                'telephone': '+225 07 45 67 89 01',
                'adresse': 'Yopougon, Abidjan'
            },
            {
                'username': 'controle2',
                'email': 'controle2@gestimmob.com',
                'password': 'controle123',
                'first_name': 'Kouassi',
                'last_name': 'Koné',
                'groupe_travail': groupe_controles,
                'poste': 'Superviseur Contrôle',
                'departement': 'Contrôle',
                'telephone': '+225 07 56 78 90 12',
                'adresse': 'Marcory, Abidjan'
            },
            # Groupe ADMINISTRATION
            {
                'username': 'admin1',
                'email': 'admin1@gestimmob.com',
                'password': 'admin123',
                'first_name': 'Aminata',
                'last_name': 'Sangaré',
                'groupe_travail': groupe_admin,
                'poste': 'Gestionnaire',
                'departement': 'Administration',
                'telephone': '+225 07 67 89 01 23',
                'adresse': 'Riviera, Abidjan'
            },
            {
                'username': 'admin2',
                'email': 'admin2@gestimmob.com',
                'password': 'admin123',
                'first_name': 'Moussa',
                'last_name': 'Ouattara',
                'groupe_travail': groupe_admin,
                'poste': 'Chef Administration',
                'departement': 'Administration',
                'telephone': '+225 07 78 90 12 34',
                'adresse': 'Angré, Abidjan'
            },
            # Groupe PRIVILEGE
            {
                'username': 'privilege1',
                'email': 'privilege1@gestimmob.com',
                'password': 'privilege123',
                'first_name': 'Kadiatou',
                'last_name': 'Coulibaly',
                'groupe_travail': groupe_privilege,
                'poste': 'Directeur',
                'departement': 'Direction',
                'telephone': '+225 07 89 01 23 45',
                'adresse': 'Zone 4, Abidjan'
            },
            {
                'username': 'privilege2',
                'email': 'privilege2@gestimmob.com',
                'password': 'privilege123',
                'first_name': 'Ibrahim',
                'last_name': 'Bamba',
                'groupe_travail': groupe_privilege,
                'poste': 'Directeur Adjoint',
                'departement': 'Direction',
                'telephone': '+225 07 90 12 34 56',
                'adresse': 'Bingerville, Abidjan'
            }
        ]
        
        for user_data in users_data:
            username = user_data['username']
            password = user_data.pop('password')
            
            user, created = Utilisateur.objects.get_or_create(
                username=username,
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'   ✅ Utilisateur {username} créé ({user.get_nom_complet()})')
            else:
                self.stdout.write(f'   ℹ️  Utilisateur {username} existe déjà')

    def display_users(self):
        """Afficher la liste des utilisateurs créés"""
        self.stdout.write('\n📋 Liste des utilisateurs de test :')
        self.stdout.write('=' * 80)
        
        for group in GroupeTravail.objects.all():
            self.stdout.write(f'\n🔹 Groupe {group.nom}:')
            users = Utilisateur.objects.filter(groupe_travail=group)
            for user in users:
                self.stdout.write(f'   • {user.username} - {user.get_nom_complet()}')
                self.stdout.write(f'     Email: {user.email}')
                self.stdout.write(f'     Poste: {user.poste}')
                self.stdout.write(f'     Téléphone: {user.telephone}')
                self.stdout.write('')
        
        self.stdout.write('\n🔑 Informations de connexion :')
        self.stdout.write('   • Superutilisateur: admin / admin123')
        self.stdout.write('   • Caisse: caisse1 / caisse123')
        self.stdout.write('   • Contrôle: controle1 / controle123')
        self.stdout.write('   • Administration: admin1 / admin123')
        self.stdout.write('   • Privilège: privilege1 / privilege123')
