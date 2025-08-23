from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien
from contrats.models import Contrat
from contrats.services import ProprieteValidationService
from django.core.exceptions import ValidationError

User = get_user_model()


class TestIntegriteProprietes(TestCase):
    """Tests pour valider l'intégrité des propriétés et des contrats."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Créer un type de bien
        self.type_bien = TypeBien.objects.create(
            nom='Appartement',
            description='Appartement standard'
        )
        
        # Créer un bailleur
        self.bailleur = Bailleur.objects.create(
            numero_bailleur='BL001',
            code_bailleur='BL001',
            civilite='M',
            nom='Dupont',
            prenom='Jean',
            telephone='0123456789'
        )
        
        # Créer un locataire
        self.locataire = Locataire.objects.create(
            numero_locataire='LOC001',
            code_locataire='LOC001',
            civilite='M',
            nom='Martin',
            prenom='Pierre',
            telephone='0987654321',
            statut='actif'
        )
        
        # Créer une propriété
        self.propriete = Propriete.objects.create(
            numero_propriete='PROP001',
            titre='Appartement T3',
            adresse='123 Rue de la Paix',
            ville='Paris',
            type_bien=self.type_bien,
            surface=75.0,
            nombre_pieces=3,
            nombre_chambres=2,
            nombre_salles_bain=1,
            loyer_actuel=800.00,
            charges_locataire=50.00,
            bailleur=self.bailleur,
            disponible=True,
            cree_par=self.user
        )
    
    def test_creation_contrat_marque_propriete_non_disponible(self):
        """Test que la création d'un contrat marque automatiquement la propriété comme non disponible."""
        # Créer un contrat
        contrat = Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=self.propriete,
            locataire=self.locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=self.user
        )
        
        # Vérifier que la propriété est maintenant non disponible
        self.propriete.refresh_from_db()
        self.assertFalse(self.propriete.disponible)
        
        # Vérifier qu'il y a bien un contrat actif
        contrats_actifs = Contrat.objects.filter(
            propriete=self.propriete,
            est_actif=True,
            est_resilie=False
        )
        self.assertEqual(contrats_actifs.count(), 1)
    
    def test_resiliation_contrat_marque_propriete_disponible(self):
        """Test que la résiliation d'un contrat marque automatiquement la propriété comme disponible."""
        # Créer un contrat actif
        contrat = Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=self.propriete,
            locataire=self.locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=self.user
        )
        
        # Vérifier que la propriété est non disponible
        self.propriete.refresh_from_db()
        self.assertFalse(self.propriete.disponible)
        
        # Résilier le contrat
        contrat.est_actif = False
        contrat.est_resilie = True
        contrat.save()
        
        # Vérifier que la propriété est maintenant disponible
        self.propriete.refresh_from_db()
        self.assertTrue(self.propriete.disponible)
    
    def test_impossible_creation_contrat_propriete_non_disponible(self):
        """Test qu'il est impossible de créer un contrat pour une propriété non disponible."""
        # Marquer la propriété comme non disponible
        self.propriete.disponible = False
        self.propriete.save()
        
        # Essayer de créer un contrat
        with self.assertRaises(ValidationError):
            contrat = Contrat(
                numero_contrat='CTR001',
                propriete=self.propriete,
                locataire=self.locataire,
                date_debut=date.today(),
                date_fin=date.today() + timedelta(days=365),
                date_signature=date.today(),
                loyer_mensuel=800.00,
                charges_mensuelles=50.00,
                est_actif=True,
                cree_par=self.user
            )
            contrat.full_clean()
    
    def test_impossible_creation_contrat_chevauchement_dates(self):
        """Test qu'il est impossible de créer un contrat avec des dates qui chevauchent un contrat existant."""
        # Créer un premier contrat
        contrat1 = Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=self.propriete,
            locataire=self.locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=self.user
        )
        
        # Essayer de créer un second contrat avec des dates qui chevauchent
        with self.assertRaises(ValidationError):
            contrat2 = Contrat(
                numero_contrat='CTR002',
                propriete=self.propriete,
                locataire=self.locataire,
                date_debut=date.today() + timedelta(days=180),  # Chevauchement
                date_fin=date.today() + timedelta(days=545),
                date_signature=date.today(),
                loyer_mensuel=800.00,
                charges_mensuelles=50.00,
                est_actif=True,
                cree_par=self.user
            )
            contrat2.full_clean()
    
    def test_suppression_contrat_marque_propriete_disponible(self):
        """Test que la suppression d'un contrat marque automatiquement la propriété comme disponible."""
        # Créer un contrat actif
        contrat = Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=self.propriete,
            locataire=self.locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=self.user
        )
        
        # Vérifier que la propriété est non disponible
        self.propriete.refresh_from_db()
        self.assertFalse(self.propriete.disponible)
        
        # Supprimer le contrat
        contrat.delete()
        
        # Vérifier que la propriété est maintenant disponible
        self.propriete.refresh_from_db()
        self.assertTrue(self.propriete.disponible)


