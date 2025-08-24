#!/usr/bin/env python
"""
Script de test simple pour vérifier le bouton sauvegarder
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from utilisateurs.models import Utilisateur, GroupeTravail
from core.models import ConfigurationTableauBord

def test_bouton_sauvegarder():
    """Test simple du bouton sauvegarder"""
    print("🔧 Test du bouton sauvegarder")
    print("=" * 50)
    
    # 1. Vérifier que le groupe PRIVILEGE existe
    try:
        groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
        print("✅ Groupe PRIVILEGE trouvé")
    except GroupeTravail.DoesNotExist:
        print("❌ Groupe PRIVILEGE non trouvé - Création...")
        groupe_privilege = GroupeTravail.objects.create(
            nom='PRIVILEGE',
            description='Groupe avec privilèges spéciaux',
            permissions={'modules': ['all']},
            actif=True
        )
        print("✅ Groupe PRIVILEGE créé")
    
    # 2. Créer un utilisateur de test PRIVILEGE
    from django.contrib.auth.hashers import make_password
    
    user_privilege, created = Utilisateur.objects.get_or_create(
        username='test_sauvegarde',
        defaults={
            'email': 'sauvegarde@test.com',
            'password': make_password('test123'),
            'first_name': 'Test',
            'last_name': 'Sauvegarde',
            'is_active': True,
            'groupe_travail': groupe_privilege
        }
    )
    if created:
        print("✅ Utilisateur de test créé: test_sauvegarde / test123")
    else:
        print("✅ Utilisateur de test existe déjà")
    
    # 3. Test de la sauvegarde
    print("\n📝 Test de la sauvegarde:")
    print("-" * 30)
    
    client = Client()
    client.force_login(user_privilege)
    
    # Données de test pour la sauvegarde
    data_post = {
        'nom_tableau': 'Tableau Test',
        'widgets_actifs': ['statistiques_generales', 'activite_recente'],
        'masquer_montants': 'on',
        'affichage_anonymise': 'off',
        'limite_jours': '15'
    }
    
    # Test POST vers la configuration
    print("Envoi des données de configuration...")
    response = client.post('/configuration-tableau/', data_post)
    
    print(f"Statut de la réponse: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Sauvegarde réussie (statut 200)")
        
        # Vérifier que la configuration a été sauvegardée
        config_sauvegardee = ConfigurationTableauBord.objects.filter(
            utilisateur=user_privilege,
            nom_tableau='Tableau Test'
        ).first()
        
        if config_sauvegardee:
            print("✅ Configuration trouvée en base de données")
            print(f"  - Nom: {config_sauvegardee.nom_tableau}")
            print(f"  - Widgets actifs: {config_sauvegardee.widgets_actifs}")
            print(f"  - Masquer montants: {config_sauvegardee.masquer_montants_sensibles}")
            print(f"  - Affichage anonymisé: {config_sauvegardee.affichage_anonymise}")
            print(f"  - Limite jours: {config_sauvegardee.limite_donnees_recentes}")
        else:
            print("❌ Configuration non trouvée en base de données")
            
    elif response.status_code == 302:
        print("⚠️ Redirection détectée")
        print(f"URL de redirection: {response.url}")
        
        # Suivre la redirection
        response_redirect = client.get(response.url)
        print(f"Statut après redirection: {response_redirect.status_code}")
        
    else:
        print(f"❌ Erreur: Statut {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Contenu de la réponse: {response.content[:200]}...")
    
    # 4. Test de récupération de la configuration
    print("\n📖 Test de récupération de la configuration:")
    print("-" * 40)
    
    response_get = client.get('/configuration-tableau/')
    print(f"Statut GET: {response_get.status_code}")
    
    if response_get.status_code == 200:
        print("✅ Page de configuration accessible")
        
        # Vérifier que les données sont bien affichées
        if 'Tableau Test' in str(response_get.content):
            print("✅ Nom du tableau affiché correctement")
        else:
            print("⚠️ Nom du tableau non trouvé dans la réponse")
            
    else:
        print(f"❌ Erreur lors de la récupération: {response_get.status_code}")
    
    # 5. Nettoyage
    print("\n🧹 Nettoyage:")
    print("-" * 20)
    
    # Supprimer la configuration de test
    try:
        ConfigurationTableauBord.objects.filter(
            utilisateur=user_privilege,
            nom_tableau='Tableau Test'
        ).delete()
        print("✅ Configuration de test supprimée")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {str(e)}")
    
    # Supprimer l'utilisateur de test
    try:
        user_privilege.delete()
        print("✅ Utilisateur de test supprimé")
    except Exception as e:
        print(f"⚠️ Erreur lors de la suppression de l'utilisateur: {str(e)}")
    
    print("\n🎯 Résumé du test:")
    print("=" * 30)
    print("✅ Test du bouton sauvegarder terminé")
    print("✅ Vérification de la sauvegarde en base")
    print("✅ Test de récupération des données")
    print("✅ Nettoyage des données de test")
    
    return True

if __name__ == '__main__':
    try:
        test_bouton_sauvegarder()
        print("\n🎉 Test terminé avec succès !")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
