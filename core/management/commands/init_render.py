from django.core.management.base import BaseCommand
from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Initialise les données de base pour Render (groupes, types de biens, utilisateurs de test)'

    def handle(self, *args, **options):
        """Exécute l'initialisation des données"""
        self.stdout.write("🚀 INITIALISATION AUTOMATIQUE POUR RENDER")
        self.stdout.write("=" * 50)
        
        try:
            # 1. Initialiser les groupes
            self.init_groupes()
            
            # 2. Initialiser les types de biens
            self.init_types_bien()
            
            # 3. Initialiser les utilisateurs de test
            self.init_utilisateurs_test()
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.SUCCESS("✅ INITIALISATION TERMINÉE AVEC SUCCÈS !")
            )
            self.stdout.write("=" * 50)
            
            self.stdout.write(f"\n📊 Statistiques:")
            self.stdout.write(f"   - Groupes: {GroupeTravail.objects.count()}")
            self.stdout.write(f"   - Types de biens: {TypeBien.objects.count()}")
            self.stdout.write(f"   - Utilisateurs: {Utilisateur.objects.count()}")
            
            self.stdout.write(f"\n🔑 Identifiants de test:")
            self.stdout.write(f"   Mot de passe: password123")
            self.stdout.write(f"   - admin / password123 (Super Admin)")
            self.stdout.write(f"   - caisse1 / password123 (Groupe Caisse)")
            self.stdout.write(f"   - controle1 / password123 (Groupe Contrôles)")
            self.stdout.write(f"   - admin1 / password123 (Groupe Administration)")
            self.stdout.write(f"   - privilege1 / password123 (Groupe Privilege)")
            
            self.stdout.write(f"\n🌐 L'application est prête à être utilisée !")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur lors de l'initialisation: {e}")
            )
            import traceback
            traceback.print_exc()

    def init_groupes(self):
        """Initialise les groupes de travail"""
        self.stdout.write("🏢 Initialisation des groupes de travail...")
        
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
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Groupe créé: {groupe.nom}")
                )
            else:
                self.stdout.write(f"ℹ️  Groupe existant: {groupe.nom}")

    def init_types_bien(self):
        """Initialise les types de biens"""
        self.stdout.write("🏠 Initialisation des types de biens...")
        
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
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Type créé: {type_bien.nom}")
                )
            else:
                self.stdout.write(f"ℹ️  Type existant: {type_bien.nom}")

    def init_utilisateurs_test(self):
        """Initialise les utilisateurs de test"""
        self.stdout.write("👥 Initialisation des utilisateurs de test...")
        
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
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Utilisateur créé: {user.username} ({user.groupe_travail.nom})")
                )
            else:
                self.stdout.write(f"ℹ️  Utilisateur existant: {user.username}")