class TestProprieteValidationService(TestCase):
    """Tests pour le service de validation des propriétés."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Configuration similaire à TestIntegriteProprietes
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.type_bien = TypeBien.objects.create(nom='Appartement')
        self.bailleur = Bailleur.objects.create(
            numero_bailleur='BL001',
            civilite='M',
            nom='Dupont',
            prenom='Jean',
            telephone='0123456789'
        )
        self.locataire = Locataire.objects.create(
            numero_locataire='LOC001',
            civilite='M',
            nom='Martin',
            prenom='Pierre',
            telephone='0987654321',
            statut='actif'
        )
        self.propriete = Propriete.objects.create(
            numero_propriete='PROP001',
            titre='Appartement T3',
            adresse='123 Rue de la Paix',
            ville='Paris',
            type_bien=self.type_bien,
            surface=75.0,
            nombre_pieces=3,
            nombre_chambres=2,
            nombre_salles_bain=1,
            loyer_actuel=800.00,
            charges_locataire=50.00,
            bailleur=self.bailleur,
            disponible=True,
            cree_par=self.user
        )
    
    def test_verifier_disponibilite_propriete_disponible(self):
        """Test de vérification d'une propriété disponible."""
        validation = ProprieteValidationService.verifier_disponibilite_propriete(self.propriete)
        
        self.assertTrue(validation['disponible'])
        self.assertEqual(len(validation['messages']), 0)
        self.assertEqual(len(validation['contrats_conflictuels']), 0)
    
    def test_verifier_disponibilite_propriete_avec_contrat_actif(self):
        """Test de vérification d'une propriété avec un contrat actif."""
        # Créer un contrat actif
        Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=self.propriete,
            locataire=self.locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=self.user
        )
        
        validation = ProprieteValidationService.verifier_disponibilite_propriete(self.propriete)
        
        self.assertFalse(validation['disponible'])
        self.assertGreater(len(validation['messages']), 0)
        self.assertEqual(len(validation['contrats_conflictuels']), 1)
    
    def test_synchroniser_disponibilite_propriete(self):
        """Test de synchronisation de la disponibilité d'une propriété."""
        # Créer un contrat actif
        Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=self.propriete,
            locataire=self.locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=self.user
        )
        
        # Marquer manuellement la propriété comme disponible (incohérence)
        self.propriete.disponible = True
        self.propriete.save()
        
        # Synchroniser
        modifiee = ProprieteValidationService.synchroniser_disponibilite_propriete(self.propriete)
        
        self.assertTrue(modifiee)
        self.propriete.refresh_from_db()
        self.assertFalse(self.propriete.disponible)


class TestIntegriteTransactionnelle(TransactionTestCase):
    """Tests transactionnels pour valider l'intégrité en cas de concurrence."""
    
    def test_creation_concurrente_contrats_meme_propriete(self):
        """Test qu'il est impossible de créer deux contrats actifs pour la même propriété."""
        # Configuration de base
        user = User.objects.create_user(username='testuser', password='testpass123')
        type_bien = TypeBien.objects.create(nom='Appartement')
        bailleur = Bailleur.objects.create(
            numero_bailleur='BL001',
            civilite='M',
            nom='Dupont',
            prenom='Jean',
            telephone='0123456789'
        )
        locataire = Locataire.objects.create(
            numero_locataire='LOC001',
            civilite='M',
            nom='Martin',
            prenom='Pierre',
            telephone='0987654321',
            statut='actif'
        )
        propriete = Propriete.objects.create(
            numero_propriete='PROP001',
            titre='Appartement T3',
            adresse='123 Rue de la Paix',
            ville='Paris',
            type_bien=type_bien,
            surface=75.0,
            nombre_pieces=3,
            nombre_chambres=2,
            nombre_salles_bain=1,
            loyer_actuel=800.00,
            charges_locataire=50.00,
            bailleur=bailleur,
            disponible=True,
            cree_par=user
        )
        
        # Créer le premier contrat
        contrat1 = Contrat.objects.create(
            numero_contrat='CTR001',
            propriete=propriete,
            locataire=locataire,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=365),
            date_signature=date.today(),
            loyer_mensuel=800.00,
            charges_mensuelles=50.00,
            est_actif=True,
            cree_par=user
        )
        
        # Vérifier que la propriété est maintenant non disponible
        propriete.refresh_from_db()
        self.assertFalse(propriete.disponible)
        
        # Essayer de créer un second contrat (devrait échouer)
        with self.assertRaises(ValidationError):
            contrat2 = Contrat(
                numero_contrat='CTR002',
                propriete=propriete,
                locataire=locataire,
                date_debut=date.today() + timedelta(days=30),
                date_fin=date.today() + timedelta(days=395),
                date_signature=date.today(),
                loyer_mensuel=800.00,
                charges_mensuelles=50.00,
                est_actif=True,
                cree_par=user
            )
            contrat2.full_clean()
