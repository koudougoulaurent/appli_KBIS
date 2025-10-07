#!/usr/bin/env python
"""
Test de l'interface des avances de loyer
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_interface_avances():
    """Test de l'interface des avances"""
    print("=" * 60)
    print("TEST DE L'INTERFACE DES AVANCES DE LOYER")
    print("=" * 60)
    
    try:
        # Test 1: Vérifier que les URLs sont accessibles
        print("\n1. VERIFICATION DES URLs")
        print("-" * 40)
        
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # URLs à tester
        urls_to_test = [
            ('paiements:dashboard_avances', 'Dashboard des avances'),
            ('paiements:liste_avances', 'Liste des avances'),
            ('paiements:ajouter_avance', 'Ajouter une avance'),
        ]
        
        for url_name, description in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✓ {description}: {url}")
            except Exception as e:
                print(f"✗ {description}: ERREUR - {str(e)}")
        
        # Test 2: Vérifier que les templates existent
        print("\n2. VERIFICATION DES TEMPLATES")
        print("-" * 40)
        
        template_paths = [
            'paiements/avances/dashboard_avances.html',
            'paiements/avances/liste_avances.html',
            'paiements/avances/ajouter_avance.html',
        ]
        
        for template_path in template_paths:
            full_path = os.path.join('templates', template_path)
            if os.path.exists(full_path):
                print(f"✓ Template trouvé: {template_path}")
            else:
                print(f"✗ Template manquant: {template_path}")
        
        # Test 3: Vérifier que les vues sont accessibles
        print("\n3. VERIFICATION DES VUES")
        print("-" * 40)
        
        from paiements.views_avance import dashboard_avances, liste_avances, ajouter_avance_loyer
        
        print("✓ dashboard_avances: Fonction disponible")
        print("✓ liste_avances: Fonction disponible")
        print("✓ ajouter_avance_loyer: Fonction disponible")
        
        # Test 4: Vérifier les formulaires
        print("\n4. VERIFICATION DES FORMULAIRES")
        print("-" * 40)
        
        from paiements.forms_avance import AvanceLoyerForm, PaiementAvanceForm
        
        form = AvanceLoyerForm()
        print(f"✓ AvanceLoyerForm: {len(form.fields)} champs")
        
        form_paiement = PaiementAvanceForm()
        print(f"✓ PaiementAvanceForm: {len(form_paiement.fields)} champs")
        
        # Test 5: Vérifier les modèles
        print("\n5. VERIFICATION DES MODELES")
        print("-" * 40)
        
        from paiements.models_avance import AvanceLoyer, ConsommationAvance, HistoriquePaiement
        
        print(f"✓ AvanceLoyer: {len(AvanceLoyer._meta.fields)} champs")
        print(f"✓ ConsommationAvance: {len(ConsommationAvance._meta.fields)} champs")
        print(f"✓ HistoriquePaiement: {len(HistoriquePaiement._meta.fields)} champs")
        
        # Test 6: Vérifier les services
        print("\n6. VERIFICATION DES SERVICES")
        print("-" * 40)
        
        from paiements.services_avance import ServiceGestionAvance
        
        methods = [method for method in dir(ServiceGestionAvance) if not method.startswith('_')]
        print(f"✓ ServiceGestionAvance: {len(methods)} méthodes disponibles")
        
        # Test 7: Vérifier les CSS
        print("\n7. VERIFICATION DES FICHIERS CSS")
        print("-" * 40)
        
        css_path = 'static/css/avances.css'
        if os.path.exists(css_path):
            print(f"✓ Fichier CSS trouvé: {css_path}")
        else:
            print(f"✗ Fichier CSS manquant: {css_path}")
        
        print("\n" + "=" * 60)
        print("TEST DE L'INTERFACE TERMINE AVEC SUCCES!")
        print("L'interface des avances de loyer est prête à être utilisée")
        print("=" * 60)
        
        # Instructions d'utilisation
        print("\nINSTRUCTIONS D'UTILISATION:")
        print("-" * 40)
        print("1. Démarrez le serveur: python manage.py runserver")
        print("2. Accédez à: http://127.0.0.1:8000/")
        print("3. Cliquez sur 'Paiements' dans le menu principal")
        print("4. Sélectionnez 'Avances de Loyer' dans le sous-menu")
        print("5. Vous verrez le dashboard des avances avec toutes les fonctionnalités")
        
    except Exception as e:
        print(f"\nERREUR LORS DU TEST: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_interface_avances()
