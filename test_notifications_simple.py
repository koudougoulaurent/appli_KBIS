#!/usr/bin/env python
"""
Script simple pour tester les notifications
Usage: python manage.py shell < test_notifications_simple.py
"""

from notifications.models import Notification, NotificationPreference
from utilisateurs.models import Utilisateur
from contrats.models import Contrat
from paiements.models import Paiement
from proprietes.models import Propriete
from django.utils import timezone
from datetime import timedelta

# Récupérer un utilisateur
user = Utilisateur.objects.filter(is_staff=True).first()
if not user:
    user = Utilisateur.objects.first()

if not user:
    print("❌ Aucun utilisateur trouvé")
    exit()

print(f"✅ Utilisateur trouvé : {user.username}")

# Créer les préférences
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

print(f"✅ Préférences {'créées' if created else 'existantes'}")

# Récupérer des objets existants
contrat = Contrat.objects.first()
paiement = Paiement.objects.first()
propriete = Propriete.objects.first()

# Créer quelques notifications de test
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
    created_at = timezone.now() - timedelta(days=i, hours=i*2)
    
    notification = Notification.objects.create(
        recipient=user,
        type=data['type'],
        title=data['title'],
        message=data['message'],
        priority=data['priority'],
        content_object=data['content_object'],
        created_at=created_at,
        is_read=(i % 3 == 0)
    )
    
    notifications_created += 1
    print(f"✅ Notification créée : {notification.title}")

print(f"\n🎉 {notifications_created} notifications créées avec succès !")

# Statistiques
total = Notification.objects.filter(recipient=user).count()
unread = Notification.objects.filter(recipient=user, is_read=False).count()
high_priority = Notification.objects.filter(recipient=user, priority__in=['high', 'urgent']).count()

print(f"\n📊 Statistiques :")
print(f"   • Total : {total}")
print(f"   • Non lues : {unread}")
print(f"   • Priorité élevée : {high_priority}")

print(f"\n🔗 URLs disponibles :")
print(f"   • Liste : /notifications/")
print(f"   • API : /notifications/api/notifications/")
print(f"   • Préférences : /notifications/preferences/")
