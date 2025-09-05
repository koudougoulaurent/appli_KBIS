#!/usr/bin/env python
"""
Test script pour le système de notifications SMS
Date: 20 juillet 2025
Version: 1.0

Ce script teste le système de notifications SMS pour les paiements en retard.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.utils import timezone
from notifications.sms_service import SMSService, PaymentOverdueService
from notifications.models import Notification, NotificationPreference, SMSNotification
from contrats.models import Contrat
from paiements.models import Paiement
from proprietes.models import Propriete, Bailleur, TypeBien
from utilisateurs.models import Utilisateur
from proprietes.models import Locataire

def test_sms_service():
    """Test du service SMS"""
    print("🧪 TEST DU SERVICE SMS")
    print("=" * 50)
    
    # Test avec simulation
    sms_service = SMSService(provider='custom')
    
    # Test d'envoi de SMS
    result = sms_service.send_sms(
        phone_number="+33123456789",
        message="Test SMS - Votre loyer est en retard",
        notification_id=None
    )
    
    print(f"✅ Résultat envoi SMS: {result}")
    
    # Vérifier que l'enregistrement SMS a été créé
    sms_count = SMSNotification.objects.count()
    print(f"📊 Nombre d'enregistrements SMS: {sms_count}")
    
    return result.get('success', False)

def test_payment_overdue_detection():
    """Test de détection des paiements en retard"""
    print("\n🔍 TEST DE DÉTECTION DES PAIEMENTS EN RETARD")
    print("=" * 50)
    
    # Créer des données de test
    test_data = create_test_data()
    
    # Service de détection
    overdue_service = PaymentOverdueService()
    
    # Vérifier les paiements en retard
    overdue_contracts = overdue_service._get_overdue_contracts(
        overdue_service._get_overdue_date()
    )
    
    print(f"📋 Contrats avec paiements en retard: {len(overdue_contracts)}")
    
    for contrat in overdue_contracts:
        print(f"  - Contrat {contrat.numero_contrat}: {contrat.propriete.titre}")
        print(f"    Locataire: {contrat.locataire.nom} {contrat.locataire.prenom}")
        print(f"    Loyer: {contrat.loyer_mensuel} F CFA")
    
    return len(overdue_contracts)

def test_notification_creation():
    """Test de création des notifications"""
    print("\n📢 TEST DE CRÉATION DES NOTIFICATIONS")
    print("=" * 50)
    
    # Créer une notification de test
    user = Utilisateur.objects.first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return False
    
    notification = Notification.create_notification(
        recipient=user,
        type='payment_overdue',
        title='Test - Paiement en retard',
        message='Ceci est un test de notification de paiement en retard.',
        priority='urgent'
    )
    
    print(f"✅ Notification créée: {notification}")
    print(f"📊 Type: {notification.get_type_display()}")
    print(f"📊 Priorité: {notification.get_priority_display()}")
    print(f"📊 Destinataire: {notification.recipient.username}")
    
    return True

def test_preferences_sms():
    """Test des préférences SMS"""
    print("\n⚙️ TEST DES PRÉFÉRENCES SMS")
    print("=" * 50)
    
    user = Utilisateur.objects.first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return False
    
    # Créer ou récupérer les préférences
    preferences, created = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={
            'sms_notifications': True,
            'payment_overdue_sms': True,
            'phone_number': '+33123456789'
        }
    )
    
    if created:
        print(f"✅ Préférences créées pour {user.username}")
    else:
        print(f"📋 Préférences existantes pour {user.username}")
    
    print(f"📱 SMS activés: {preferences.sms_notifications}")
    print(f"📱 SMS retard de paiement: {preferences.payment_overdue_sms}")
    print(f"📱 Numéro de téléphone: {preferences.phone_number}")
    
    # Tester les préférences
    sms_prefs = preferences.get_sms_preferences()
    print(f"📊 Préférences SMS: {sms_prefs}")
    
    return preferences.sms_notifications

def test_complete_overdue_workflow():
    """Test du workflow complet de détection et notification"""
    print("\n🔄 TEST DU WORKFLOW COMPLET")
    print("=" * 50)
    
    # Créer des données de test
    test_data = create_test_data()
    
    # Service complet
    overdue_service = PaymentOverdueService()
    
    # Exécuter la vérification
    notifications_sent = overdue_service.check_overdue_payments()
    
    print(f"📤 Notifications envoyées: {notifications_sent}")
    
    # Vérifier les notifications créées
    overdue_notifications = Notification.objects.filter(type='payment_overdue')
    print(f"📊 Notifications de retard créées: {overdue_notifications.count()}")
    
    # Vérifier les SMS envoyés
    sms_notifications = SMSNotification.objects.all()
    print(f"📱 SMS envoyés: {sms_notifications.count()}")
    
    for sms in sms_notifications:
        print(f"  - SMS à {sms.phone_number}: {sms.status}")
    
    return notifications_sent > 0

def create_test_data():
    """Créer des données de test"""
    print("\n📝 CRÉATION DES DONNÉES DE TEST")
    print("=" * 50)
    
    # Créer un utilisateur de test
    user, created = Utilisateur.objects.get_or_create(
        username='test_locataire',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Locataire'
        }
    )
    
    if created:
        print(f"✅ Utilisateur créé: {user.username}")
    
    # Créer un locataire
    locataire, created = Locataire.objects.get_or_create(
        nom='Test',
        prenom='Locataire',
        defaults={
            'email': 'test@example.com',
            'telephone': '+33123456789',
            'cree_par': user
        }
    )
    
    if created:
        print(f"✅ Locataire créé: {locataire.nom} {locataire.prenom}")
    
    # Créer un bailleur d'abord
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Test',
        prenom='Bailleur',
        defaults={
            'email': 'bailleur@example.com',
            'telephone': '+33123456788',
            'adresse': '456 Rue Bailleur, Paris'
        }
    )
    
    # Créer un type de bien
    type_bien, created = TypeBien.objects.get_or_create(
        nom='Appartement',
        defaults={'description': 'Appartement standard'}
    )
    
    # Créer une propriété
    propriete, created = Propriete.objects.get_or_create(
        titre='Appartement Test',
        defaults={
            'adresse': '123 Rue Test',
            'ville': 'Paris',
            'code_postal': '75001',
            'pays': 'France',
            'type_bien': type_bien,
            'surface': 50.0,
            'nombre_pieces': 3,
            'nombre_chambres': 2,
            'nombre_salles_bain': 1,
            'loyer_actuel': 1200,
            'disponible': False,
            'bailleur': bailleur
        }
    )
    
    if created:
        print(f"✅ Propriété créée: {propriete.titre}")
    
    # Créer un contrat
    contrat, created = Contrat.objects.get_or_create(
        propriete=propriete,
        locataire=locataire,
        defaults={
            'date_debut': timezone.now().date() - timedelta(days=30),
            'date_fin': timezone.now().date() + timedelta(days=335),
            'date_signature': timezone.now().date() - timedelta(days=30),
            'loyer_mensuel': 1200,
            'jour_paiement': 1,
            'est_actif': True
        }
    )
    
    if created:
        print(f"✅ Contrat créé: {contrat.numero_contrat}")
    
    # Créer des préférences SMS
    preferences, created = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={
            'sms_notifications': True,
            'payment_overdue_sms': True,
            'phone_number': '+33123456789'
        }
    )
    
    if created:
        print(f"✅ Préférences SMS créées")
    
    return {
        'user': user,
        'locataire': locataire,
        'propriete': propriete,
        'contrat': contrat,
        'preferences': preferences
    }

def test_sms_statistics():
    """Test des statistiques SMS"""
    print("\n📊 TEST DES STATISTIQUES SMS")
    print("=" * 50)
    
    # Statistiques générales
    total_sms = SMSNotification.objects.count()
    sent_sms = SMSNotification.objects.filter(status='sent').count()
    delivered_sms = SMSNotification.objects.filter(status='delivered').count()
    failed_sms = SMSNotification.objects.filter(status='failed').count()
    pending_sms = SMSNotification.objects.filter(status='pending').count()
    
    print(f"📱 Total SMS: {total_sms}")
    print(f"📤 SMS envoyés: {sent_sms}")
    print(f"✅ SMS livrés: {delivered_sms}")
    print(f"❌ SMS échoués: {failed_sms}")
    print(f"⏳ SMS en attente: {pending_sms}")
    
    # Statistiques par fournisseur
    providers = SMSNotification.objects.values_list('provider', flat=True).distinct()
    for provider in providers:
        count = SMSNotification.objects.filter(provider=provider).count()
        print(f"📡 {provider}: {count} SMS")
    
    return total_sms

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DU SYSTÈME SMS")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test 1: Service SMS
        results['sms_service'] = test_sms_service()
        
        # Test 2: Détection des paiements en retard
        results['overdue_detection'] = test_payment_overdue_detection()
        
        # Test 3: Création des notifications
        results['notification_creation'] = test_notification_creation()
        
        # Test 4: Préférences SMS
        results['sms_preferences'] = test_preferences_sms()
        
        # Test 5: Workflow complet
        results['complete_workflow'] = test_complete_overdue_workflow()
        
        # Test 6: Statistiques
        results['statistics'] = test_sms_statistics()
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Résumé des tests
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    print(f"\n📊 Résultat global: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 