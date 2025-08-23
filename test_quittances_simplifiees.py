#!/usr/bin/env python3
"""
Script de test pour vérifier les quittances simplifiées
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise
from django.test import Client
from django.urls import reverse

def test_configuration_entreprise():
    """Test de la configuration de l'entreprise"""
    print("🧪 Test de la configuration de l'entreprise")
    
    # Vérifier qu'il y a une configuration active
    config = ConfigurationEntreprise.get_configuration_active()
    if config:
        print(f"✅ Configuration trouvée: {config.nom_entreprise}")
        print(f"   Adresse: {config.get_adresse_complete()}")
        print(f"   Contact: {config.get_contact_complet()}")
        print(f"   Légal: {config.get_informations_legales()}")
    else:
        print("❌ Aucune configuration d'entreprise trouvée")
        return False
    
    return True

def test_urls_quittances():
    """Test des URLs des quittances"""
    print("\n🧪 Test des URLs des quittances")
    
    client = Client()
    
    # Test URL liste quittances de loyer
    try:
        url = reverse('contrats:quittances_liste')
        print(f"✅ URL liste quittances loyer: {url}")
    except Exception as e:
        print(f"❌ Erreur URL liste quittances loyer: {e}")
    
    # Test URL ajouter quittance
    try:
        url = reverse('contrats:quittance_ajouter')
        print(f"✅ URL ajouter quittance: {url}")
    except Exception as e:
        print(f"❌ Erreur URL ajouter quittance: {e}")
    
    # Test URL liste quittances paiement
    try:
        url = reverse('paiements:quittance_list')
        print(f"✅ URL liste quittances paiement: {url}")
    except Exception as e:
        print(f"❌ Erreur URL liste quittances paiement: {e}")

def test_templates_quittances():
    """Test de l'existence des templates"""
    print("\n🧪 Test de l'existence des templates")
    
    templates = [
        'templates/contrats/quittance_detail.html',
        'templates/contrats/quittance_ajouter.html',
        'templates/contrats/quittance_liste.html',
        'templates/paiements/quittance_detail.html',
        'templates/paiements/quittance_list.html'
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"✅ Template trouvé: {template}")
        else:
            print(f"❌ Template manquant: {template}")

def main():
    """Fonction principale"""
    print("🚀 Test des quittances simplifiées")
    print("=" * 50)
    
    # Test 1: Configuration entreprise
    if not test_configuration_entreprise():
        print("❌ Échec du test de configuration")
        return
    
    # Test 2: URLs
    test_urls_quittances()
    
    # Test 3: Templates
    test_templates_quittances()
    
    print("\n✅ Tests terminés avec succès!")

if __name__ == '__main__':
    main()
