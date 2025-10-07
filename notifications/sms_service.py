"""
Service SMS pour les notifications de retard de paiement
"""

import os
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import SMSNotification, Notification, NotificationPreference

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service pour l'envoi de SMS via différents fournisseurs
    """
    
    def __init__(self, provider='twilio'):
        self.provider = provider
        self.client = self._get_client()
    
    def _get_client(self):
        """Obtenir le client SMS selon le fournisseur"""
        if self.provider == 'twilio':
            return self._get_twilio_client()
        elif self.provider == 'nexmo':
            return self._get_nexmo_client()
        else:
            return None
    
    def _get_twilio_client(self):
        """Obtenir le client Twilio"""
        try:
            from twilio.rest import Client
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', os.environ.get('TWILIO_ACCOUNT_SID'))
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', os.environ.get('TWILIO_AUTH_TOKEN'))
            if account_sid and auth_token:
                return Client(account_sid, auth_token)
        except ImportError:
            logger.warning("Twilio library not installed. Install with: pip install twilio")
        except Exception as e:
            logger.error(f"Error initializing Twilio client: {e}")
        return None
    
    def _get_nexmo_client(self):
        """Obtenir le client Nexmo/Vonage"""
        try:
            import vonage
            api_key = getattr(settings, 'NEXMO_API_KEY', os.environ.get('NEXMO_API_KEY'))
            api_secret = getattr(settings, 'NEXMO_API_SECRET', os.environ.get('NEXMO_API_SECRET'))
            if api_key and api_secret:
                return vonage.Client(key=api_key, secret=api_secret)
        except ImportError:
            logger.warning("Vonage library not installed. Install with: pip install vonage")
        except Exception as e:
            logger.error(f"Error initializing Nexmo client: {e}")
        return None
    
    def send_sms(self, phone_number, message, notification_id=None, user=None):
        """
        Envoyer un SMS
        
        Args:
            phone_number (str): Numéro de téléphone
            message (str): Message à envoyer
            notification_id (int): ID de la notification associée
            user: Utilisateur associé au SMS
        
        Returns:
            dict: Résultat de l'envoi
        """
        # Créer l'enregistrement SMS
        sms_notification = SMSNotification.objects.create(
            notification_id=notification_id,
            user=user,
            phone_number=phone_number,
            message=message,
            provider=self.provider
        )
        
        try:
            if self.provider == 'twilio':
                result = self._send_via_twilio(phone_number, message)
            elif self.provider == 'nexmo':
                result = self._send_via_nexmo(phone_number, message)
            else:
                result = self._send_via_custom(phone_number, message)
            
            # Mettre à jour le statut
            if result.get('success'):
                sms_notification.mark_as_sent(
                    provider_message_id=result.get('message_id'),
                    provider_response=str(result)
                )
                logger.info(f"SMS sent successfully to {phone_number}")
            else:
                sms_notification.mark_as_failed(provider_response=str(result))
                logger.error(f"Failed to send SMS to {phone_number}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            sms_notification.mark_as_failed(provider_response=str(e))
            logger.error(f"Exception sending SMS to {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_via_twilio(self, phone_number, message):
        """Envoyer via Twilio"""
        if not self.client:
            return {'success': False, 'error': 'Twilio client not available'}
        
        try:
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', os.environ.get('TWILIO_FROM_NUMBER'))
            if not from_number:
                return {'success': False, 'error': 'TWILIO_FROM_NUMBER not configured'}
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_via_nexmo(self, phone_number, message):
        """Envoyer via Nexmo/Vonage"""
        if not self.client:
            return {'success': False, 'error': 'Nexmo client not available'}
        
        try:
            from_number = getattr(settings, 'NEXMO_FROM_NUMBER', os.environ.get('NEXMO_FROM_NUMBER'))
            if not from_number:
                return {'success': False, 'error': 'NEXMO_FROM_NUMBER not configured'}
            
            response = self.client.sms.send_message({
                "from": from_number,
                "to": phone_number,
                "text": message
            })
            
            if response["messages"][0]["status"] == "0":
                return {
                    'success': True,
                    'message_id': response["messages"][0]["message-id"],
                    'status': 'sent'
                }
            else:
                return {
                    'success': False,
                    'error': response["messages"][0]["error-text"]
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_via_custom(self, phone_number, message):
        """Envoyer via un fournisseur personnalisé"""
        # Simulation pour les tests
        logger.info(f"Simulated SMS to {phone_number}: {message}")
        return {
            'success': True,
            'message_id': f'sim_{datetime.now().timestamp()}',
            'status': 'sent'
        }


class PaymentOverdueService:
    """
    Service pour détecter et notifier les paiements en retard
    """
    
    def __init__(self):
        self.sms_service = SMSService()
    
    def check_overdue_payments(self):
        """
        Vérifier les paiements en retard et envoyer des notifications
        """
        # Date limite pour considérer un paiement en retard (fin du mois + 5 jours)
        overdue_date = self._get_overdue_date()
        
        # Trouver les contrats avec paiements en retard
        overdue_contracts = self._get_overdue_contracts(overdue_date)
        
        notifications_sent = 0
        
        for contrat in overdue_contracts:
            try:
                self._send_overdue_notification(contrat, overdue_date)
                notifications_sent += 1
            except Exception as e:
                logger.error("Error sending overdue notification for contract %s: %s", contrat.id, e)
        
        logger.info("Sent %d overdue payment notifications", notifications_sent)
        return notifications_sent
    
    def _get_overdue_date(self):
        """Calculer la date limite pour les paiements en retard"""
        today = timezone.now().date()
        
        # Si on est dans les 5 premiers jours du mois, vérifier le mois précédent
        if today.day <= 5:
            # Dernier jour du mois précédent
            if today.month == 1:
                previous_month = 12
                previous_year = today.year - 1
            else:
                previous_month = today.month - 1
                previous_year = today.year
            
            # Trouver le dernier jour du mois précédent
            if previous_month in [4, 6, 9, 11]:  # 30 jours
                last_day = 30
            elif previous_month == 2:  # Février
                if previous_year % 4 == 0 and (previous_year % 100 != 0 or previous_year % 400 == 0):
                    last_day = 29  # Année bissextile
                else:
                    last_day = 28
            else:  # 31 jours
                last_day = 31
            
            return datetime(previous_year, previous_month, last_day).date()
        else:
            # Sinon, vérifier le mois en cours
            return datetime(today.year, today.month, 1).date()
    
    def _get_overdue_contracts(self, overdue_date):
        """Obtenir les contrats avec paiements en retard"""
        from contrats.models import Contrat
        from paiements.models import Paiement
        from dateutil.relativedelta import relativedelta
        
        # Trouver les contrats actifs
        active_contracts = Contrat.objects.filter(
            date_fin__gte=timezone.now().date(),
            est_actif=True
        )
        
        overdue_contracts = []
        today = timezone.now().date()
        
        for contrat in active_contracts:
            # Vérifier les retards pour le mois en cours ET les mois précédents
            months_to_check = self._get_months_to_check(today, overdue_date)
            
            for check_date in months_to_check:
                # Vérifier si le paiement du mois est en retard
                expected_payment_date = datetime(
                    check_date.year, 
                    check_date.month, 
                    contrat.jour_paiement or 1
                ).date()
                
                # Chercher un paiement pour ce mois
                payment_exists = Paiement.objects.filter(
                    contrat=contrat,
                    date_paiement__year=expected_payment_date.year,
                    date_paiement__month=expected_payment_date.month,
                    statut='valide'
                ).exists()
                
                if not payment_exists and today > expected_payment_date:
                    # Ajouter le contrat s'il n'est pas déjà dans la liste
                    if contrat not in overdue_contracts:
                        overdue_contracts.append(contrat)
                    break  # Un seul retard par contrat suffit
        
        return overdue_contracts
    
    def _get_months_to_check(self, today, overdue_date):
        """Déterminer quels mois vérifier pour les retards"""
        months_to_check = []
        
        # Si on est dans les 5 premiers jours du mois, vérifier le mois précédent
        if today.day <= 5:
            # Ajouter le mois précédent
            if today.month == 1:
                previous_month = 12
                previous_year = today.year - 1
            else:
                previous_month = today.month - 1
                previous_year = today.year
            
            months_to_check.append(datetime(previous_year, previous_month, 1).date())
        
        # Toujours vérifier le mois en cours
        months_to_check.append(datetime(today.year, today.month, 1).date())
        
        return months_to_check
    
    def _send_overdue_notification(self, contrat, overdue_date):
        """Envoyer une notification de retard pour un contrat"""
        from utilisateurs.models import Utilisateur
        
        # Déterminer le destinataire
        recipient = None
        if contrat.locataire and contrat.locataire.cree_par:
            recipient = contrat.locataire.cree_par
        elif contrat.propriete and contrat.propriete.bailleur and contrat.propriete.bailleur.cree_par:
            recipient = contrat.propriete.bailleur.cree_par
        else:
            # Utiliser le premier utilisateur administrateur disponible
            recipient = Utilisateur.objects.filter(is_staff=True).first()
        
        if not recipient:
            logger.warning(f"No recipient found for contract {contrat.id}")
            return
        
        # Créer la notification
        notification = Notification.create_notification(
            recipient=recipient,
            type='payment_overdue',
            title='Paiement de loyer en retard',
            message=f'Votre paiement de loyer pour {contrat.propriete.titre} est en retard depuis le {overdue_date.strftime("%d/%m/%Y")}. Veuillez régulariser votre situation.',
            priority='urgent',
            content_object=contrat
        )
        
        # Vérifier les préférences SMS
        preferences, created = NotificationPreference.objects.get_or_create(
            user=recipient
        )
        
        if preferences.sms_notifications and preferences.payment_overdue_sms and preferences.phone_number:
            # Envoyer le SMS
            message = self._format_sms_message(contrat, overdue_date)
            self.sms_service.send_sms(
                phone_number=preferences.phone_number,
                message=message,
                notification_id=notification.id,
                user=recipient
            )
            
            # Marquer la notification comme envoyée par SMS
            notification.is_sent_sms = True
            notification.save()
    
    def _format_sms_message(self, contrat, overdue_date):
        """Formater le message SMS"""
        montant = contrat.loyer_mensuel or 0
        return (
            f"URGENT: Votre loyer de {montant} F CFA pour {contrat.propriete.titre} "
            f"est en retard depuis le {overdue_date.strftime('%d/%m/%Y')}. "
            f"Veuillez régulariser rapidement. "
            f"Contact: {getattr(settings, 'COMPANY_PHONE', '')}"
        )


def send_monthly_overdue_notifications():
    """
    Fonction à appeler via une tâche cron pour envoyer les notifications mensuelles
    """
    try:
        service = PaymentOverdueService()
        count = service.check_overdue_payments()
        
        return {
            'success': True,
            'count': count,
            'message': f'{count} notification(s) de retard envoyée(s) avec succès'
        }
    except Exception as e:
        logger.error(f"Error in send_monthly_overdue_notifications: {e}")
        return {
            'success': False,
            'count': 0,
            'message': f'Erreur lors de l\'envoi des notifications : {str(e)}'
        } 