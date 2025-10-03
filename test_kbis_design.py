#!/usr/bin/env python
"""
Script de test pour vérifier le design KBIS
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.models import ConfigurationEntreprise, GroupeTravail
from django.urls import reverse

class TestKBISDesign(TestCase):
    """Tests pour le design KBIS"""
    
    def setUp(self):
        """Configuration des tests"""
        # Créer un groupe de travail
        self.groupe = GroupeTravail.objects.create(
            nom='PRIVILEGE',
            description='Groupe privilégié'
        )
        
        # Créer un utilisateur
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            groupe_travail=self.groupe
        )
        
        # Créer une configuration d'entreprise
        self.config = ConfigurationEntreprise.objects.create(
            nom_entreprise='KBIS',
            adresse='BP 440 Ouaga pissy 10050',
            ville='Ouagadougou',
            pays='Burkina Faso',
            telephone='+226 79 18 32 32',
            email='kbissarl2022@gmail.com',
            siret='123 456 789 00012',
            numero_licence='123456789',
            actif=True
        )
        
        self.client = Client()
    
    def test_demo_page_access(self):
        """Test l'accès à la page de démonstration"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:demo_kbis_design'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Démonstration Design KBIS')
        self.assertContains(response, 'KBIS')
        self.assertContains(response, 'Immobilier & Construction')
    
    def test_header_template(self):
        """Test le template d'en-tête"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:demo_kbis_design'))
        
        # Vérifier la présence des éléments de l'en-tête
        self.assertContains(response, 'kbis-header')
        self.assertContains(response, 'kbis-company-name')
        self.assertContains(response, 'kbis-tagline')
        self.assertContains(response, 'kbis-services')
    
    def test_footer_template(self):
        """Test le template de pied de page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:demo_kbis_design'))
        
        # Vérifier la présence des éléments du pied de page
        self.assertContains(response, 'kbis-footer')
        self.assertContains(response, 'kbis-footer-content')
        self.assertContains(response, 'kbis-footer-address')
        self.assertContains(response, 'kbis-footer-phones')
    
    def test_pdf_templates(self):
        """Test les templates PDF"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:demo_kbis_design'))
        
        # Vérifier la présence des éléments PDF
        self.assertContains(response, 'kbis-pdf-document')
        self.assertContains(response, 'kbis-pdf-header')
        self.assertContains(response, 'kbis-pdf-footer')
        self.assertContains(response, 'CONTRAT DE BAIL D\'HABITATION')
    
    def test_css_files_loaded(self):
        """Test que les fichiers CSS sont chargés"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:demo_kbis_design'))
        
        # Vérifier la présence des liens CSS
        self.assertContains(response, 'kbis_header_footer.css')
        self.assertContains(response, 'kbis_pdf_styles.css')
    
    def test_entreprise_config_in_context(self):
        """Test que la configuration d'entreprise est dans le contexte"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('core:demo_kbis_design'))
        
        # Vérifier que les informations de l'entreprise sont présentes
        self.assertContains(response, self.config.nom_entreprise)
        self.assertContains(response, self.config.telephone)
        self.assertContains(response, self.config.email)
        self.assertContains(response, self.config.siret)

def run_tests():
    """Fonction pour exécuter les tests"""
    print("🧪 Test du design KBIS")
    print("=" * 50)
    
    try:
        # Exécuter les tests
        from django.test.utils import get_runner
        from django.conf import settings
        
        TestRunner = get_runner(settings)
        test_runner = TestRunner()
        failures = test_runner.run_tests(["__main__"])
        
        if failures:
            print(f"❌ {failures} test(s) ont échoué")
            return False
        else:
            print("✅ Tous les tests sont passés avec succès!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests: {e}")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
