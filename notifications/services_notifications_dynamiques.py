"""
Service de Notifications Dynamiques Ultra-Fonctionnel
Gère toutes les notifications en temps réel avec intelligence artificielle
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import logging

from .models import Notification, NotificationPreference, SMSNotification
from paiements.models import Paiement
from contrats.models import Contrat
from proprietes.models import Locataire, Bailleur
from .sms_service import SMSService

logger = logging.getLogger(__name__)


class ServiceNotificationsDynamiques:
    """Service ultra-avancé pour les notifications dynamiques"""
    
    # Types de notifications avec configuration complète
    NOTIFICATION_TYPES = {
        'payment_received': {
            'title': '💰 Paiement Reçu',
            'icon': 'bi-cash-stack',
            'color': 'success',
            'priority': 'medium',
            'auto_read': False,
            'sound': 'success',
            'duration': 5000
        },
        'payment_partial': {
            'title': '⚠️ Paiement Partiel',
            'icon': 'bi-cash-coin',
            'color': 'warning',
            'priority': 'high',
            'auto_read': False,
            'sound': 'warning',
            'duration': 7000
        },
        'payment_overdue': {
            'title': '🚨 Paiement en Retard',
            'icon': 'bi-exclamation-triangle',
            'color': 'danger',
            'priority': 'urgent',
            'auto_read': False,
            'sound': 'alert',
            'duration': 10000
        },
        'advance_consumed': {
            'title': '📉 Avance Consommée',
            'icon': 'bi-arrow-down-circle',
            'color': 'info',
            'priority': 'medium',
            'auto_read': True,
            'sound': 'info',
            'duration': 4000
        },
        'contract_expiring': {
            'title': '📅 Contrat Expirant',
            'icon': 'bi-calendar-x',
            'color': 'warning',
            'priority': 'high',
            'auto_read': False,
            'sound': 'warning',
            'duration': 6000
        },
        'synchronization_complete': {
            'title': '✅ Synchronisation Terminée',
            'icon': 'bi-check-circle',
            'color': 'success',
            'priority': 'low',
            'auto_read': True,
            'sound': 'success',
            'duration': 3000
        },
        'retrait_created': {
            'title': '💸 Retrait Créé',
            'icon': 'bi-bank',
            'color': 'primary',
            'priority': 'medium',
            'auto_read': False,
            'sound': 'info',
            'duration': 5000
        },
        'system_alert': {
            'title': '🔧 Alerte Système',
            'icon': 'bi-gear',
            'color': 'secondary',
            'priority': 'high',
            'auto_read': False,
            'sound': 'alert',
            'duration': 8000
        }
    }
    
    @classmethod
    def creer_notification_intelligente(cls, recipient, type_notification, message, 
                                      content_object=None, data_extra=None, 
                                      force_send=False):
        """
        Crée une notification intelligente avec gestion avancée
        """
        try:
            # Vérifier les préférences utilisateur
            if not force_send:
                preferences = cls._get_user_preferences(recipient)
                if not cls._should_send_notification(preferences, type_notification):
                    return None
            
            # Configuration de la notification
            config = cls.NOTIFICATION_TYPES.get(type_notification, cls.NOTIFICATION_TYPES['info'])
            
            # Créer la notification
            notification = Notification.objects.create(
                recipient=recipient,
                type=type_notification,
                title=config['title'],
                message=message,
                priority=config['priority'],
                content_object=content_object
            )
            
            # Ajouter des données extra si fournies
            if data_extra:
                notification.data_extra = json.dumps(data_extra)
                notification.save()
            
            # Envoyer les notifications selon les préférences
            cls._envoyer_notifications_multi_canaux(notification, recipient, config)
            
            # Log de l'activité
            logger.info(f"Notification créée: {type_notification} pour {recipient.username}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Erreur création notification: {str(e)}")
            return None
    
    @classmethod
    def _get_user_preferences(cls, user):
        """Récupère les préférences de notification de l'utilisateur"""
        try:
            return NotificationPreference.objects.get(user=user)
        except NotificationPreference.DoesNotExist:
            return NotificationPreference.objects.create(user=user)
    
    @classmethod
    def _should_send_notification(cls, preferences, type_notification):
        """Détermine si une notification doit être envoyée"""
        if not preferences.browser_notifications:
            return False
        
        # Vérifier les préférences spécifiques par type
        email_prefs = preferences.get_email_preferences()
        return email_prefs.get(type_notification, True)
    
    @classmethod
    def _envoyer_notifications_multi_canaux(cls, notification, recipient, config):
        """Envoie les notifications sur tous les canaux activés"""
        preferences = cls._get_user_preferences(recipient)
        
        # Notification navigateur (toujours activée)
        notification.is_sent_browser = True
        
        # Notification email
        if preferences.email_notifications:
            cls._envoyer_notification_email(notification, recipient)
        
        # Notification SMS
        if preferences.sms_notifications and preferences.phone_number:
            cls._envoyer_notification_sms(notification, recipient, preferences.phone_number)
        
        notification.save()
    
    @classmethod
    def _envoyer_notification_email(cls, notification, recipient):
        """Envoie une notification par email"""
        try:
            subject = f"[GESTIMMOB] {notification.title}"
            message = f"""
            {notification.message}
            
            Date: {notification.created_at.strftime('%d/%m/%Y %H:%M')}
            Priorité: {notification.get_priority_display()}
            
            ---
            GESTIMMOB - Système de Gestion Immobilière
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False
            )
            
            notification.is_sent_email = True
            notification.save()
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {str(e)}")
    
    @classmethod
    def _envoyer_notification_sms(cls, notification, recipient, phone_number):
        """Envoie une notification par SMS"""
        try:
            sms_service = SMSService()
            message = f"{notification.title}: {notification.message[:100]}..."
            
            success, response = sms_service.send_sms(
                phone_number=phone_number,
                message=message,
                user=recipient,
                notification_id=notification.id
            )
            
            if success:
                notification.is_sent_sms = True
                notification.save()
            
        except Exception as e:
            logger.error(f"Erreur envoi SMS: {str(e)}")
    
    # ===== NOTIFICATIONS SPÉCIFIQUES =====
    
    @classmethod
    def notifier_paiement_recu(cls, paiement):
        """Notification pour paiement reçu"""
        contrat = paiement.contrat
        locataire = contrat.locataire
        
        # Déterminer le destinataire
        recipient = cls._determiner_destinataire_paiement(contrat)
        
        message = f"Paiement de {paiement.montant} F CFA reçu de {locataire.nom} {locataire.prenom} pour {paiement.mois_paye or 'le mois en cours'}"
        
        if paiement.est_paiement_partiel:
            message += f" (Paiement partiel - Reste dû: {paiement.montant_restant_du} F CFA)"
            type_notif = 'payment_partial'
        else:
            type_notif = 'payment_received'
        
        return cls.creer_notification_intelligente(
            recipient=recipient,
            type_notification=type_notif,
            message=message,
            content_object=paiement,
            data_extra={
                'montant': float(paiement.montant),
                'locataire': locataire.get_nom_complet(),
                'mois': paiement.mois_paye,
                'est_partiel': paiement.est_paiement_partiel
            }
        )
    
    @classmethod
    def notifier_retard_paiement(cls, contrat, jours_retard):
        """Notification pour retard de paiement"""
        recipient = cls._determiner_destinataire_paiement(contrat)
        locataire = contrat.locataire
        
        message = f"Paiement en retard de {jours_retard} jours pour {locataire.nom} {locataire.prenom} (Contrat: {contrat.numero_contrat})"
        
        return cls.creer_notification_intelligente(
            recipient=recipient,
            type_notification='payment_overdue',
            message=message,
            content_object=contrat,
            data_extra={
                'jours_retard': jours_retard,
                'locataire': locataire.get_nom_complet(),
                'contrat': contrat.numero_contrat
            }
        )
    
    @classmethod
    def notifier_avance_consommee(cls, avance, mois_consommes):
        """Notification pour consommation d'avance"""
        contrat = avance.contrat
        recipient = cls._determiner_destinataire_paiement(contrat)
        
        message = f"Avance de {avance.montant_avance} F CFA consommée pour {mois_consommes} mois (Contrat: {contrat.numero_contrat})"
        
        return cls.creer_notification_intelligente(
            recipient=recipient,
            type_notification='advance_consumed',
            message=message,
            content_object=avance,
            data_extra={
                'montant_avance': float(avance.montant_avance),
                'mois_consommes': mois_consommes,
                'contrat': contrat.numero_contrat
            }
        )
    
    @classmethod
    def notifier_retrait_cree(cls, retrait):
        """Notification pour retrait créé"""
        bailleur = retrait.bailleur
        recipient = cls._determiner_destinataire_retrait(bailleur)
        
        message = f"Retrait de {retrait.montant_net_a_payer} F CFA créé pour {bailleur.nom} {bailleur.prenom} (Mois: {retrait.mois_retrait.strftime('%B %Y')})"
        
        return cls.creer_notification_intelligente(
            recipient=recipient,
            type_notification='retrait_created',
            message=message,
            content_object=retrait,
            data_extra={
                'montant': float(retrait.montant_net_a_payer),
                'bailleur': bailleur.get_nom_complet(),
                'mois': retrait.mois_retrait.strftime('%B %Y')
            }
        )
    
    @classmethod
    def notifier_contrat_expirant(cls, contrat, jours_restants):
        """Notification pour contrat expirant"""
        recipient = cls._determiner_destinataire_paiement(contrat)
        locataire = contrat.locataire
        
        message = f"Contrat de {locataire.nom} {locataire.prenom} expire dans {jours_restants} jours (Date: {contrat.date_fin.strftime('%d/%m/%Y')})"
        
        return cls.creer_notification_intelligente(
            recipient=recipient,
            type_notification='contract_expiring',
            message=message,
            content_object=contrat,
            data_extra={
                'jours_restants': jours_restants,
                'locataire': locataire.get_nom_complet(),
                'date_fin': contrat.date_fin.strftime('%d/%m/%Y')
            }
        )
    
    @classmethod
    def notifier_synchronisation_complete(cls, type_sync, details):
        """Notification pour synchronisation terminée"""
        # Notifier tous les utilisateurs privilégiés
        from utilisateurs.models import Utilisateur
        recipients = Utilisateur.objects.filter(
            groupe_travail__nom__in=['PRIVILEGE', 'ADMINISTRATION']
        )
        
        message = f"Synchronisation {type_sync} terminée: {details}"
        
        notifications = []
        for recipient in recipients:
            notif = cls.creer_notification_intelligente(
                recipient=recipient,
                type_notification='synchronization_complete',
                message=message,
                data_extra={'type_sync': type_sync, 'details': details}
            )
            if notif:
                notifications.append(notif)
        
        return notifications
    
    @classmethod
    def notifier_alerte_systeme(cls, message, priority='high'):
        """Notification d'alerte système"""
        from utilisateurs.models import Utilisateur
        recipients = Utilisateur.objects.filter(
            groupe_travail__nom__in=['PRIVILEGE', 'ADMINISTRATION']
        )
        
        notifications = []
        for recipient in recipients:
            notif = cls.creer_notification_intelligente(
                recipient=recipient,
                type_notification='system_alert',
                message=message,
                data_extra={'priority': priority}
            )
            if notif:
                notifications.append(notif)
        
        return notifications
    
    # ===== MÉTHODES UTILITAIRES =====
    
    @classmethod
    def _determiner_destinataire_paiement(cls, contrat):
        """Détermine le destinataire pour les notifications de paiement"""
        # Priorité: utilisateur qui a créé le locataire > utilisateur qui a créé le bailleur > admin
        if contrat.locataire and hasattr(contrat.locataire, 'cree_par') and contrat.locataire.cree_par:
            return contrat.locataire.cree_par
        elif contrat.propriete and contrat.propriete.bailleur and hasattr(contrat.propriete.bailleur, 'cree_par') and contrat.propriete.bailleur.cree_par:
            return contrat.propriete.bailleur.cree_par
        else:
            # Retourner le premier admin disponible
            from utilisateurs.models import Utilisateur
            return Utilisateur.objects.filter(
                groupe_travail__nom='ADMINISTRATION'
            ).first()
    
    @classmethod
    def _determiner_destinataire_retrait(cls, bailleur):
        """Détermine le destinataire pour les notifications de retrait"""
        if bailleur.cree_par:
            return bailleur.cree_par
        else:
            from utilisateurs.models import Utilisateur
            return Utilisateur.objects.filter(
                groupe_travail__nom='ADMINISTRATION'
            ).first()
    
    @classmethod
    def get_notifications_utilisateur(cls, user, limit=20, unread_only=False):
        """Récupère les notifications d'un utilisateur"""
        queryset = Notification.objects.filter(recipient=user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')[:limit]
    
    @classmethod
    def get_statistiques_notifications(cls, user):
        """Récupère les statistiques des notifications"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        return {
            'total': Notification.objects.filter(recipient=user).count(),
            'non_lues': Notification.objects.filter(recipient=user, is_read=False).count(),
            'aujourd_hui': Notification.objects.filter(
                recipient=user, 
                created_at__date=today
            ).count(),
            'cette_semaine': Notification.objects.filter(
                recipient=user, 
                created_at__date__gte=week_ago
            ).count(),
            'par_priorite': {
                'urgent': Notification.objects.filter(
                    recipient=user, priority='urgent', is_read=False
                ).count(),
                'high': Notification.objects.filter(
                    recipient=user, priority='high', is_read=False
                ).count(),
                'medium': Notification.objects.filter(
                    recipient=user, priority='medium', is_read=False
                ).count(),
                'low': Notification.objects.filter(
                    recipient=user, priority='low', is_read=False
                ).count(),
            }
        }
    
    @classmethod
    def nettoyer_notifications_anciennes(cls, jours=30):
        """Nettoie les notifications anciennes"""
        date_limite = timezone.now() - timedelta(days=jours)
        count = Notification.objects.filter(
            created_at__lt=date_limite,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Notifications anciennes nettoyées: {count}")
        return count
