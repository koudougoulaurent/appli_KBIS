#!/usr/bin/env python
"""
Script pour initialiser des données de test pour les notifications
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from notifications.models import Notification, NotificationPreference
from contrats.models import Contrat
from paiements.models import Paiement
from proprietes.models import Propriete

User = get_user_model()


def create_notification_data():
    """Créer des données de test pour les notifications"""
    print("Création des données de test pour les notifications...")
    
    # Récupérer les utilisateurs existants
    users = User.objects.all()
    if not users.exists():
        print("Aucun utilisateur trouvé. Création d'un utilisateur de test...")
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        users = [user]
    
    # Récupérer des objets existants pour les références
    contrats = Contrat.objects.all()[:3]
    paiements = Paiement.objects.all()[:3]
    proprietes = Propriete.objects.all()[:3]
    
    # Types de notifications à créer
    notification_data = [
        # Notifications de paiement
        {
            'type': 'payment_due',
            'title': 'Échéance de paiement approche',
            'message': 'Le paiement du loyer pour le contrat #{} arrive à échéance dans 5 jours.',
            'priority': 'high',
            'content_objects': list(contrats)
        },
        {
            'type': 'payment_received',
            'title': 'Paiement reçu',
            'message': 'Un paiement de {} XOF a été reçu pour le contrat #{}',
            'priority': 'medium',
            'content_objects': list(paiements)
        },
        
        # Notifications de contrat
        {
            'type': 'contract_expiring',
            'title': 'Contrat expirant',
            'message': 'Le contrat #{} expire dans 30 jours. Pensez à le renouveler.',
            'priority': 'high',
            'content_objects': list(contrats)
        },
        
        # Notifications de maintenance
        {
            'type': 'maintenance_request',
            'title': 'Demande de maintenance',
            'message': 'Nouvelle demande de maintenance pour la propriété {}',
            'priority': 'medium',
            'content_objects': list(proprietes)
        },
        {
            'type': 'maintenance_completed',
            'title': 'Maintenance terminée',
            'message': 'La maintenance de la propriété {} a été terminée avec succès.',
            'priority': 'low',
            'content_objects': list(proprietes)
        },
        
        # Notifications système
        {
            'type': 'system_alert',
            'title': 'Sauvegarde automatique',
            'message': 'La sauvegarde automatique de la base de données a été effectuée avec succès.',
            'priority': 'low',
            'content_objects': []
        },
        {
            'type': 'info',
            'title': 'Bienvenue sur la plateforme',
            'message': 'Bienvenue sur la plateforme de gestion immobilière ! Votre compte a été configuré avec succès.',
            'priority': 'medium',
            'content_objects': []
        }
    ]
    
    # Créer les notifications
    notifications_created = 0
    
    for user in users:
        # Créer des préférences de notification pour l'utilisateur
        NotificationPreference.objects.get_or_create(
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
        
        # Créer des notifications pour chaque type
        for data in notification_data:
            # Créer plusieurs notifications avec des dates différentes
            for i in range(3):
                # Choisir un objet de contenu si disponible
                content_object = None
                if data['content_objects']:
                    content_object = data['content_objects'][i % len(data['content_objects'])]
                
                # Personnaliser le message
                message = data['message']
                if content_object:
                    if isinstance(content_object, Contrat):
                        message = message.format(content_object.id)
                    elif isinstance(content_object, Paiement):
                        message = message.format(content_object.montant, content_object.contrat.id)
                    elif isinstance(content_object, Propriete):
                        message = message.format(content_object.adresse)
                
                # Créer la notification avec une date différente
                created_at = timezone.now() - timedelta(days=i*2, hours=i*3)
                
                notification = Notification.objects.create(
                    recipient=user,
                    type=data['type'],
                    title=data['title'],
                    message=message,
                    priority=data['priority'],
                    content_object=content_object,
                    created_at=created_at,
                    is_read=(i == 0),  # La première notification est lue
                )
                notifications_created += 1
    
    print(f"✅ {notifications_created} notifications créées avec succès !")
    
    # Afficher des statistiques
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    high_priority_notifications = Notification.objects.filter(
        priority__in=['high', 'urgent']
    ).count()
    
    print(f"\n📊 Statistiques des notifications :")
    print(f"   - Total : {total_notifications}")
    print(f"   - Non lues : {unread_notifications}")
    print(f"   - Haute priorité : {high_priority_notifications}")
    
    # Afficher les types de notifications créés
    print(f"\n📋 Types de notifications créés :")
    from django.db import models
    for notification_type, count in Notification.objects.values_list('type').annotate(
        count=models.Count('id')
    ).order_by('-count'):
        type_display = dict(Notification.TYPE_CHOICES)[notification_type]
        print(f"   - {type_display} : {count}")


def test_notification_api():
    """Tester l'API des notifications"""
    print("\n🧪 Test de l'API des notifications...")
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        client = Client()
        
        # Se connecter avec un utilisateur
        user = User.objects.first()
        if user:
            client.force_login(user)
            
            # Tester l'endpoint de comptage
            response = client.get('/notifications/api/notifications/unread_count/')
            if response.status_code == 200:
                print("✅ API unread_count fonctionne")
            else:
                print(f"❌ API unread_count échoue : {response.status_code}")
            
            # Tester l'endpoint des notifications récentes
            response = client.get('/notifications/api/notifications/recent/')
            if response.status_code == 200:
                print("✅ API recent fonctionne")
            else:
                print(f"❌ API recent échoue : {response.status_code}")
            
            # Tester l'endpoint des préférences
            response = client.get('/notifications/api/preferences/my_preferences/')
            if response.status_code == 200:
                print("✅ API preferences fonctionne")
            else:
                print(f"❌ API preferences échoue : {response.status_code}")
                
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API : {e}")


if __name__ == '__main__':
    print("🚀 Initialisation des données de test pour les notifications")
    print("=" * 60)
    
    try:
        create_notification_data()
        test_notification_api()
        
        print("\n✅ Initialisation terminée avec succès !")
        print("\n📝 Prochaines étapes :")
        print("   1. Démarrer le serveur : python manage.py runserver")
        print("   2. Accéder aux notifications : http://127.0.0.1:8000/notifications/")
        print("   3. Tester l'API : http://127.0.0.1:8000/notifications/api/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        import traceback
        traceback.print_exc() 