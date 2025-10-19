"""
Validateurs de sécurité pour les formulaires Django
"""
import re
import html
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils.html import strip_tags


class SecurityValidators:
    """Classe contenant tous les validateurs de sécurité"""
    
    @staticmethod
    def validate_phone_international(value):
        """Valide un numéro de téléphone au format international"""
        if not value:
            return value
            
        # Nettoyer le numéro
        clean_number = re.sub(r'[\s\-\.\(\)]', '', str(value))
        
        # Pattern pour téléphone international
        pattern = r'^(\+?[1-9]\d{0,3})?[1-9]\d{7,14}$'
        
        if not re.match(pattern, clean_number):
            raise ValidationError(
                _("Format de téléphone invalide. Utilisez le format international "
                  "(ex: +226 70 12 34 56 ou 22670123456)"),
                code='invalid_phone'
            )
        
        # Vérifier la longueur
        if len(clean_number) < 8:
            raise ValidationError(
                _("Le numéro de téléphone doit contenir au moins 8 chiffres."),
                code='phone_too_short'
            )
        
        if len(clean_number) > 15:
            raise ValidationError(
                _("Le numéro de téléphone ne peut pas dépasser 15 chiffres."),
                code='phone_too_long'
            )
        
        return clean_number
    
    @staticmethod
    def validate_text_security(value):
        """Valide un texte avec des règles de sécurité anti-XSS"""
        if not value:
            return value
        
        value = str(value)
        
        # Détecter les tentatives XSS
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'on\w+\s*=',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                raise ValidationError(
                    _("Contenu suspect détecté. Caractères non autorisés."),
                    code='xss_attempt'
                )
        
        # Détecter les injections SQL
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_',
            r'xp_',
            r'--',
            r'/\*.*?\*/',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    _("Contenu suspect détecté. Caractères non autorisés."),
                    code='sql_injection_attempt'
                )
        
        # Nettoyer le texte
        cleaned_value = html.escape(value)
        
        return cleaned_value
    
    @staticmethod
    def validate_numeric_security(value):
        """Valide un nombre avec des règles de sécurité"""
        if value is None or value == '':
            return value
        
        try:
            # Convertir en float pour valider
            numeric_value = float(str(value))
            
            # Vérifier les limites
            if numeric_value < 0:
                raise ValidationError(
                    _("La valeur ne peut pas être négative."),
                    code='negative_value'
                )
            
            if numeric_value > 999999999.99:
                raise ValidationError(
                    _("La valeur est trop élevée."),
                    code='value_too_high'
                )
            
            # Vérifier les décimales (max 2)
            if '.' in str(value):
                decimal_part = str(value).split('.')[1]
                if len(decimal_part) > 2:
                    raise ValidationError(
                        _("Maximum 2 décimales autorisées."),
                        code='too_many_decimals'
                    )
            
            return numeric_value
            
        except ValueError:
            raise ValidationError(
                _("Valeur numérique invalide."),
                code='invalid_numeric'
            )
    
    @staticmethod
    def validate_date_security(value):
        """Valide une date avec des règles de sécurité"""
        if not value:
            return value
        
        from datetime import datetime, date
        
        if isinstance(value, str):
            # Vérifier le format de date
            date_patterns = [
                r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                r'^\d{2}/\d{2}/\d{4}$',  # DD/MM/YYYY
                r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
            ]
            
            valid_format = False
            for pattern in date_patterns:
                if re.match(pattern, value):
                    valid_format = True
                    break
            
            if not valid_format:
                raise ValidationError(
                    _("Format de date invalide. Utilisez DD/MM/YYYY ou YYYY-MM-DD."),
                    code='invalid_date_format'
                )
        
        # Vérifier que la date n'est pas dans le futur (pour certaines validations)
        if isinstance(value, (datetime, date)):
            from django.utils import timezone
            now = timezone.now().date()
            if value > now:
                raise ValidationError(
                    _("La date ne peut pas être dans le futur."),
                    code='future_date'
                )
        
        return value
    
    @staticmethod
    def validate_email_security(value):
        """Valide un email avec des règles de sécurité"""
        if not value or (isinstance(value, str) and value.strip() == ''):
            return value
            
        # Pattern email plus flexible et robuste
        # Accepte les caractères spéciaux courants dans les emails
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._+-]*[a-zA-Z0-9])?@([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$'
        
        # Vérification de base avec un pattern plus permissif
        basic_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        
        if not re.match(basic_pattern, value):
            raise ValidationError(
                _("Format d'email invalide. Format attendu : nom@domaine.com"),
                code='invalid_email'
            )
        
        # Vérifications supplémentaires pour les cas spéciaux
        if '..' in value:  # Double point
            raise ValidationError(
                _("Format d'email invalide. Caractères consécutifs non autorisés."),
                code='invalid_email'
            )
        
        # Vérifications supplémentaires pour les caractères autorisés
        if not re.match(pattern, value):
            raise ValidationError(
                _("Format d'email invalide. Caractères non autorisés détectés."),
                code='invalid_email'
            )
        
        # Vérifier la longueur
        if len(value) > 254:
            raise ValidationError(
                _("L'adresse email ne peut pas dépasser 254 caractères."),
                code='email_too_long'
            )
        
        # Vérifier les caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')']
        if any(char in value for char in dangerous_chars):
            raise ValidationError(
                _("L'adresse email contient des caractères non autorisés."),
                code='email_dangerous_chars'
            )
        
        return value
    
    @staticmethod
    def validate_password_strength(value):
        """Valide la force d'un mot de passe"""
        if not value:
            return value
        
        errors = []
        
        # Longueur minimale
        if len(value) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères.")
        
        # Longueur maximale
        if len(value) > 128:
            errors.append("Le mot de passe ne peut pas dépasser 128 caractères.")
        
        # Au moins une majuscule
        if not re.search(r'[A-Z]', value):
            errors.append("Le mot de passe doit contenir au moins une majuscule.")
        
        # Au moins une minuscule
        if not re.search(r'[a-z]', value):
            errors.append("Le mot de passe doit contenir au moins une minuscule.")
        
        # Au moins un chiffre
        if not re.search(r'\d', value):
            errors.append("Le mot de passe doit contenir au moins un chiffre.")
        
        # Au moins un caractère spécial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial.")
        
        # Vérifier les mots de passe communs
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if value.lower() in common_passwords:
            errors.append("Ce mot de passe est trop commun. Choisissez un mot de passe plus sécurisé.")
        
        if errors:
            raise ValidationError(errors, code='weak_password')
        
        return value
    
    @staticmethod
    def validate_name_security(value):
        """Valide un nom/prénom avec des règles de sécurité"""
        if not value:
            return value
        
        # Nettoyer les espaces
        clean_value = value.strip()
        
        # Vérifier la longueur
        if len(clean_value) < 2:
            raise ValidationError(
                _("Le nom doit contenir au moins 2 caractères."),
                code='name_too_short'
            )
        
        if len(clean_value) > 50:
            raise ValidationError(
                _("Le nom ne peut pas dépasser 50 caractères."),
                code='name_too_long'
            )
        
        # Vérifier les caractères autorisés (lettres, espaces, tirets, apostrophes)
        pattern = r'^[a-zA-ZÀ-ÿ\s\-\']+$'
        if not re.match(pattern, clean_value):
            raise ValidationError(
                _("Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes."),
                code='invalid_name_chars'
            )
        
        # Vérifier les caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '[', ']', '{', '}']
        if any(char in clean_value for char in dangerous_chars):
            raise ValidationError(
                _("Le nom contient des caractères non autorisés."),
                code='name_dangerous_chars'
            )
        
        return clean_value
    
    @staticmethod
    def validate_username_security(value):
        """Valide un nom d'utilisateur avec des règles de sécurité"""
        if not value:
            return value
        
        # Vérifier la longueur
        if len(value) < 3:
            raise ValidationError(
                _("Le nom d'utilisateur doit contenir au moins 3 caractères."),
                code='username_too_short'
            )
        
        if len(value) > 30:
            raise ValidationError(
                _("Le nom d'utilisateur ne peut pas dépasser 30 caractères."),
                code='username_too_long'
            )
        
        # Vérifier les caractères autorisés (lettres, chiffres, tirets, underscores)
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, value):
            raise ValidationError(
                _("Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores."),
                code='invalid_username_chars'
            )
        
        # Vérifier qu'il ne commence pas par un chiffre
        if value[0].isdigit():
            raise ValidationError(
                _("Le nom d'utilisateur ne peut pas commencer par un chiffre."),
                code='username_starts_with_digit'
            )
        
        return value


# Validateurs prêts à l'emploi
phone_validator = RegexValidator(
    regex=r'^(\+?[1-9]\d{0,3})?[1-9]\d{7,14}$',
    message="Format de téléphone invalide. Utilisez le format international.",
    code='invalid_phone'
)

email_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    message="Format d'email invalide.",
    code='invalid_email'
)

name_validator = RegexValidator(
    regex=r'^[a-zA-ZÀ-ÿ\s\-\']+$',
    message="Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes.",
    code='invalid_name'
)

username_validator = RegexValidator(
    regex=r'^[a-zA-Z][a-zA-Z0-9_-]*$',
    message="Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores, et doit commencer par une lettre.",
    code='invalid_username'
)
