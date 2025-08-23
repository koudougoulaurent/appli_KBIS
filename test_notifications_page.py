#!/usr/bin/env python
"""
Script de test pour vérifier l'accessibilité de la page des notifications
"""

import os
import sys
import django
import requests
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

User = get_user_model()


def test_notifications_page():
    """Tester l'accessibilité de la page des notifications"""
    print("🧪 Test de la page des notifications...")
    
    try:
        client = Client()
        
        # Se connecter avec un utilisateur
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé pour les tests")
            return False
        
        client.force_login(user)
        
        # Test 1: Page principale des notifications
        print("📄 Test de la page principale des notifications...")
        response = client.get('/notifications/')
        if response.status_code == 200:
            print("✅ Page principale accessible (200)")
            print(f"   - Contenu : {len(response.content)} caractères")
            
            # Vérifier la présence d'éléments clés
            content = response.content.decode('utf-8')
            if 'Notifications' in content:
                print("✅ Titre 'Notifications' trouvé")
            if 'notification-card' in content:
                print("✅ Classes CSS des notifications trouvées")
            if 'Filtrer' in content:
                print("✅ Bouton de filtrage trouvé")
        else:
            print(f"❌ Page principale inaccessible : {response.status_code}")
            return False
        
        # Test 2: Page des préférences
        print("\n⚙️ Test de la page des préférences...")
        response = client.get('/notifications/preferences/')
        if response.status_code == 200:
            print("✅ Page des préférences accessible (200)")
            print(f"   - Contenu : {len(response.content)} caractères")
            
            content = response.content.decode('utf-8')
            if 'Préférences de Notification' in content:
                print("✅ Titre des préférences trouvé")
            if 'form-check' in content:
                print("✅ Formulaire de préférences trouvé")
        else:
            print(f"❌ Page des préférences inaccessible : {response.status_code}")
            return False
        
        # Test 3: Détail d'une notification
        print("\n📋 Test du détail d'une notification...")
        from notifications.models import Notification
        notification = Notification.objects.filter(recipient=user).first()
        if notification:
            response = client.get(f'/notifications/{notification.id}/')
            if response.status_code == 200:
                print("✅ Page de détail accessible (200)")
                print(f"   - Notification : {notification.title}")
                
                content = response.content.decode('utf-8')
                if notification.title in content:
                    print("✅ Titre de la notification trouvé")
                if 'Retour' in content:
                    print("✅ Bouton de retour trouvé")
            else:
                print(f"❌ Page de détail inaccessible : {response.status_code}")
        else:
            print("⚠️ Aucune notification trouvée pour tester le détail")
        
        # Test 4: Actions AJAX
        print("\n🔄 Test des actions AJAX...")
        
        # Marquer comme lu
        if notification:
            response = client.post(f'/notifications/{notification.id}/mark-read/')
            if response.status_code == 200:
                print("✅ Action 'marquer comme lu' fonctionnelle")
            else:
                print(f"❌ Action 'marquer comme lu' échoue : {response.status_code}")
        
        # Comptage des notifications
        response = client.get('/notifications/notification-count/')
        if response.status_code == 200:
            print("✅ Comptage des notifications fonctionnel")
        else:
            print(f"❌ Comptage des notifications échoue : {response.status_code}")
        
        # Marquer toutes comme lues
        response = client.post('/notifications/mark-all-as-read/')
        if response.status_code == 200:
            print("✅ Action 'marquer toutes comme lues' fonctionnelle")
        else:
            print(f"❌ Action 'marquer toutes comme lues' échoue : {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de la page : {e}")
        return False


def test_notifications_api():
    """Tester l'API des notifications"""
    print("\n🌐 Test de l'API des notifications...")
    
    try:
        client = Client()
        
        # Se connecter avec un utilisateur
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé pour les tests")
            return False
        
        client.force_login(user)
        
        # Test des endpoints API
        endpoints = [
            ('/notifications/api/notifications/', 'Liste des notifications'),
            ('/notifications/api/notifications/unread_count/', 'Comptage non lues'),
            ('/notifications/api/notifications/recent/', 'Notifications récentes'),
            ('/notifications/api/preferences/my_preferences/', 'Mes préférences'),
        ]
        
        for endpoint, description in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                print(f"✅ {description} : OK")
            else:
                print(f"❌ {description} : {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API : {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🚀 Test de l'accessibilité des notifications")
    print("=" * 50)
    
    tests = [
        test_notifications_page,
        test_notifications_api,
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution du test {test.__name__} : {e}")
    
    print("\n" + "=" * 50)
    print(f"📋 Résumé des tests : {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 Tous les tests sont passés avec succès !")
        print("\n✅ La page des notifications est maintenant accessible")
        print("\n📝 URLs disponibles :")
        print("   - Page principale : http://127.0.0.1:8000/notifications/")
        print("   - Préférences : http://127.0.0.1:8000/notifications/preferences/")
        print("   - API : http://127.0.0.1:8000/notifications/api/")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return passed_tests == total_tests


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 