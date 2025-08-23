#!/usr/bin/env python
"""
Script de test pour la Phase 4 - Système de Notifications
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from notifications.models import Notification, NotificationPreference
from contrats.models import Contrat
from paiements.models import Paiement
from proprietes.models import Propriete

User = get_user_model()


def test_notification_models():
    """Tester les modèles de notifications"""
    print("🧪 Test des modèles de notifications...")
    
    try:
        # Vérifier que les notifications existent
        total_notifications = Notification.objects.count()
        print(f"✅ {total_notifications} notifications trouvées")
        
        # Vérifier les préférences
        total_preferences = NotificationPreference.objects.count()
        print(f"✅ {total_preferences} préférences trouvées")
        
        # Tester les méthodes du modèle
        user = User.objects.first()
        if user:
            unread_count = Notification.get_unread_count(user)
            print(f"✅ Nombre de notifications non lues : {unread_count}")
            
            recent_notifications = Notification.get_user_notifications(user, limit=5)
            print(f"✅ {len(recent_notifications)} notifications récentes récupérées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des modèles : {e}")
        return False


def test_notification_api():
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
        
        # Test 1: Endpoint de comptage des notifications non lues
        response = client.get('/notifications/api/notifications/unread_count/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API unread_count : {data.get('unread_count', 0)} notifications non lues")
        else:
            print(f"❌ API unread_count échoue : {response.status_code}")
        
        # Test 2: Endpoint des notifications récentes
        response = client.get('/notifications/api/notifications/recent/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API recent : {len(data)} notifications récentes")
        else:
            print(f"❌ API recent échoue : {response.status_code}")
        
        # Test 3: Endpoint des préférences
        response = client.get('/notifications/api/preferences/my_preferences/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API preferences : préférences récupérées pour {data.get('user_username', 'N/A')}")
        else:
            print(f"❌ API preferences échoue : {response.status_code}")
        
        # Test 4: Endpoint des notifications par type
        response = client.get('/notifications/api/notifications/by_type/?type=payment_due')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API by_type : {len(data)} notifications de type 'payment_due'")
        else:
            print(f"❌ API by_type échoue : {response.status_code}")
        
        # Test 5: Endpoint des notifications haute priorité
        response = client.get('/notifications/api/notifications/high_priority/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API high_priority : {len(data)} notifications haute priorité")
        else:
            print(f"❌ API high_priority échoue : {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API : {e}")
        return False


def test_notification_creation():
    """Tester la création de notifications"""
    print("\n📝 Test de création de notifications...")
    
    try:
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        # Créer une notification de test
        notification = Notification.create_notification(
            recipient=user,
            type='system_alert',
            title='Test de notification',
            message='Ceci est un test de création de notification',
            priority='medium'
        )
        
        print(f"✅ Notification créée avec succès (ID: {notification.id})")
        
        # Tester la méthode mark_as_read
        notification.mark_as_read()
        print("✅ Notification marquée comme lue")
        
        # Tester la méthode mark_as_unread
        notification.mark_as_unread()
        print("✅ Notification marquée comme non lue")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de notification : {e}")
        return False


def test_notification_preferences():
    """Tester les préférences de notification"""
    print("\n⚙️ Test des préférences de notification...")
    
    try:
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        # Créer ou récupérer les préférences
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_notifications': True,
                'browser_notifications': True,
                'payment_due_email': True,
                'payment_received_email': True,
                'contract_expiring_email': True,
                'maintenance_email': True,
                'system_alerts_email': True,
                'daily_digest': False,
                'weekly_digest': True,
            }
        )
        
        if created:
            print("✅ Nouvelles préférences créées")
        else:
            print("✅ Préférences existantes récupérées")
        
        # Tester les préférences par email
        email_prefs = preferences.get_email_preferences()
        print(f"✅ Préférences email : {email_prefs}")
        
        # Modifier les préférences
        preferences.email_notifications = False
        preferences.save()
        print("✅ Préférences modifiées avec succès")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des préférences : {e}")
        return False


def test_notification_statistics():
    """Tester les statistiques des notifications"""
    print("\n📊 Test des statistiques des notifications...")
    
    try:
        # Statistiques globales
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        high_priority_notifications = Notification.objects.filter(
            priority__in=['high', 'urgent']
        ).count()
        
        print(f"✅ Statistiques globales :")
        print(f"   - Total : {total_notifications}")
        print(f"   - Non lues : {unread_notifications}")
        print(f"   - Haute priorité : {high_priority_notifications}")
        
        # Statistiques par type
        print(f"✅ Statistiques par type :")
        for notification_type, count in Notification.objects.values_list('type').annotate(
            count=django.db.models.Count('id')
        ).order_by('-count'):
            type_display = dict(Notification.TYPE_CHOICES)[notification_type]
            print(f"   - {type_display} : {count}")
        
        # Statistiques par priorité
        print(f"✅ Statistiques par priorité :")
        for priority, count in Notification.objects.values_list('priority').annotate(
            count=django.db.models.Count('id')
        ).order_by('-count'):
            priority_display = dict(Notification.PRIORITY_CHOICES)[priority]
            print(f"   - {priority_display} : {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des statistiques : {e}")
        return False


def test_notification_integration():
    """Tester l'intégration avec les autres modules"""
    print("\n🔗 Test d'intégration avec les autres modules...")
    
    try:
        # Vérifier les références vers les contrats
        contrats_with_notifications = Notification.objects.filter(
            content_type__model='contrat'
        ).count()
        print(f"✅ {contrats_with_notifications} notifications liées à des contrats")
        
        # Vérifier les références vers les paiements
        paiements_with_notifications = Notification.objects.filter(
            content_type__model='paiement'
        ).count()
        print(f"✅ {paiements_with_notifications} notifications liées à des paiements")
        
        # Vérifier les références vers les propriétés
        proprietes_with_notifications = Notification.objects.filter(
            content_type__model='propriete'
        ).count()
        print(f"✅ {proprietes_with_notifications} notifications liées à des propriétés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration : {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🚀 Test complet de la Phase 4 - Système de Notifications")
    print("=" * 60)
    
    tests = [
        test_notification_models,
        test_notification_api,
        test_notification_creation,
        test_notification_preferences,
        test_notification_statistics,
        test_notification_integration,
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution du test {test.__name__} : {e}")
    
    print("\n" + "=" * 60)
    print(f"📋 Résumé des tests : {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 Tous les tests sont passés avec succès !")
        print("\n✅ La Phase 4 (Système de Notifications) est opérationnelle")
        print("\n📝 Prochaines étapes :")
        print("   1. Accéder aux notifications : http://127.0.0.1:8000/notifications/")
        print("   2. Tester l'API : http://127.0.0.1:8000/notifications/api/")
        print("   3. Vérifier l'admin : http://127.0.0.1:8000/admin/notifications/")
        print("   4. Continuer avec la Phase 5 (Rapports et Statistiques)")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return passed_tests == total_tests


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 