"""
Formulaires pour les notifications avec support du Burkina Faso
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import NotificationPreference
from .widgets import BurkinaFasoPhoneField


class NotificationPreferenceForm(forms.ModelForm):
    """
    Formulaire pour les préférences de notification avec format Burkina Faso
    """
    phone_number = BurkinaFasoPhoneField(
        required=False,
        label=_("Numéro de téléphone"),
        help_text=_("Format: +226 XX XX XX XX (Burkina Faso)")
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications',
            'browser_notifications', 
            'sms_notifications',
            'phone_number',
            'sms_provider',
            'daily_digest',
            'weekly_digest',
            # Préférences par type
            'payment_due_email',
            'payment_due_sms',
            'payment_received_email',
            'payment_received_sms',
            'payment_overdue_email',
            'payment_overdue_sms',
            'contract_expiring_email',
            'contract_expiring_sms',
            'maintenance_email',
            'maintenance_sms',
            'system_alerts_email',
            'system_alerts_sms',
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'browser_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_provider': forms.Select(attrs={'class': 'form-select'}),
            'daily_digest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weekly_digest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter des classes CSS pour les checkboxes
        for field_name in self.fields:
            if isinstance(self.fields[field_name].widget, forms.CheckboxInput):
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-check-input',
                    'data-bs-toggle': 'collapse',
                    'data-bs-target': f'#{field_name}_options'
                })
        
        # Grouper les préférences par type
        self.fieldsets = {
            'general': [
                'email_notifications',
                'browser_notifications', 
                'sms_notifications',
                'phone_number',
                'sms_provider',
            ],
            'digest': [
                'daily_digest',
                'weekly_digest',
            ],
            'payment_due': [
                'payment_due_email',
                'payment_due_sms',
            ],
            'payment_received': [
                'payment_received_email',
                'payment_received_sms',
            ],
            'payment_overdue': [
                'payment_overdue_email',
                'payment_overdue_sms',
            ],
            'contract_expiring': [
                'contract_expiring_email',
                'contract_expiring_sms',
            ],
            'maintenance': [
                'maintenance_email',
                'maintenance_sms',
            ],
            'system_alerts': [
                'system_alerts_email',
                'system_alerts_sms',
            ],
        }
    
    def clean_phone_number(self):
        """
        Validation spécifique du numéro de téléphone
        """
        phone_number = self.cleaned_data.get('phone_number')
        sms_notifications = self.cleaned_data.get('sms_notifications')
        
        # Si les SMS sont activés, le numéro est obligatoire
        if sms_notifications and not phone_number:
            raise forms.ValidationError(
                _("Le numéro de téléphone est obligatoire quand les notifications SMS sont activées.")
            )
        
        return phone_number


class TestSMSForm(forms.Form):
    """
    Formulaire pour tester l'envoi de SMS
    """
    phone_number = BurkinaFasoPhoneField(
        label=_("Numéro de téléphone"),
        help_text=_("Format: +226 XX XX XX XX"),
        required=True
    )
    message = forms.CharField(
        max_length=160,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': _('Votre message de test...')
        }),
        label=_("Message"),
        help_text=_("Maximum 160 caractères")
    )
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) > 160:
            raise forms.ValidationError(
                _("Le message ne peut pas dépasser 160 caractères.")
            )
        return message


class BulkNotificationForm(forms.Form):
    """
    Formulaire pour l'envoi de notifications en masse
    """
    RECIPIENT_CHOICES = [
        ('all', _('Tous les utilisateurs')),
        ('active_contracts', _('Utilisateurs avec contrats actifs')),
        ('overdue_payments', _('Utilisateurs avec paiements en retard')),
        ('expiring_contracts', _('Utilisateurs avec contrats expirants')),
    ]
    
    TYPE_CHOICES = [
        ('payment_overdue', _('Paiement en retard')),
        ('contract_expiring', _('Contrat expirant')),
        ('system_alert', _('Alerte système')),
        ('info', _('Information générale')),
    ]
    
    recipients = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Destinataires")
    )
    notification_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Type de notification")
    )
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_("Titre")
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control'
        }),
        label=_("Message")
    )
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Envoyer par email")
    )
    send_sms = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Envoyer par SMS")
    )
