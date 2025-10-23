"""
Service de Notifications Simples et Efficaces
Notifications navigateur et email sans complexité SMS
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta, date
import json
import logging

from .models import Notification, NotificationPreference
from paiements.models import Paiement
from contrats.models import Contrat
from proprietes.models import Locataire, Bailleur
from paiements.models import RetraitBailleur

logger = logging.getLogger(__name__)


class ServiceNotificationsSimples:
    """Service simple et efficace pour les notifications"""
    
    # Types de notifications avec configuration simple
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
        },
        'info': {
            'title': 'ℹ️ Information',
            'icon': 'bi-info-circle',
            'color': 'info',
            'priority': 'low',
            'auto_read': True,
            'sound': 'info',
            'duration': 3000
        }
    }
    
    @classmethod
    def creer_notification_simple(cls, recipient, type_notification, message, 
                                content_object=None, data_extra=None, 
                                force_send=False):
        """
        Crée une notification simple et efficace
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
            cls._envoyer_notifications_simples(notification, recipient, config)
            
            # Log de l'activité
            logger.info(f"Notification simple créée: {type_notification} pour {recipient.username}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Erreur création notification simple: {str(e)}")
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
    def _envoyer_notifications_simples(cls, notification, recipient, config):
        """Envoie les notifications sur les canaux simples (navigateur + email)"""
        preferences = cls._get_user_preferences(recipient)
        
        # Notification navigateur (toujours activée)
        notification.is_sent_browser = True
        
        # Notification email
        if preferences.email_notifications:
            cls._envoyer_notification_email_simple(notification, recipient)
        
        notification.save()
    
    @classmethod
    def _envoyer_notification_email_simple(cls, notification, recipient):
        """Envoie une notification par email de manière simple"""
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
            logger.error(f"Erreur envoi email simple: {str(e)}")
    
    # ===== NOTIFICATIONS SPÉCIFIQUES SIMPLES =====
    
    @classmethod
    def notifier_paiement_recu_simple(cls, paiement):
        """Notification simple pour paiement reçu"""
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
        
        return cls.creer_notification_simple(
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
    def notifier_retard_paiement_simple(cls, contrat, jours_retard):
        """Notification simple pour retard de paiement"""
        recipient = cls._determiner_destinataire_paiement(contrat)
        locataire = contrat.locataire
        
        message = f"Paiement en retard de {jours_retard} jours pour {locataire.nom} {locataire.prenom} (Contrat: {contrat.numero_contrat})"
        
        return cls.creer_notification_simple(
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
    def notifier_retrait_cree_simple(cls, retrait):
        """Notification simple pour retrait créé"""
        bailleur = retrait.bailleur
        recipient = cls._determiner_destinataire_retrait(bailleur)
        
        message = f"Retrait de {retrait.montant_net_a_payer} F CFA créé pour {bailleur.nom} {bailleur.prenom} (Mois: {retrait.mois_retrait.strftime('%B %Y')})"
        
        return cls.creer_notification_simple(
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
    def notifier_contrat_expirant_simple(cls, contrat, jours_restants):
        """Notification simple pour contrat expirant"""
        recipient = cls._determiner_destinataire_paiement(contrat)
        locataire = contrat.locataire
        
        message = f"Contrat de {locataire.nom} {locataire.prenom} expire dans {jours_restants} jours (Date: {contrat.date_fin.strftime('%d/%m/%Y')})"
        
        return cls.creer_notification_simple(
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
    def notifier_info_simple(cls, recipient, message, title="Information"):
        """Notification simple d'information"""
        return cls.creer_notification_simple(
            recipient=recipient,
            type_notification='info',
            message=message,
            data_extra={'title': title}
        )
    
    @classmethod
    def notifier_alerte_systeme_simple(cls, message):
        """Notification simple d'alerte système"""
        from utilisateurs.models import Utilisateur
        recipients = Utilisateur.objects.filter(
            groupe_travail__nom__in=['PRIVILEGE', 'ADMINISTRATION']
        )
        
        notifications = []
        for recipient in recipients:
            notif = cls.creer_notification_simple(
                recipient=recipient,
                type_notification='system_alert',
                message=message,
                data_extra={'priority': 'high'}
            )
            if notif:
                notifications.append(notif)
        
        return notifications
    
    # ===== MÉTHODES UTILITAIRES SIMPLES =====
    
    @classmethod
    def _determiner_destinataire_paiement(cls, contrat):
        """Détermine le destinataire pour les notifications de paiement"""
        # Priorité: utilisateur qui a créé le locataire > utilisateur qui a créé le bailleur > admin
        if contrat.locataire and contrat.locataire.cree_par:
            return contrat.locataire.cree_par
        elif contrat.propriete and contrat.propriete.bailleur and contrat.propriete.bailleur.cree_par:
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
    def get_notifications_utilisateur_simple(cls, user, limit=20, unread_only=False):
        """Récupère les notifications d'un utilisateur de manière simple"""
        queryset = Notification.objects.filter(recipient=user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')[:limit]
    
    @classmethod
    def get_statistiques_notifications_simple(cls, user):
        """Récupère les statistiques des notifications de manière simple"""
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
    def nettoyer_notifications_anciennes_simple(cls, jours=30):
        """Nettoie les notifications anciennes de manière simple"""
        date_limite = timezone.now() - timedelta(days=jours)
        count = Notification.objects.filter(
            created_at__lt=date_limite,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Notifications anciennes nettoyées: {count}")
        return count
