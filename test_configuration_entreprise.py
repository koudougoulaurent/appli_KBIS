#!/usr/bin/env python
"""
Test simple de la configuration de l'entreprise
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise

def test_configuration():
    """Test de la configuration de l'entreprise"""
    print("🧪 Test de la configuration de l'entreprise")
    print("=" * 50)
    
    try:
        # Récupérer la configuration active
        config = ConfigurationEntreprise.get_configuration_active()
        
        if config:
            print(f"✅ Configuration trouvée : {config.nom_entreprise}")
            print(f"   📍 Adresse : {config.get_adresse_complete()}")
            print(f"   📞 Contact : {config.get_contact_complet()}")
            print(f"   🏛️ Légal : {config.get_informations_legales()}")
            print(f"   🏦 Banque : {config.get_informations_bancaires()}")
            print(f"   🎨 Couleurs : {config.couleur_principale} / {config.couleur_secondaire}")
            
            # Test des méthodes utilitaires
            print(f"\n🔧 Test des méthodes utilitaires :")
            print(f"   - get_adresse_complete(): {config.get_adresse_complete()}")
            print(f"   - get_contact_complet(): {config.get_contact_complet()}")
            print(f"   - get_informations_legales(): {config.get_informations_legales()}")
            print(f"   - get_informations_bancaires(): {config.get_informations_bancaires()}")
            
            return True
        else:
            print("❌ Aucune configuration trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False

if __name__ == '__main__':
    success = test_configuration()
    if success:
        print("\n🎉 Configuration de l'entreprise fonctionnelle !")
    else:
        print("\n💥 Problème avec la configuration de l'entreprise")
