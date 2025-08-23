#!/usr/bin/env python
"""
Test script to verify URL fixes and ensure no NoReverseMatch errors
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

User = get_user_model()

class URLFixTests(TestCase):
    """Test that all URL references are working correctly"""
    
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
    
    def test_dashboard_urls(self):
        """Test that dashboard URLs resolve correctly"""
        # Test main dashboard
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Test intelligent search
        response = self.client.get(reverse('core:intelligent_search'))
        self.assertEqual(response.status_code, 200)
        
        # Test profile
        response = self.client.get(reverse('core:profile'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_privilege_urls(self):
        """Test that privilege dashboard URLs work"""
        # Test privilege dashboard
        response = self.client.get('/utilisateurs/dashboard/PRIVILEGE/')
        self.assertEqual(response.status_code, 200)
        
        # Test using reverse URL
        url = reverse('utilisateurs:dashboard_groupe', kwargs={'groupe_nom': 'PRIVILEGE'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_template_rendering(self):
        """Test that templates render without URL errors"""
        # Test dashboard template
        try:
            context = {
                'user': self.user,
                'total_users': 10,
                'active_users': 8,
                'total_proprietes': 25,
                'proprietes_disponibles': 5,
                'total_bailleurs': 15,
                'total_locataires': 20,
                'top_proprietes': [],
                'proprietes_par_ville': []
            }
            rendered = render_to_string('core/dashboard.html', context)
            self.assertIn('Recherche Intelligente', rendered)
            self.assertNotIn('api_interface', rendered)
        except Exception as e:
            self.fail(f"Dashboard template failed to render: {e}")
        
        # Test settings template
        try:
            context = {'user': self.user}
            rendered = render_to_string('core/settings.html', context)
            self.assertIn('Recherche Intelligente', rendered)
            self.assertNotIn('api_interface', rendered)
        except Exception as e:
            self.fail(f"Settings template failed to render: {e}")
    
    def test_all_core_urls(self):
        """Test all core URLs are accessible"""
        core_urls = [
            'core:home',
            'core:dashboard',
            'core:profile',
            'core:intelligent_search',
            'core:advanced_search_api',
            'core:search_suggestions_api',
            'core:search_analytics_api',
            'core:advanced_proprietes_search',
            'core:advanced_contrats_search',
            'core:advanced_paiements_search',
            'core:advanced_utilisateurs_search',
        ]
        
        for url_name in core_urls:
            try:
                url = reverse(url_name)
                print(f"✓ {url_name} -> {url}")
            except Exception as e:
                self.fail(f"URL {url_name} failed to resolve: {e}")

def main():
    """Run the tests"""
    print("Testing URL fixes...")
    
    # Run the tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    failures = test_runner.run_tests(['test_urls_fixes'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All URL tests passed!")

if __name__ == '__main__':
    main() 