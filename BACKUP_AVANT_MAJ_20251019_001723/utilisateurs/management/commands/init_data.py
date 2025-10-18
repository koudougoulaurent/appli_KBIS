from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail
from core.models import ConfigurationEntreprise, Devise

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialise les données de base pour GESTIMMOB'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Initialisation des données de base pour GESTIMMOB...'))
        self.stdout.write('=' * 60)
        
        self.create_work_groups()
        self.create_test_users()
        self.create_company_config()
        self.create_currencies()
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Initialisation terminée avec succès!'))
        self.stdout.write('\n📋 Informations de connexion:')
        self.stdout.write('   - Admin: admin / password123')
        self.stdout.write('   - Caisse: caisse / password123')
        self.stdout.write('   - Contrôle: controle / password123')
        self.stdout.write('   - Privilège: privilege / password123')
        self.stdout.write('\n🌐 Accédez à l\'application: http://127.0.0.1:8000')

    def create_work_groups(self):
        """Créer les groupes de travail"""
        self.stdout.write('🔧 Création des groupes de travail...')
        
        groups_data = [
            {
                'nom': 'ADMINISTRATION',
                'description': 'Gestion administrative complète',
                'permissions': {
                    'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs', 'notifications']
                }
            },
            {
                'nom': 'CAISSE',
                'description': 'Gestion des paiements et retraits',
                'permissions': {
                    'modules': ['paiements', 'proprietes']
                }
            },
            {
                'nom': 'CONTROLES',
                'description': 'Contrôles et vérifications',
                'permissions': {
                    'modules': ['proprietes', 'contrats', 'paiements']
                }
            },
            {
                'nom': 'PRIVILEGE',
                'description': 'Accès complet au système',
                'permissions': {
                    'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs', 'notifications', 'admin']
                }
            }
        ]
        
        for group_data in groups_data:
            group, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults={
                    'description': group_data['description'],
                    'permissions': group_data['permissions'],
                    'actif': True
                }
            )
            if created:
                self.stdout.write(f'✅ Groupe créé: {group.nom}')
            else:
                self.stdout.write(f'ℹ️  Groupe existant: {group.nom}')

    def create_test_users(self):
        """Créer des utilisateurs de test"""
        self.stdout.write('\n👥 Création des utilisateurs de test...')
        
        # Récupérer les groupes
        admin_group = GroupeTravail.objects.get(nom='ADMINISTRATION')
        caisse_group = GroupeTravail.objects.get(nom='CAISSE')
        controles_group = GroupeTravail.objects.get(nom='CONTROLES')
        privilege_group = GroupeTravail.objects.get(nom='PRIVILEGE')
        
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@gestimmob.fr',
                'first_name': 'Admin',
                'last_name': 'Système',
                'groupe_travail': admin_group,
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'caisse',
                'email': 'caisse@gestimmob.fr',
                'first_name': 'Caissier',
                'last_name': 'Principal',
                'groupe_travail': caisse_group,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'controle',
                'email': 'controle@gestimmob.fr',
                'first_name': 'Contrôleur',
                'last_name': 'Principal',
                'groupe_travail': controles_group,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'privilege',
                'email': 'privilege@gestimmob.fr',
                'first_name': 'Privilégié',
                'last_name': 'Principal',
                'groupe_travail': privilege_group,
                'is_staff': True,
                'is_superuser': False
            }
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'groupe_travail': user_data['groupe_travail'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                    'actif': True
                }
            )
            
            if created:
                user.set_password('password123')  # Mot de passe par défaut
                user.save()
                self.stdout.write(f'✅ Utilisateur créé: {user.username} (mot de passe: password123)')
            else:
                self.stdout.write(f'ℹ️  Utilisateur existant: {user.username}')

    def create_company_config(self):
        """Créer la configuration de l'entreprise"""
        self.stdout.write('\n🏢 Création de la configuration entreprise...')
        
        config, created = ConfigurationEntreprise.objects.get_or_create(
            nom_entreprise='GESTIMMOB',
            defaults={
                'slogan': 'Système de Gestion Immobilière',
                'adresse': '123 Rue de la Paix',
                'code_postal': '75001',
                'ville': 'Paris',
                'pays': 'France',
                'telephone': '01 23 45 67 89',
                'email': 'contact@gestimmob.fr',
                'siret': '123 456 789 00012',
                'numero_licence': '123456789',
                'forme_juridique': 'SARL',
                'actif': True
            }
        )
        
        if created:
            self.stdout.write('✅ Configuration entreprise créée')
        else:
            self.stdout.write('ℹ️  Configuration entreprise existante')

    def create_currencies(self):
        """Créer les devises"""
        self.stdout.write('\n💰 Création des devises...')
        
        currencies_data = [
            {
                'code': 'F CFA',
                'nom': 'Franc CFA',
                'symbole': 'F CFA',
                'taux_change': 1.0,
                'par_defaut': True
            },
            {
                'code': 'EUR',
                'nom': 'Euro',
                'symbole': '€',
                'taux_change': 0.15,
                'par_defaut': False
            },
            {
                'code': 'USD',
                'nom': 'Dollar US',
                'symbole': '$',
                'taux_change': 0.16,
                'par_defaut': False
            }
        ]
        
        for currency_data in currencies_data:
            currency, created = Devise.objects.get_or_create(
                code=currency_data['code'],
                defaults=currency_data
            )
            
            if created:
                self.stdout.write(f'✅ Devise créée: {currency.nom}')
            else:
                self.stdout.write(f'ℹ️  Devise existante: {currency.nom}')

