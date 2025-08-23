#!/usr/bin/env python
"""
Test rapide de la configuration de l'entreprise
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise

def test_configuration():
    """Test rapide de la configuration"""
    print("🧪 Test rapide de la configuration de l'entreprise")
    print("=" * 50)
    
    # Récupérer ou créer la configuration
    config = ConfigurationEntreprise.get_configuration_active()
    
    if config:
        print(f"✅ Configuration trouvée : {config.nom_entreprise}")
        print(f"   📍 Adresse : {config.get_adresse_complete()}")
        print(f"   📞 Contact : {config.get_contact_complet()}")
        print(f"   🎨 Couleurs : {config.couleur_principale} / {config.couleur_secondaire}")
        
        # Modifier quelques informations pour le test
        config.nom_entreprise = "MA SOCIÉTÉ IMMOBILIÈRE"
        config.slogan = "Votre partenaire de confiance"
        config.adresse = "123 Avenue des Affaires"
        config.ville = "Paris"
        config.code_postal = "75001"
        config.telephone = "01 42 34 56 78"
        config.email = "contact@masociete.fr"
        config.siret = "123 456 789 00012"
        config.numero_licence = "123456789"
        config.couleur_principale = "#1a5f7a"
        config.couleur_secondaire = "#ff6b35"
        config.save()
        
        print(f"\n✅ Configuration mise à jour :")
        print(f"   🏢 Nom : {config.nom_entreprise}")
        print(f"   📝 Slogan : {config.slogan}")
        print(f"   📍 Adresse : {config.get_adresse_complete()}")
        print(f"   📞 Contact : {config.get_contact_complet()}")
        print(f"   🎨 Couleurs : {config.couleur_principale} / {config.couleur_secondaire}")
        
        return True
    else:
        print("❌ Aucune configuration trouvée")
        return False

if __name__ == '__main__':
    test_configuration() 