"""
Middleware de vérification des données essentielles
Vérifie à chaque requête que les données de base existent
"""

from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class DataVerificationMiddleware:
    """
    Middleware qui vérifie que les données essentielles existent
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._data_verified = False

    def __call__(self, request):
        # Vérifier les données seulement une fois par session
        if not self._data_verified and not request.path.startswith('/static/'):
            self._verify_essential_data()
            self._data_verified = True

        response = self.get_response(request)
        return response

    def _verify_essential_data(self):
        """Vérifie que les données essentielles existent"""
        try:
            from utilisateurs.models import GroupeTravail
            from proprietes.models import TypeBien
            
            # Vérifier les groupes de travail
            if not GroupeTravail.objects.filter(actif=True).exists():
                logger.warning("⚠️  Aucun groupe de travail actif trouvé")
                self._create_essential_data()
            
            # Vérifier les types de biens
            if not TypeBien.objects.exists():
                logger.warning("⚠️  Aucun type de bien trouvé")
                self._create_essential_data()
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification des données: {e}")

    def _create_essential_data(self):
        """Crée les données essentielles si elles n'existent pas"""
        try:
            from utilisateurs.models import GroupeTravail, Utilisateur
            from proprietes.models import TypeBien
            from django.contrib.auth.hashers import make_password
            
            logger.info("🔧 Création des données essentielles...")
            
            # Créer les groupes de travail
            groupes_data = [
                {'nom': 'CAISSE', 'description': 'Gestion des paiements et retraits'},
                {'nom': 'CONTROLES', 'description': 'Contrôle et audit'},
                {'nom': 'ADMINISTRATION', 'description': 'Gestion administrative'},
                {'nom': 'PRIVILEGE', 'description': 'Accès complet'},
            ]
            
            for groupe_data in groupes_data:
                GroupeTravail.objects.update_or_create(
                    nom=groupe_data['nom'],
                    defaults={
                        'description': groupe_data['description'],
                        'actif': True,
                        'permissions': {}
                    }
                )
            
            # Créer les types de biens
            types_data = [
                {'nom': 'Appartement', 'description': 'Appartement en immeuble'},
                {'nom': 'Maison', 'description': 'Maison individuelle'},
                {'nom': 'Studio', 'description': 'Studio meublé'},
                {'nom': 'Loft', 'description': 'Loft industriel'},
                {'nom': 'Villa', 'description': 'Villa avec jardin'},
            ]
            
            for type_data in types_data:
                TypeBien.objects.update_or_create(
                    nom=type_data['nom'],
                    defaults=type_data
                )
            
            # Créer l'utilisateur admin s'il n'existe pas
            if not Utilisateur.objects.filter(username='admin').exists():
                groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
                Utilisateur.objects.create(
                    username='admin',
                    email='admin@gestimmob.com',
                    first_name='Super',
                    last_name='Administrateur',
                    groupe_travail=groupe_privilege,
                    is_staff=True,
                    is_superuser=True,
                    actif=True,
                    password=make_password('password123')
                )
            
            logger.info("✅ Données essentielles créées avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des données: {e}")