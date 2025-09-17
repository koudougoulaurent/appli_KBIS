"""
Commande Django pour créer les utilisateurs de test
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from proprietes.models import TypeBien
from core.models import ConfigurationEntreprise
from utilisateurs.models import GroupeTravail

User = get_user_model()

class Command(BaseCommand):
    help = 'Créer les utilisateurs de test et données de base'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Création des utilisateurs et données...")
        
        # Create GroupeTravail (groupes de travail personnalisés)
        groupes_data = [
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
        
        groupes = {}
        for group_data in groupes_data:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults={
                    'description': group_data['description'],
                    'permissions': group_data['permissions'],
                    'actif': True
                }
            )
            groupes[group_data['nom']] = groupe
            if created:
                self.stdout.write(f"✅ GroupeTravail: {group_data['nom']}")
            else:
                self.stdout.write(f"ℹ️ GroupeTravail: {group_data['nom']} existe déjà")
        
        # Create superuser (force update for SQLite)
        try:
            admin = User.objects.get(username='admin')
            admin.delete()
            self.stdout.write("🗑️ Ancien admin supprimé")
        except User.DoesNotExist:
            pass
        
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        admin.is_superuser = True
        admin.is_staff = True
        admin.groupe_travail = groupes['ADMINISTRATION']
        admin.save()
        self.stdout.write("✅ Superuser 'admin' créé")
        
        # Create test users (force recreation for SQLite)
        test_users = [
            {'username': 'caisse1', 'email': 'caisse1@example.com', 'password': 'caisse123', 'groupe': 'CAISSE'},
            {'username': 'controle1', 'email': 'controle1@example.com', 'password': 'controle123', 'groupe': 'CONTROLES'},
            {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin123', 'groupe': 'ADMINISTRATION'},
            {'username': 'privilege1', 'email': 'privilege1@example.com', 'password': 'privilege123', 'groupe': 'PRIVILEGE'},
        ]
        
        for user_data in test_users:
            # Delete existing user if exists
            try:
                existing_user = User.objects.get(username=user_data['username'])
                existing_user.delete()
                self.stdout.write(f"🗑️ Ancien utilisateur {user_data['username']} supprimé")
            except User.DoesNotExist:
                pass
            
            # Create new user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            user.is_staff = True
            user.groupe_travail = groupes[user_data['groupe']]
            user.save()
            
            self.stdout.write(f"✅ Utilisateur: {user_data['username']} créé avec groupe {user_data['groupe']}")
        
        # Create property types
        types_bien = [
            'Appartement', 'Maison', 'Studio', 'Loft', 'Villa', 'Duplex',
            'Penthouse', 'Château', 'Ferme', 'Bureau', 'Commerce',
            'Entrepôt', 'Garage', 'Terrain', 'Autre'
        ]
        
        for type_name in types_bien:
            type_bien, created = TypeBien.objects.get_or_create(nom=type_name)
            if created:
                self.stdout.write(f"✅ Type créé: {type_name}")
        
        # Create company configuration
        config, created = ConfigurationEntreprise.objects.get_or_create(
            nom_entreprise="Gestion Immobilière KBIS",
            defaults={
                'adresse': "123 Rue de l'Immobilier",
                'ville': "Ouagadougou",
                'code_postal': "01 BP 1234",
                'telephone': "+226 25 12 34 56",
                'email': "contact@kbis.bf"
            }
        )
        if created:
            self.stdout.write("✅ Configuration entreprise créée")
        else:
            self.stdout.write("✅ Configuration entreprise existante")
        
        # Test des connexions
        self.stdout.write("\n🔍 Test des connexions...")
        from django.contrib.auth import authenticate
        
        test_credentials = [
            ('admin', 'admin123'),
            ('caisse1', 'caisse123'),
            ('controle1', 'controle123'),
            ('admin1', 'admin123'),
            ('privilege1', 'privilege123'),
        ]
        
        for username, password in test_credentials:
            user = authenticate(username=username, password=password)
            if user:
                groups = [group.name for group in user.groups.all()]
                self.stdout.write(f"✅ {username}: Connexion réussie - Groupes: {', '.join(groups)}")
            else:
                self.stdout.write(f"❌ {username}: Échec de connexion")
        
        self.stdout.write("\n🎉 Tous les utilisateurs et données créés avec succès !")
