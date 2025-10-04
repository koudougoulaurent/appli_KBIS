#!/usr/bin/env python
"""
Script pour créer des notifications de test
Usage: python manage.py shell < creer_notifications_test.py
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from notifications.models import Notification, NotificationPreference
from utilisateurs.models import Utilisateur
from contrats.models import Contrat
from paiements.models import Paiement
from proprietes.models import Propriete

def creer_notifications_test():
    """Créer des notifications de test pour démonstration"""
    
    print("🚀 Création de notifications de test...")
    
    # Récupérer un utilisateur existant
    try:
        user = Utilisateur.objects.filter(is_staff=True).first()
        if not user:
            user = Utilisateur.objects.first()
        
        if not user:
            print("❌ Aucun utilisateur trouvé. Créez d'abord un utilisateur.")
            return
        
        print(f"✅ Utilisateur trouvé : {user.username}")
        
        # Créer les préférences de notification si elles n'existent pas
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
            }
        )
        
        if created:
            print("✅ Préférences de notification créées")
        else:
            print("✅ Préférences de notification existantes")
        
        # Récupérer des objets existants pour les références
        contrat = Contrat.objects.first()
        paiement = Paiement.objects.first()
        propriete = Propriete.objects.first()
        
        # Créer des notifications de différents types
        notifications_data = [
            {
                'type': 'payment_received',
                'title': 'Paiement reçu',
                'message': f'Un paiement de 150,000 F CFA a été reçu pour le contrat #{contrat.id if contrat else "N/A"}.',
                'priority': 'medium',
                'content_object': paiement
            },
            {
                'type': 'payment_due',
                'title': 'Échéance de paiement approche',
                'message': f'Le paiement du loyer pour le contrat #{contrat.id if contrat else "N/A"} arrive à échéance dans 5 jours.',
                'priority': 'high',
                'content_object': contrat
            },
            {
                'type': 'contract_expiring',
                'title': 'Contrat expirant',
                'message': f'Le contrat #{contrat.id if contrat else "N/A"} expire dans 15 jours. Pensez à le renouveler.',
                'priority': 'high',
                'content_object': contrat
            },
            {
                'type': 'maintenance_request',
                'title': 'Demande de maintenance',
                'message': f'Nouvelle demande de maintenance pour la propriété {propriete.titre if propriete else "N/A"}.',
                'priority': 'medium',
                'content_object': propriete
            },
            {
                'type': 'system_alert',
                'title': 'Sauvegarde automatique',
                'message': 'La sauvegarde automatique de la base de données a été effectuée avec succès.',
                'priority': 'low',
                'content_object': None
            },
            {
                'type': 'info',
                'title': 'Bienvenue sur la plateforme',
                'message': 'Bienvenue sur la plateforme de gestion immobilière ! Explorez toutes les fonctionnalités disponibles.',
                'priority': 'low',
                'content_object': None
            }
        ]
        
        notifications_created = 0
        
        for i, data in enumerate(notifications_data):
            # Créer la notification avec une date différente
            created_at = timezone.now() - timedelta(days=i, hours=i*2)
            
            notification = Notification.objects.create(
                recipient=user,
                type=data['type'],
                title=data['title'],
                message=data['message'],
                priority=data['priority'],
                content_object=data['content_object'],
                created_at=created_at,
                is_read=(i % 3 == 0)  # Marquer certaines comme lues
            )
            
            notifications_created += 1
            print(f"✅ Notification créée : {notification.title}")
        
        print(f"\n🎉 {notifications_created} notifications créées avec succès !")
        
        # Afficher des statistiques
        total_notifications = Notification.objects.filter(recipient=user).count()
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        high_priority_notifications = Notification.objects.filter(
            recipient=user, 
            priority__in=['high', 'urgent']
        ).count()
        
        print(f"\n📊 Statistiques des notifications :")
        print(f"   • Total : {total_notifications}")
        print(f"   • Non lues : {unread_notifications}")
        print(f"   • Priorité élevée : {high_priority_notifications}")
        
        # Tester l'API
        print(f"\n🔗 URLs disponibles :")
        print(f"   • Liste des notifications : /notifications/")
        print(f"   • API REST : /notifications/api/notifications/")
        print(f"   • Préférences : /notifications/preferences/")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des notifications : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    creer_notifications_test()
