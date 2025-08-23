#!/usr/bin/env python
"""
Test de l'accessibilité de la page de configuration de l'entreprise
"""

import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

User = get_user_model()

def test_url_configuration():
    """Test de l'URL de configuration"""
    print("🧪 Test de l'URL de configuration de l'entreprise")
    print("=" * 50)
    
    client = Client()
    
    # Créer un utilisateur admin pour le test
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Utilisateur admin créé : {user.username}")
        
        # Créer un groupe de travail pour l'utilisateur
        from utilisateurs.models import GroupeTravail
        groupe, created_groupe = GroupeTravail.objects.get_or_create(
            nom='Groupe Test',
            defaults={'description': 'Groupe de test pour les tests'}
        )
        user.groupe_travail = groupe
        user.save()
        print(f"✅ Groupe de travail créé : {groupe.nom}")
    else:
        print(f"✅ Utilisateur admin existant : {user.username}")
    
    # Se connecter
    client.force_login(user)
    
    # Test de l'URL de configuration
    try:
        from django.urls import reverse
        response = client.get(reverse('core:configuration_entreprise'))
        
        if response.status_code == 200:
            print("✅ Page de configuration accessible")
            
            # Vérifier le contenu
            content = response.content.decode()
            
            if 'Configuration de l\'Entreprise' in content:
                print("✅ Titre de la page présent")
            else:
                print("❌ Titre de la page manquant")
            
            if 'form' in content:
                print("✅ Formulaire présent")
            else:
                print("❌ Formulaire manquant")
            
            if 'MA SOCIÉTÉ IMMOBILIÈRE' in content:
                print("✅ Informations de l'entreprise présentes")
            else:
                print("❌ Informations de l'entreprise manquantes")
                
        else:
            print(f"❌ Erreur page configuration : {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur accès configuration : {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_url_configuration() 