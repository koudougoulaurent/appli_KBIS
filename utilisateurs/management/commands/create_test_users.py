from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée des utilisateurs de test persistants pour le développement et les tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la création même si les utilisateurs existent déjà',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Créer les groupes de travail s'ils n'existent pas
        self.create_groups()
        
        # Créer les utilisateurs de test
        self.create_test_users(force)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Utilisateurs de test créés avec succès!')
        )

    def create_groups(self):
        """Crée les groupes de travail nécessaires."""
        groups_data = [
            {
                'nom': 'PRIVILEGE',
                'description': 'Groupe avec tous les privilèges',
                'permissions': {
                    'modules': ['all'],
                    'actions': ['create', 'read', 'update', 'delete']
                }
            },
            {
                'nom': 'ADMINISTRATION',
                'description': 'Groupe d\'administration',
                'permissions': {
                    'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'],
                    'actions': ['create', 'read', 'update']
                }
            },
            {
                'nom': 'CAISSE',
                'description': 'Groupe de gestion de la caisse',
                'permissions': {
                    'modules': ['paiements', 'contrats'],
                    'actions': ['create', 'read', 'update']
                }
            },
            {
                'nom': 'CONTROLES',
                'description': 'Groupe de contrôles',
                'permissions': {
                    'modules': ['proprietes', 'contrats'],
                    'actions': ['read', 'update']
                }
            }
        ]
        
        for group_data in groups_data:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults={
                    'description': group_data['description'],
                    'permissions': group_data['permissions'],
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f'✅ Groupe {groupe.nom} créé')
            else:
                self.stdout.write(f'ℹ️  Groupe {groupe.nom} existe déjà')

    def create_test_users(self, force=False):
        """Crée les utilisateurs de test."""
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'Test',
                'password': 'admin123',
                'groupe_nom': 'PRIVILEGE',
                'is_staff': True,
                'is_superuser': True,
                'telephone': '+226 70 00 00 01',
                'poste': 'Administrateur Principal',
                'departement': 'Direction'
            },
            {
                'username': 'caisse',
                'email': 'caisse@test.com',
                'first_name': 'Marie',
                'last_name': 'Caisse',
                'password': 'caisse123',
                'groupe_nom': 'CAISSE',
                'is_staff': True,
                'is_superuser': False,
                'telephone': '+226 70 00 00 02',
                'poste': 'Agent de Caisse',
                'departement': 'Finances'
            },
            {
                'username': 'admin_immobilier',
                'email': 'admin.immobilier@test.com',
                'first_name': 'Jean',
                'last_name': 'Immobilier',
                'password': 'admin123',
                'groupe_nom': 'ADMINISTRATION',
                'is_staff': True,
                'is_superuser': False,
                'telephone': '+226 70 00 00 03',
                'poste': 'Administrateur Immobilier',
                'departement': 'Immobilier'
            },
            {
                'username': 'controleur',
                'email': 'controleur@test.com',
                'first_name': 'Sophie',
                'last_name': 'Controleur',
                'password': 'controle123',
                'groupe_nom': 'CONTROLES',
                'is_staff': True,
                'is_superuser': False,
                'telephone': '+226 70 00 00 04',
                'poste': 'Contrôleur',
                'departement': 'Contrôle'
            },
            {
                'username': 'test',
                'email': 'test@test.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'test123',
                'groupe_nom': 'CAISSE',
                'is_staff': False,
                'is_superuser': False,
                'telephone': '+226 70 00 00 05',
                'poste': 'Utilisateur Test',
                'departement': 'Test'
            }
        ]
        
        with transaction.atomic():
            for user_data in users_data:
                groupe_nom = user_data.pop('groupe_nom')
                
                # Vérifier si l'utilisateur existe déjà
                if User.objects.filter(username=user_data['username']).exists():
                    if not force:
                        self.stdout.write(f'ℹ️  Utilisateur {user_data["username"]} existe déjà (utilisez --force pour le recréer)')
                        continue
                    else:
                        # Supprimer l'ancien utilisateur
                        User.objects.filter(username=user_data['username']).delete()
                        self.stdout.write(f'🔄 Utilisateur {user_data["username"]} supprimé et recréé')
                
                # Récupérer le groupe
                try:
                    groupe = GroupeTravail.objects.get(nom=groupe_nom)
                except GroupeTravail.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Groupe {groupe_nom} non trouvé pour {user_data["username"]}')
                    )
                    continue
                
                # Créer l'utilisateur
                user = User.objects.create_user(
                    **user_data
                )
                user.groupe_travail = groupe
                user.save()
                
                self.stdout.write(f'✅ Utilisateur {user.username} créé (Groupe: {groupe.nom})')
        
        # Afficher les informations de connexion
        self.stdout.write('\n' + '='*60)
        self.stdout.write('🔐 INFORMATIONS DE CONNEXION:')
        self.stdout.write('='*60)
        for user_data in users_data:
            self.stdout.write(f'👤 {user_data["username"]} / {user_data["password"]} (Groupe: {user_data["groupe_nom"]})')
        self.stdout.write('='*60)
        self.stdout.write('🌐 URL de connexion: /utilisateurs/connexion-groupes/')
        self.stdout.write('='*60)