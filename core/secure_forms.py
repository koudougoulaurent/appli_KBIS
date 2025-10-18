"""
Formulaires sécurisés avec protection contre les injections SQL et XSS
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .sql_security import SQLInjectionProtection
from .input_sanitizer import InputSanitizer


class SecureFormMixin:
    """Mixin pour sécuriser les formulaires"""
    
    def clean(self):
        """Validation globale sécurisée du formulaire"""
        cleaned_data = super().clean()
        
        # Sanitiser tous les champs de type string
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                try:
                    cleaned_data[field_name] = InputSanitizer.sanitize_string(value)
                except ValidationError as e:
                    self.add_error(field_name, e)
        
        return cleaned_data
    
    def clean_field(self, field_name, value):
        """Méthode utilitaire pour nettoyer un champ"""
        if not value:
            return value
        
        # Vérifier l'injection SQL
        if SQLInjectionProtection.detect_sql_injection(str(value)):
            raise ValidationError(_("Caractères non autorisés détectés"))
        
        # Sanitiser la valeur
        if isinstance(value, str):
            return InputSanitizer.sanitize_string(value)
        
        return value


class SecureCharField(forms.CharField):
    """Champ CharField sécurisé"""
    
    def clean(self, value):
        value = super().clean(value)
        
        if value:
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(value):
                raise ValidationError(_("Caractères non autorisés détectés"))
            
            # Sanitiser la valeur
            value = InputSanitizer.sanitize_string(value)
        
        return value


class SecureTextField(forms.CharField):
    """Champ TextField sécurisé"""
    
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = forms.Textarea
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        value = super().clean(value)
        
        if value:
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(value):
                raise ValidationError(_("Caractères non autorisés détectés"))
            
            # Sanitiser la valeur
            value = InputSanitizer.sanitize_string(value, max_length=5000)
        
        return value


class SecureEmailField(forms.EmailField):
    """Champ EmailField sécurisé"""
    
    def clean(self, value):
        value = super().clean(value)
        
        if value:
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(value):
                raise ValidationError(_("Caractères non autorisés détectés"))
            
            # Sanitiser l'email
            value = InputSanitizer.sanitize_email(value)
        
        return value


class SecureIntegerField(forms.IntegerField):
    """Champ IntegerField sécurisé"""
    
    def clean(self, value):
        value = super().clean(value)
        
        if value is not None:
            # Sanitiser l'entier
            value = InputSanitizer.sanitize_integer(value)
        
        return value


class SecureDecimalField(forms.DecimalField):
    """Champ DecimalField sécurisé"""
    
    def clean(self, value):
        value = super().clean(value)
        
        if value is not None:
            # Sanitiser le décimal
            value = InputSanitizer.sanitize_decimal(value)
        
        return value


class SecurePhoneField(forms.CharField):
    """Champ téléphone sécurisé"""
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 20
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        value = super().clean(value)
        
        if value:
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(value):
                raise ValidationError(_("Caractères non autorisés détectés"))
            
            # Sanitiser le téléphone
            value = InputSanitizer.sanitize_phone(value)
        
        return value


class SecureChoiceField(forms.ChoiceField):
    """Champ ChoiceField sécurisé"""
    
    def clean(self, value):
        value = super().clean(value)
        
        if value:
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(str(value)):
                raise ValidationError(_("Caractères non autorisés détectés"))
            
            # Sanitiser la valeur
            value = InputSanitizer.sanitize_string(str(value))
        
        return value


class SecureModelForm(forms.ModelForm, SecureFormMixin):
    """FormModel sécurisé"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remplacer les champs par des versions sécurisées
        self._replace_fields_with_secure_versions()
    
    def _replace_fields_with_secure_versions(self):
        """Remplace les champs par des versions sécurisées"""
        field_mapping = {
            forms.CharField: SecureCharField,
            forms.EmailField: SecureEmailField,
            forms.IntegerField: SecureIntegerField,
            forms.DecimalField: SecureDecimalField,
            forms.ChoiceField: SecureChoiceField,
        }
        
        for field_name, field in self.fields.items():
            field_class = type(field)
            if field_class in field_mapping:
                # Créer une nouvelle instance du champ sécurisé
                secure_field_class = field_mapping[field_class]
                secure_field = secure_field_class(
                    required=field.required,
                    label=field.label,
                    help_text=field.help_text,
                    initial=field.initial,
                    widget=field.widget,
                    error_messages=field.error_messages,
                    validators=field.validators,
                    localize=field.localize,
                    disabled=field.disabled,
                    label_suffix=field.label_suffix,
                )
                
                # Copier les attributs
                for attr in ['max_length', 'min_length', 'strip', 'empty_value']:
                    if hasattr(field, attr):
                        setattr(secure_field, attr, getattr(field, attr))
                
                self.fields[field_name] = secure_field


class SecureForm(forms.Form, SecureFormMixin):
    """Form sécurisé"""
    pass
