"""
Système de protection contre les injections SQL - Version simplifiée
"""
import re
import logging
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class SQLInjectionProtection:
    """Classe principale pour la protection contre les injections SQL"""
    
    # Patterns dangereux simplifiés
    DANGEROUS_PATTERNS = [
        r'(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)',
        r'(OR|AND)\s+\d+\s*=\s*\d+',
        r'(OR|AND)\s+.*\s*=\s*.*',
        r'(--|#|/\*|\*/)',
        r'[;\'\"\\]',
        r'(OR|AND)\s+1\s*=\s*1',
        r'(OR|AND)\s+true',
        r'(OR|AND)\s+false',
        r'(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)',
        r'(CHAR|ASCII|ORD|HEX|UNHEX)\s*\(',
        r'(SLEEP|BENCHMARK|WAITFOR)\s*\(',
        r'\\[x0-9a-fA-F]{2}',
        r'\\[0-7]{3}',
        r'(CHAR|CHR)\s*\(\s*\d+\s*\)',
        r'(SYSTEM|SHELL|CMD|POWERSHELL|BASH)',
        r'(COPY|MOVE|DEL|RM|RMDIR|MKDIR)',
    ]
    
    @classmethod
    def detect_sql_injection(cls, input_string):
        """Détecte une tentative d'injection SQL"""
        if not input_string or not isinstance(input_string, str):
            return False
        
        input_upper = input_string.upper()
        
        # Vérifier les patterns dangereux
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                logger.warning(f"SQL Injection detectee: {pattern} dans '{input_string}'")
                return True
        
        return False
    
    @classmethod
    def sanitize_input(cls, input_value, input_type='string'):
        """Nettoie une entrée utilisateur"""
        if input_value is None:
            return None
        
        str_value = str(input_value).strip()
        
        # Détecter les injections SQL
        if cls.detect_sql_injection(str_value):
            raise ValidationError(_("Entree suspecte detectee. Caracteres non autorises."))
        
        return str_value


class InputSanitizer:
    """Classe pour la sanitisation des entrées utilisateur"""
    
    @classmethod
    def sanitize_string(cls, input_string, max_length=1000):
        """Sanitise une chaîne de caractères"""
        if not input_string or not isinstance(input_string, str):
            return ""
        
        # Supprimer les caractères de contrôle
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', input_string)
        
        # Limiter la longueur
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Échapper les caractères HTML
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        sanitized = sanitized.replace('/', '&#x2F;')
        
        return sanitized.strip()
    
    @classmethod
    def sanitize_integer(cls, value):
        """Sanitise une valeur entière"""
        if value is None:
            return None
        
        try:
            str_value = str(value).strip()
            
            if SQLInjectionProtection.detect_sql_injection(str_value):
                raise ValidationError(_("Valeur suspecte detectee"))
            
            if not re.match(r'^-?\d+$', str_value):
                raise ValidationError(_("Valeur entiere invalide"))
            
            return int(str_value)
        except (ValueError, TypeError):
            raise ValidationError(_("Valeur entiere invalide"))
    
    @classmethod
    def sanitize_decimal(cls, value):
        """Sanitise une valeur décimale"""
        if value is None:
            return None
        
        try:
            str_value = str(value).strip()
            
            if SQLInjectionProtection.detect_sql_injection(str_value):
                raise ValidationError(_("Valeur suspecte detectee"))
            
            if not re.match(r'^-?\d+(\.\d+)?$', str_value):
                raise ValidationError(_("Valeur decimale invalide"))
            
            return float(str_value)
        except (ValueError, TypeError):
            raise ValidationError(_("Valeur decimale invalide"))
    
    @classmethod
    def sanitize_email(cls, email):
        """Sanitise une adresse email"""
        if not email:
            return ""
        
        email = email.strip().lower()
        
        if SQLInjectionProtection.detect_sql_injection(email):
            raise ValidationError(_("Email suspect detecte"))
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_("Format d'email invalide"))
        
        if len(email) > 254:
            raise ValidationError(_("Email trop long"))
        
        return email
    
    @classmethod
    def sanitize_phone(cls, phone):
        """Sanitise un numéro de téléphone"""
        if not phone:
            return ""
        
        phone = phone.strip()
        
        if SQLInjectionProtection.detect_sql_injection(phone):
            raise ValidationError(_("Telephone suspect detecte"))
        
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        phone_pattern = r'^(\+?[1-9]\d{0,3})?[1-9]\d{7,14}$'
        if not re.match(phone_pattern, cleaned_phone):
            raise ValidationError(_("Format de telephone invalide"))
        
        return cleaned_phone
