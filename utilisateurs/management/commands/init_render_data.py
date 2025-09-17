"""
Commande Django pour initialiser les données sur Render
"""
from django.core.management.base import BaseCommand
from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import TypeBien

class Command(BaseCommand):
    help = 'Initialise les données de base sur Render'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Initialisation des données sur Render...")
        
        # Créer les groupes de travail
        groupes_data = [
            {'nom': 'PRIVILEGE', 'description': 'Groupe avec tous les privilèges'},
            {'nom': 'ADMINISTRATION', 'description': 'Groupe d\'administration'},
            {'nom': 'CAISSE', 'description': 'Groupe de gestion de la caisse'},
            {'nom': 'CONTROLES', 'description': 'Groupe de contrôles'},
        ]
        
        for groupe_data in groupes_data:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=groupe_data['nom'],
                defaults={'description': groupe_data['description'], 'actif': True}
            )
            if created:
                self.stdout.write(f"✅ Groupe {groupe.nom} créé")
            else:
                self.stdout.write(f"ℹ️  Groupe {groupe.nom} existe déjà")
        
        # Créer les types de biens
        types_bien = [
            'Appartement', 'Maison', 'Studio', 'Loft', 'Villa', 'Duplex',
            'Penthouse', 'Château', 'Ferme', 'Bureau', 'Commerce', 'Entrepôt',
            'Garage', 'Terrain', 'Autre'
        ]
        
        for type_nom in types_bien:
            type_bien, created = TypeBien.objects.get_or_create(
                nom=type_nom,
                defaults={'actif': True}
            )
            if created:
                self.stdout.write(f"✅ Type {type_nom} créé")
            else:
                self.stdout.write(f"ℹ️  Type {type_nom} existe déjà")
        
        # Créer les utilisateurs de test
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@gestimmob.com',
                'password': 'admin123',
                'first_name': 'Administrateur',
                'last_name': 'Principal',
                'groupe': 'PRIVILEGE'
            },
            {
                'username': 'caisse1',
                'email': 'caisse@gestimmob.com',
                'password': 'caisse123',
                'first_name': 'Caissier',
                'last_name': 'Principal',
                'groupe': 'CAISSE'
            },
            {
                'username': 'controle1',
                'email': 'controle@gestimmob.com',
                'password': 'controle123',
                'first_name': 'Contrôleur',
                'last_name': 'Principal',
                'groupe': 'CONTROLES'
            },
            {
                'username': 'admin1',
                'email': 'admin1@gestimmob.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'Immobilier',
                'groupe': 'ADMINISTRATION'
            },
            {
                'username': 'privilege1',
                'email': 'privilege@gestimmob.com',
                'password': 'privilege123',
                'first_name': 'Privilège',
                'last_name': 'Test',
                'groupe': 'PRIVILEGE'
            }
        ]
        
        for user_data in users_data:
            # Supprimer l'ancien utilisateur s'il existe
            Utilisateur.objects.filter(username=user_data['username']).delete()
            
            # Créer le nouvel utilisateur
            user = Utilisateur.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            
            # Assigner au groupe
            groupe = GroupeTravail.objects.get(nom=user_data['groupe'])
            user.groupe_travail = groupe
            user.save()
            
            self.stdout.write(f"✅ Utilisateur {user.username} créé (Groupe: {groupe.nom})")
        
        self.stdout.write("🎉 Initialisation terminée avec succès!")
        self.stdout.write("\n📋 Informations de connexion pour Render:")
        self.stdout.write("=" * 50)
        for user_data in users_data:
            self.stdout.write(f"👤 {user_data['username']} / {user_data['password']} (Groupe: {user_data['groupe']})")
        self.stdout.write("=" * 50)
        self.stdout.write("🌐 URL: https://appli-kbis.onrender.com/")
