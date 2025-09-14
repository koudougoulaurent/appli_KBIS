"""
Signals Django pour l'initialisation automatique des données
S'exécute automatiquement au démarrage de l'application
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def init_data_after_migrate(sender, **kwargs):
    """
    Initialise automatiquement les données après les migrations
    S'exécute à chaque démarrage de l'application
    """
    if sender.name in ['utilisateurs', 'proprietes']:
        try:
            from utilisateurs.models import GroupeTravail, Utilisateur
            from proprietes.models import TypeBien
            from django.contrib.auth.hashers import make_password
            
            logger.info("🚀 Initialisation automatique des données...")
            
            # 1. Créer les groupes de travail
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
                    logger.info(f"✅ Groupe créé: {groupe.nom}")
                else:
                    logger.info(f"ℹ️  Groupe existant: {groupe.nom}")
            
            # 2. Créer les types de biens
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
                    logger.info(f"✅ Type créé: {type_bien.nom}")
                else:
                    logger.info(f"ℹ️  Type existant: {type_bien.nom}")
            
            # 3. Créer les utilisateurs de test s'ils n'existent pas
            if not Utilisateur.objects.filter(username='admin').exists():
                groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
                
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
                        'groupe_travail': GroupeTravail.objects.get(nom='CAISSE'),
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
                        'groupe_travail': GroupeTravail.objects.get(nom='CONTROLES'),
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
                        'groupe_travail': GroupeTravail.objects.get(nom='ADMINISTRATION'),
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
                        logger.info(f"✅ Utilisateur créé: {user.username}")
                    else:
                        logger.info(f"ℹ️  Utilisateur existant: {user.username}")
            
            logger.info("🎉 Initialisation automatique terminée avec succès !")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation automatique: {e}")
            import traceback
            logger.error(traceback.format_exc())
