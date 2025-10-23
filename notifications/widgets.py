"""
Widgets pour les numéros de téléphone du Burkina Faso
"""
from django import forms
from django.utils.translation import gettext_lazy as _


class BurkinaFasoPhoneWidget(forms.TextInput):
    """
    Widget pour les numéros de téléphone du Burkina Faso avec formatage automatique
    """
    template_name = 'notifications/widgets/burkina_faso_phone.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'placeholder': '+226 XX XX XX XX',
            'pattern': r'\+226\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}',
            'title': _('Format: +226 XX XX XX XX'),
            'class': 'form-control burkina-phone-input',
            'maxlength': '17',  # +226 XX XX XX XX = 17 caractères
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        """
        Formate la valeur pour l'affichage
        """
        if not value:
            return value
        
        # Si c'est déjà formaté, le garder
        if value.startswith('+226') and ' ' in value:
            return value
        
        # Formater avec des espaces
        cleaned = value.replace(' ', '').replace('-', '')
        if cleaned.startswith('+226') and len(cleaned) == 12:
            # +226XXXXXXXX -> +226 XX XX XX XX
            number = cleaned[4:]  # Enlever +226
            return f"+226 {number[:2]} {number[2:4]} {number[4:6]} {number[6:8]}"
        
        return value


class BurkinaFasoPhoneField(forms.CharField):
    """
    Champ de formulaire pour les numéros de téléphone du Burkina Faso
    """
    widget = BurkinaFasoPhoneWidget
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 17)
        kwargs.setdefault('help_text', _('Format: +226 XX XX XX XX'))
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        """
        Nettoie et valide le numéro de téléphone
        """
        value = super().clean(value)
        if not value:
            return value
        
        from .validators import clean_phone_number
        return clean_phone_number(value)


