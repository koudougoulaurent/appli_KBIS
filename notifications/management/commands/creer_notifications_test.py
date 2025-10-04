from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification, NotificationPreference
from utilisateurs.models import Utilisateur
from contrats.models import Contrat
from paiements.models import Paiement
from proprietes.models import Propriete


class Command(BaseCommand):
    help = 'Créer des notifications de test pour démonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=6,
            help='Nombre de notifications à créer (défaut: 6)'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Nom d\'utilisateur pour recevoir les notifications (défaut: premier utilisateur staff)'
        )

    def handle(self, *args, **options):
        count = options['count']
        username = options.get('user')
        
        self.stdout.write(self.style.SUCCESS('🚀 Création de notifications de test...'))
        
        # Récupérer l'utilisateur
        if username:
            try:
                user = Utilisateur.objects.get(username=username)
            except Utilisateur.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Utilisateur "{username}" non trouvé.')
                )
                return
        else:
            user = Utilisateur.objects.filter(is_staff=True).first()
            if not user:
                user = Utilisateur.objects.first()
            
            if not user:
                self.stdout.write(
                    self.style.ERROR('❌ Aucun utilisateur trouvé. Créez d\'abord un utilisateur.')
                )
                return
        
        self.stdout.write(f'✅ Utilisateur trouvé : {user.username}')
        
        # Créer les préférences de notification
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
            self.stdout.write('✅ Préférences de notification créées')
        else:
            self.stdout.write('✅ Préférences de notification existantes')
        
        # Récupérer des objets existants
        contrat = Contrat.objects.first()
        paiement = Paiement.objects.first()
        propriete = Propriete.objects.first()
        
        # Types de notifications disponibles
        notification_templates = [
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
            },
            {
                'type': 'payment_overdue',
                'title': 'Paiement en retard',
                'message': f'Le paiement du loyer pour le contrat #{contrat.id if contrat else "N/A"} est en retard depuis 3 jours.',
                'priority': 'urgent',
                'content_object': contrat
            },
            {
                'type': 'maintenance_completed',
                'title': 'Maintenance terminée',
                'message': f'La maintenance de la propriété {propriete.titre if propriete else "N/A"} a été terminée avec succès.',
                'priority': 'low',
                'content_object': propriete
            }
        ]
        
        notifications_created = 0
        
        # Créer les notifications
        for i in range(count):
            template = notification_templates[i % len(notification_templates)]
            
            # Créer la notification avec une date différente
            created_at = timezone.now() - timedelta(days=i, hours=i*2)
            
            notification = Notification.objects.create(
                recipient=user,
                type=template['type'],
                title=template['title'],
                message=template['message'],
                priority=template['priority'],
                content_object=template['content_object'],
                created_at=created_at,
                is_read=(i % 3 == 0)  # Marquer certaines comme lues
            )
            
            notifications_created += 1
            self.stdout.write(f'✅ Notification créée : {notification.title}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 {notifications_created} notifications créées avec succès !')
        )
        
        # Afficher des statistiques
        total_notifications = Notification.objects.filter(recipient=user).count()
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        high_priority_notifications = Notification.objects.filter(
            recipient=user, 
            priority__in=['high', 'urgent']
        ).count()
        
        self.stdout.write(f'\n📊 Statistiques des notifications :')
        self.stdout.write(f'   • Total : {total_notifications}')
        self.stdout.write(f'   • Non lues : {unread_notifications}')
        self.stdout.write(f'   • Priorité élevée : {high_priority_notifications}')
        
        self.stdout.write(f'\n🔗 URLs disponibles :')
        self.stdout.write(f'   • Liste des notifications : /notifications/')
        self.stdout.write(f'   • API REST : /notifications/api/notifications/')
        self.stdout.write(f'   • Préférences : /notifications/preferences/')
