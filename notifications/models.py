from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .validators import validate_burkina_faso_phone


class Notification(models.Model):
    """
    Modèle pour gérer les notifications système
    """
    TYPE_CHOICES = [
        ('payment_due', 'Échéance de paiement'),
        ('payment_received', 'Paiement reçu'),
        ('payment_overdue', 'Paiement en retard'),
        ('contract_expiring', 'Contrat expirant'),
        ('maintenance_request', 'Demande de maintenance'),
        ('maintenance_completed', 'Maintenance terminée'),
        ('system_alert', 'Alerte système'),
        ('info', 'Information générale'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]
    
    # Champs de base
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Destinataire
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Référence générique à un objet (contrat, paiement, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # État de la notification
    is_read = models.BooleanField(default=False)
    is_sent_email = models.BooleanField(default=False)
    is_sent_sms = models.BooleanField(default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_unread(self):
        """Marquer la notification comme non lue"""
        self.is_read = False
        self.read_at = None
        self.save()
    
    @classmethod
    def create_notification(cls, recipient, type, title, message, priority='medium', 
                          content_object=None):
        """Méthode utilitaire pour créer une notification"""
        notification = cls.objects.create(
            recipient=recipient,
            type=type,
            title=title,
            message=message,
            priority=priority,
            content_object=content_object
        )
        return notification
    
    @classmethod
    def get_unread_count(cls, user):
        """Obtenir le nombre de notifications non lues pour un utilisateur"""
        return cls.objects.filter(recipient=user, is_read=False).count()
    
    @classmethod
    def get_user_notifications(cls, user, limit=None):
        """Obtenir les notifications d'un utilisateur"""
        queryset = cls.objects.filter(recipient=user)
        if limit:
            queryset = queryset[:limit]
        return queryset


class NotificationPreference(models.Model):
    """
    Préférences de notification par utilisateur
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Types de notifications activés
    email_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Préférences par type
    payment_due_email = models.BooleanField(default=True)
    payment_received_email = models.BooleanField(default=True)
    payment_overdue_email = models.BooleanField(default=True)
    contract_expiring_email = models.BooleanField(default=True)
    maintenance_email = models.BooleanField(default=True)
    system_alerts_email = models.BooleanField(default=True)
    
    # Préférences SMS
    payment_due_sms = models.BooleanField(default=False)
    payment_received_sms = models.BooleanField(default=False)
    payment_overdue_sms = models.BooleanField(default=True)
    contract_expiring_sms = models.BooleanField(default=False)
    maintenance_sms = models.BooleanField(default=False)
    system_alerts_sms = models.BooleanField(default=False)
    
    # Fréquence des notifications
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=False)
    
    # Configuration SMS
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[validate_burkina_faso_phone],
        help_text="Format: +226 XX XX XX XX"
    )
    sms_provider = models.CharField(max_length=50, default='twilio', choices=[
        ('twilio', 'Twilio'),
        ('nexmo', 'Nexmo/Vonage'),
        ('custom', 'Fournisseur personnalisé'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Préférence de notification'
        verbose_name_plural = 'Préférences de notification'
    
    def __str__(self):
        return f"Préférences de {self.user.username}"
    
    def get_email_preferences(self):
        """Obtenir les types de notifications activés par email"""
        return {
            'payment_due': self.payment_due_email,
            'payment_received': self.payment_received_email,
            'payment_overdue': self.payment_overdue_email,
            'contract_expiring': self.contract_expiring_email,
            'maintenance': self.maintenance_email,
            'system_alerts': self.system_alerts_email,
        }
    
    def get_sms_preferences(self):
        """Obtenir les types de notifications activés par SMS"""
        return {
            'payment_due': self.payment_due_sms,
            'payment_received': self.payment_received_sms,
            'payment_overdue': self.payment_overdue_sms,
            'contract_expiring': self.contract_expiring_sms,
            'maintenance': self.maintenance_sms,
            'system_alerts': self.system_alerts_sms,
        }


class SMSNotification(models.Model):
    """
    Modèle pour gérer les notifications SMS
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyé'),
        ('delivered', 'Livré'),
        ('failed', 'Échec'),
        ('cancelled', 'Annulé'),
    ]
    
    # Référence à la notification principale
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='sms_notifications',
        null=True,
        blank=True
    )
    
    # Référence à l'utilisateur (pour les SMS sans notification)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sms_notifications',
        null=True,
        blank=True
    )
    
    # Informations SMS
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Informations du fournisseur SMS
    provider = models.CharField(max_length=50, default='twilio')
    provider_message_id = models.CharField(max_length=100, blank=True, null=True)
    provider_response = models.TextField(blank=True, null=True)
    
    # Tentatives
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification SMS'
        verbose_name_plural = 'Notifications SMS'
    
    def __str__(self):
        return f"SMS à {self.phone_number} - {self.status}"
    
    def mark_as_sent(self, provider_message_id=None, provider_response=None):
        """Marquer le SMS comme envoyé"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.attempts += 1
        if provider_message_id:
            self.provider_message_id = provider_message_id
        if provider_response:
            self.provider_response = provider_response
        self.save()
    
    def mark_as_delivered(self):
        """Marquer le SMS comme livré"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, provider_response=None):
        """Marquer le SMS comme échoué"""
        self.status = 'failed'
        self.attempts += 1
        if provider_response:
            self.provider_response = provider_response
        self.save()
    
    def can_retry(self):
        """Vérifier si on peut réessayer l'envoi"""
        return self.status in ['pending', 'failed'] and self.attempts < self.max_attempts 