#!/usr/bin/env python
"""
Script de test rapide pour vérifier la connexion et la configuration
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import authenticate
from core.models import ConfigurationEntreprise
from utilisateurs.models import Utilisateur, GroupeTravail

def test_connexion():
    """Test de connexion utilisateur"""
    print("🔍 Test de connexion...")
    
    # Test avec l'utilisateur admin1
    user = authenticate(username='admin1', password='test123')
    if user:
        print(f"✅ Connexion réussie pour {user.username}")
        print(f"   - Groupe: {user.groupe_travail}")
        print(f"   - Permissions: {user.is_staff}")
        return user
    else:
        print("❌ Échec de la connexion")
        return None

def test_configuration_entreprise():
    """Test de la configuration de l'entreprise"""
    print("\n🏢 Test de la configuration de l'entreprise...")
    
    # Vérifier s'il existe une configuration
    config = ConfigurationEntreprise.objects.filter(actif=True).first()
    if config:
        print(f"✅ Configuration trouvée: {config.nom_entreprise}")
        print(f"   - Slogan: {config.slogan}")
        print(f"   - Adresse: {config.get_adresse_complete()}")
        print(f"   - Contact: {config.get_contact_complet()}")
        return config
    else:
        print("⚠️  Aucune configuration d'entreprise active")
        return None

def test_groupe_administration():
    """Test du groupe d'administration"""
    print("\n👥 Test du groupe d'administration...")
    
    groupe = GroupeTravail.objects.filter(nom='ADMINISTRATION').first()
    if groupe:
        print(f"✅ Groupe ADMINISTRATION trouvé")
        print(f"   - Nombre d'utilisateurs: {groupe.utilisateurs.count()}")
        return groupe
    else:
        print("❌ Groupe ADMINISTRATION non trouvé")
        return None

def main():
    """Fonction principale"""
    print("🚀 Test rapide du système de gestion immobilière")
    print("=" * 50)
    
    # Tests
    user = test_connexion()
    config = test_configuration_entreprise()
    groupe = test_groupe_administration()
    
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    print(f"   - Connexion: {'✅' if user else '❌'}")
    print(f"   - Configuration: {'✅' if config else '⚠️'}")
    print(f"   - Groupe Admin: {'✅' if groupe else '❌'}")
    
    if user and groupe:
        print("\n🎉 Le système semble fonctionnel !")
        print("   Vous pouvez maintenant vous connecter à http://127.0.0.1:8000")
    else:
        print("\n⚠️  Certains éléments nécessitent une attention")

if __name__ == '__main__':
    main() 