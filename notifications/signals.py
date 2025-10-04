from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Notification, NotificationPreference
from paiements.models import Paiement
from contrats.models import Contrat
from proprietes.models import Propriete

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Paiement)
def creer_notification_paiement(sender, instance, created, **kwargs):
    """
    Créer une notification quand un paiement est reçu
    """
    if created and instance.statut == 'valide':
        try:
            # Déterminer le destinataire
            recipient = None
            if instance.contrat and instance.contrat.locataire and instance.contrat.locataire.cree_par:
                recipient = instance.contrat.locataire.cree_par
            elif instance.contrat and instance.contrat.propriete and instance.contrat.propriete.bailleur and instance.contrat.propriete.bailleur.cree_par:
                recipient = instance.contrat.propriete.bailleur.cree_par
            else:
                # Utiliser l'utilisateur qui a créé le paiement
                recipient = instance.cree_par
            
            if recipient:
                # Vérifier les préférences de notification
                preferences, created = NotificationPreference.objects.get_or_create(
                    user=recipient
                )
                
                if preferences.browser_notifications and preferences.payment_received_email:
                    notification = Notification.create_notification(
                        recipient=recipient,
                        type='payment_received',
                        title='Paiement reçu',
                        message=f'Un paiement de {instance.montant:,.0f} F CFA a été reçu pour le contrat #{instance.contrat.id if instance.contrat else "N/A"}.',
                        priority='medium',
                        content_object=instance
                    )
                    logger.info(f"Notification de paiement créée pour {recipient.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification de paiement : {e}")


@receiver(post_save, sender=Contrat)
def creer_notification_contrat(sender, instance, created, **kwargs):
    """
    Créer des notifications pour les contrats
    """
    if created:
        try:
            # Notification pour le locataire
            if instance.locataire and instance.locataire.cree_par:
                recipient = instance.locataire.cree_par
                preferences, created = NotificationPreference.objects.get_or_create(
                    user=recipient
                )
                
                if preferences.browser_notifications:
                    notification = Notification.create_notification(
                        recipient=recipient,
                        type='info',
                        title='Nouveau contrat créé',
                        message=f'Un nouveau contrat a été créé pour la propriété {instance.propriete.titre if instance.propriete else "N/A"}.',
                        priority='medium',
                        content_object=instance
                    )
                    logger.info(f"Notification de contrat créée pour {recipient.username}")
            
            # Notification pour le bailleur
            if instance.propriete and instance.propriete.bailleur and instance.propriete.bailleur.cree_par:
                recipient = instance.propriete.bailleur.cree_par
                preferences, created = NotificationPreference.objects.get_or_create(
                    user=recipient
                )
                
                if preferences.browser_notifications:
                    notification = Notification.create_notification(
                        recipient=recipient,
                        type='info',
                        title='Nouveau contrat créé',
                        message=f'Un nouveau contrat a été créé pour votre propriété {instance.propriete.titre}.',
                        priority='medium',
                        content_object=instance
                    )
                    logger.info(f"Notification de contrat créée pour {recipient.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification de contrat : {e}")


@receiver(pre_save, sender=Contrat)
def verifier_expiration_contrat(sender, instance, **kwargs):
    """
    Vérifier si un contrat va expirer bientôt
    """
    if instance.pk:  # Contrat existant
        try:
            old_instance = Contrat.objects.get(pk=instance.pk)
            
            # Vérifier si la date de fin a changé et si elle est dans les 30 prochains jours
            if old_instance.date_fin != instance.date_fin:
                today = timezone.now().date()
                days_until_expiry = (instance.date_fin - today).days
                
                if 0 <= days_until_expiry <= 30:
                    # Créer une notification d'expiration
                    recipients = []
                    
                    if instance.locataire and instance.locataire.cree_par:
                        recipients.append(instance.locataire.cree_par)
                    if instance.propriete and instance.propriete.bailleur and instance.propriete.bailleur.cree_par:
                        recipients.append(instance.propriete.bailleur.cree_par)
                    
                    for recipient in recipients:
                        preferences, created = NotificationPreference.objects.get_or_create(
                            user=recipient
                        )
                        
                        if preferences.browser_notifications and preferences.contract_expiring_email:
                            priority = 'urgent' if days_until_expiry <= 7 else 'high'
                            notification = Notification.create_notification(
                                recipient=recipient,
                                type='contract_expiring',
                                title='Contrat expirant',
                                message=f'Le contrat #{instance.id} expire dans {days_until_expiry} jour(s). Pensez à le renouveler.',
                                priority=priority,
                                content_object=instance
                            )
                            logger.info(f"Notification d'expiration créée pour {recipient.username}")
        except Contrat.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'expiration du contrat : {e}")


@receiver(post_save, sender=Propriete)
def creer_notification_propriete(sender, instance, created, **kwargs):
    """
    Créer des notifications pour les changements de propriété
    """
    if created:
        try:
            # Notification pour le bailleur
            if instance.bailleur and instance.bailleur.cree_par:
                recipient = instance.bailleur.cree_par
                preferences, created = NotificationPreference.objects.get_or_create(
                    user=recipient
                )
                
                if preferences.browser_notifications:
                    notification = Notification.create_notification(
                        recipient=recipient,
                        type='info',
                        title='Nouvelle propriété ajoutée',
                        message=f'Une nouvelle propriété "{instance.titre}" a été ajoutée à votre portefeuille.',
                        priority='low',
                        content_object=instance
                    )
                    logger.info(f"Notification de propriété créée pour {recipient.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification de propriété : {e}")


def creer_notification_echeance_paiement():
    """
    Fonction pour créer des notifications d'échéance de paiement
    À appeler via une tâche cron ou management command
    """
    try:
        today = timezone.now().date()
        # Vérifier les contrats actifs dont l'échéance est dans 5 jours
        echeance_date = today + timedelta(days=5)
        
        contrats_echeance = Contrat.objects.filter(
            statut='actif',
            date_fin__gte=today,
            date_debut__lte=echeance_date
        )
        
        for contrat in contrats_echeance:
            recipients = []
            
            if contrat.locataire and contrat.locataire.cree_par:
                recipients.append(contrat.locataire.cree_par)
            if contrat.propriete and contrat.propriete.bailleur and contrat.propriete.bailleur.cree_par:
                recipients.append(contrat.propriete.bailleur.cree_par)
            
            for recipient in recipients:
                preferences, created = NotificationPreference.objects.get_or_create(
                    user=recipient
                )
                
                if preferences.browser_notifications and preferences.payment_due_email:
                    notification = Notification.create_notification(
                        recipient=recipient,
                        type='payment_due',
                        title='Échéance de paiement approche',
                        message=f'Le paiement du loyer pour le contrat #{contrat.id} arrive à échéance dans 5 jours.',
                        priority='high',
                        content_object=contrat
                    )
                    logger.info(f"Notification d'échéance créée pour {recipient.username}")
    except Exception as e:
        logger.error(f"Erreur lors de la création des notifications d'échéance : {e}")


def creer_notifications_retard_paiement():
    """
    Fonction pour créer des notifications de retard de paiement
    À appeler via une tâche cron ou management command
    """
    try:
        from notifications.sms_service import PaymentOverdueService
        
        service = PaymentOverdueService()
        service.check_overdue_payments()
    except Exception as e:
        logger.error(f"Erreur lors de la création des notifications de retard : {e}")
