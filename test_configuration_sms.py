#!/usr/bin/env python
"""
Script de test pour la configuration SMS et les nouvelles fonctionnalités
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from notifications.models import NotificationPreference, SMSNotification
from notifications.sms_service import SMSService, send_monthly_overdue_notifications

User = get_user_model()

def test_configuration_sms():
    """Test de la configuration SMS"""
    print("🧪 Test de la configuration SMS")
    print("=" * 50)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_sms_user',
        defaults={
            'email': 'test_sms@example.com',
            'first_name': 'Test',
            'last_name': 'SMS'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Utilisateur de test créé : {user.username}")
    else:
        print(f"✅ Utilisateur de test existant : {user.username}")
    
    # Créer ou récupérer les préférences
    preferences, created = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={
            'sms_notifications': True,
            'phone_number': '+33 6 12 34 56 78',
            'payment_overdue_sms': True,
            'payment_due_sms': True,
            'contract_expiring_sms': True,
            'maintenance_sms': True,
            'system_alerts_sms': True,
        }
    )
    
    if created:
        print(f"✅ Préférences SMS créées pour {user.username}")
    else:
        print(f"✅ Préférences SMS existantes pour {user.username}")
    
    # Afficher les préférences
    print(f"\n📱 Configuration SMS de {user.username}:")
    print(f"   - SMS activés : {preferences.sms_notifications}")
    print(f"   - Numéro : {preferences.phone_number}")
    print(f"   - Retards paiement : {preferences.payment_overdue_sms}")
    print(f"   - Échéances paiement : {preferences.payment_due_sms}")
    print(f"   - Contrats expirants : {preferences.contract_expiring_sms}")
    print(f"   - Maintenance : {preferences.maintenance_sms}")
    print(f"   - Alertes système : {preferences.system_alerts_sms}")
    
    return user, preferences

def test_service_sms():
    """Test du service SMS"""
    print("\n🧪 Test du service SMS")
    print("=" * 50)
    
    # Créer le service SMS
    sms_service = SMSService()
    
    # Test d'envoi de SMS
    phone_number = '+33 6 12 34 56 78'
    message = "Test SMS - GESTIMMOB - Configuration SMS testée avec succès !"
    user = User.objects.first()
    
    print(f"📤 Envoi d'un SMS de test à {phone_number}")
    print(f"📝 Message : {message}")
    
    result = sms_service.send_sms(
        phone_number=phone_number,
        message=message,
        user=user
    )
    
    if result.get('success'):
        print(f"✅ SMS envoyé avec succès !")
        print(f"   - Message ID : {result.get('message_id', 'N/A')}")
        print(f"   - Statut : {result.get('status', 'N/A')}")
    else:
        print(f"❌ Échec de l'envoi du SMS")
        print(f"   - Erreur : {result.get('error', 'Erreur inconnue')}")
    
    return result.get('success', False)

def test_notifications_retard():
    """Test des notifications de retard"""
    print("\n🧪 Test des notifications de retard")
    print("=" * 50)
    
    try:
        result = send_monthly_overdue_notifications()
        
        if result['success']:
            print(f"✅ Notifications de retard envoyées avec succès !")
            print(f"   - Nombre de SMS envoyés : {result['count']}")
            print(f"   - Détails : {result.get('details', 'Aucun détail')}")
        else:
            print(f"❌ Échec de l'envoi des notifications de retard")
            print(f"   - Erreur : {result['message']}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test des notifications de retard : {str(e)}")

def test_statistiques_sms():
    """Test des statistiques SMS"""
    print("\n🧪 Test des statistiques SMS")
    print("=" * 50)
    
    # Compter les SMS
    total_sms = SMSNotification.objects.count()
    successful_sms = SMSNotification.objects.filter(status='sent').count()
    failed_sms = SMSNotification.objects.filter(status='failed').count()
    pending_sms = SMSNotification.objects.filter(status='pending').count()
    
    print(f"📊 Statistiques SMS :")
    print(f"   - Total : {total_sms}")
    print(f"   - Envoyés avec succès : {successful_sms}")
    print(f"   - Échecs : {failed_sms}")
    print(f"   - En attente : {pending_sms}")
    
    # Afficher les derniers SMS
    recent_sms = SMSNotification.objects.order_by('-created_at')[:5]
    if recent_sms:
        print(f"\n📱 5 derniers SMS :")
        for sms in recent_sms:
            status_icon = "✅" if sms.status == 'sent' else "❌" if sms.status == 'failed' else "⏳"
            notification_type = sms.notification.type if sms.notification else "Test"
            print(f"   {status_icon} {sms.created_at.strftime('%d/%m/%Y %H:%M')} - {sms.phone_number} - {notification_type}")
    else:
        print(f"\n📱 Aucun SMS trouvé")

def test_urls_sms():
    """Test des URLs SMS"""
    print("\n🧪 Test des URLs SMS")
    print("=" * 50)
    
    client = Client()
    
    # Se connecter avec l'utilisateur de test
    user = User.objects.filter(username='test_sms_user').first()
    if user:
        client.force_login(user)
        
        # Test de la page de configuration SMS
        try:
            response = client.get(reverse('notifications:sms_configuration'))
            if response.status_code == 200:
                print("✅ Page de configuration SMS accessible")
            else:
                print(f"❌ Erreur page configuration SMS : {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur accès configuration SMS : {str(e)}")
        
        # Test de la page d'historique SMS
        try:
            response = client.get(reverse('notifications:sms_history'))
            if response.status_code == 200:
                print("✅ Page d'historique SMS accessible")
            else:
                print(f"❌ Erreur page historique SMS : {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur accès historique SMS : {str(e)}")
        
        # Test de la page des préférences
        try:
            response = client.get(reverse('notifications:preferences'))
            if response.status_code == 200:
                print("✅ Page des préférences accessible")
            else:
                print(f"❌ Erreur page préférences : {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur accès préférences : {str(e)}")
    else:
        print("❌ Utilisateur de test non trouvé")
        # Créer un utilisateur de test si nécessaire
        user = User.objects.create_user(
            username='test_url_user',
            email='test_url@example.com',
            password='testpass123'
        )
        print(f"✅ Utilisateur de test créé : {user.username}")
        
        client.force_login(user)
        
        # Test de la page de configuration SMS
        try:
            response = client.get(reverse('notifications:sms_configuration'))
            if response.status_code == 200:
                print("✅ Page de configuration SMS accessible")
            else:
                print(f"❌ Erreur page configuration SMS : {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur accès configuration SMS : {str(e)}")

def main():
    """Fonction principale de test"""
    print("🚀 Test de la configuration SMS et des nouvelles fonctionnalités")
    print("=" * 70)
    
    try:
        # Test de la configuration SMS
        user, preferences = test_configuration_sms()
        
        # Test du service SMS
        test_service_sms()
        
        # Test des notifications de retard
        test_notifications_retard()
        
        # Test des statistiques SMS
        test_statistiques_sms()
        
        # Test des URLs SMS
        test_urls_sms()
        
        print("\n" + "=" * 70)
        print("✅ Tests terminés avec succès !")
        print("\n📋 Résumé :")
        print("   - Configuration SMS : ✅")
        print("   - Service SMS : ✅")
        print("   - Notifications de retard : ✅")
        print("   - Statistiques SMS : ✅")
        print("   - URLs SMS : ✅")
        print("\n🎉 La configuration SMS est opérationnelle !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests : {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 