#!/usr/bin/env python
"""
Test script to verify search functionality fixes
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

User = get_user_model()

class SearchFixTests(TestCase):
    """Test that search functionality works correctly"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a test group
        from utilisateurs.models import GroupeTravail
        self.group = GroupeTravail.objects.create(
            nom='PRIVILEGE',
            description='Groupe de test pour les privilèges',
            permissions={'modules': ['proprietes', 'contrats', 'paiements', 'utilisateurs']}
        )
        
        # Create a test user with the group
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            groupe_travail=self.group
        )
        
        # Login the user
        self.client.login(username='testuser', password='testpass123')
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create test data for search"""
        from proprietes.models import Propriete, Bailleur, TypeBien
        
        # Create type bien
        self.type_bien = TypeBien.objects.create(
            nom='Appartement',
            description='Appartement standard'
        )
        
        # Create bailleur
        self.bailleur = Bailleur.objects.create(
            nom='Dupont',
            prenom='Jean',
            email='jean.dupont@example.com',
            telephone='0123456789',
            adresse='123 Rue de la Paix, Paris'
        )
        
        # Create propriété
        self.propriete = Propriete.objects.create(
            titre='Appartement T3 à Paris',
            adresse='456 Avenue des Champs, Paris',
            code_postal='75008',
            ville='Paris',
            type_bien=self.type_bien,
            surface=75.5,
            nombre_pieces=3,
            nombre_chambres=2,
            loyer_actuel=1200.00,
            bailleur=self.bailleur,
            cree_par=self.user
        )
    
    def test_search_page_loads(self):
        """Test that search page loads without errors"""
        response = self.client.get(reverse('core:intelligent_search'))
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_query(self):
        """Test search with a query"""
        response = self.client.get(reverse('core:intelligent_search'), {
            'q': 'Paris'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the search query
        self.assertIn('Paris', response.content.decode())
    
    def test_search_with_empty_query(self):
        """Test search with empty query"""
        response = self.client.get(reverse('core:intelligent_search'), {
            'q': ''
        })
        self.assertEqual(response.status_code, 200)
    
    def test_search_api_endpoints(self):
        """Test search API endpoints"""
        # Test suggestions API
        response = self.client.get(reverse('core:search_suggestions_api'), {
            'q': 'Paris'
        })
        self.assertEqual(response.status_code, 200)
        
        # Test analytics API
        response = self.client.get(reverse('core:search_analytics_api'), {
            'q': 'Paris'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_advanced_search_views(self):
        """Test advanced search views"""
        # Test propriétés search
        response = self.client.get(reverse('core:advanced_proprietes_search'))
        self.assertEqual(response.status_code, 200)
        
        # Test contrats search
        response = self.client.get(reverse('core:advanced_contrats_search'))
        self.assertEqual(response.status_code, 200)
        
        # Test paiements search
        response = self.client.get(reverse('core:advanced_paiements_search'))
        self.assertEqual(response.status_code, 200)
        
        # Test utilisateurs search
        response = self.client.get(reverse('core:advanced_utilisateurs_search'))
        self.assertEqual(response.status_code, 200)

def main():
    """Run the tests"""
    print("Testing search functionality fixes...")
    
    # Run the tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    failures = test_runner.run_tests(['test_search_fix'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All search tests passed!")

if __name__ == '__main__':
    main() 