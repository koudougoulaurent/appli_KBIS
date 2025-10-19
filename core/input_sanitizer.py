"""
Système de sanitisation des entrées utilisateur
"""
import re
import html
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Any, Dict, List, Union
from .sql_security import SQLInjectionProtection


class InputSanitizer:
    """Classe pour la sanitisation des entrées utilisateur"""
    
    # Patterns de caractères dangereux
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Scripts JavaScript
        r'javascript:',  # URLs JavaScript
        r'vbscript:',  # URLs VBScript
        r'on\w+\s*=',  # Événements HTML
        r'<iframe[^>]*>.*?</iframe>',  # Iframes
        r'<object[^>]*>.*?</object>',  # Objects
        r'<embed[^>]*>.*?</embed>',  # Embeds
        r'<form[^>]*>.*?</form>',  # Forms
        r'<input[^>]*>',  # Inputs
        r'<textarea[^>]*>.*?</textarea>',  # Textareas
        r'<select[^>]*>.*?</select>',  # Selects
        r'<button[^>]*>.*?</button>',  # Buttons
        r'<link[^>]*>',  # Links
        r'<meta[^>]*>',  # Meta tags
        r'<style[^>]*>.*?</style>',  # Styles
        r'expression\s*\(',  # CSS expressions
        r'url\s*\(',  # CSS URLs
        r'@import',  # CSS imports
        r'<![CDATA\[',  # CDATA sections
        r'<!DOCTYPE',  # DOCTYPE declarations
        r'<\?xml',  # XML declarations
        r'<\?php',  # PHP code
        r'<%',  # ASP/JSP code
        r'<%=',  # ASP/JSP expressions
        r'<%.*?%>',  # ASP/JSP blocks
    ]
    
    # Caractères de contrôle à supprimer
    CONTROL_CHARS = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]'
    
    # Caractères HTML à échapper
    HTML_ESCAPE_MAP = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }
    
    @classmethod
    def sanitize_string(cls, input_string: str, max_length: int = 1000) -> str:
        """
        Sanitise une chaîne de caractères
        
        Args:
            input_string: La chaîne à sanitiser
            max_length: Longueur maximale autorisée
            
        Returns:
            str: La chaîne sanitisée
        """
        if not input_string or not isinstance(input_string, str):
            return ""
        
        # Supprimer les caractères de contrôle
        sanitized = re.sub(cls.CONTROL_CHARS, '', input_string)
        
        # Limiter la longueur
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Supprimer les patterns dangereux
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Échapper les caractères HTML
        sanitized = cls._escape_html(sanitized)
        
        # Supprimer les espaces en début/fin
        sanitized = sanitized.strip()
        
        return sanitized
    
    @classmethod
    def _escape_html(cls, text: str) -> str:
        """Échappe les caractères HTML"""
        for char, escaped in cls.HTML_ESCAPE_MAP.items():
            text = text.replace(char, escaped)
        return text
    
    @classmethod
    def sanitize_integer(cls, value: Any) -> int:
        """
        Sanitise une valeur entière
        
        Args:
            value: La valeur à sanitiser
            
        Returns:
            int: La valeur entière sanitisée
            
        Raises:
            ValidationError: Si la valeur n'est pas un entier valide
        """
        if value is None:
            return None
        
        try:
            # Convertir en chaîne et nettoyer
            str_value = str(value).strip()
            
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(str_value):
                raise ValidationError(_("Valeur suspecte détectée"))
            
            # Vérifier que c'est un entier
            if not re.match(r'^-?\d+$', str_value):
                raise ValidationError(_("Valeur entière invalide"))
            
            return int(str_value)
        
        except (ValueError, TypeError):
            raise ValidationError(_("Valeur entière invalide"))
    
    @classmethod
    def sanitize_decimal(cls, value: Any) -> float:
        """
        Sanitise une valeur décimale
        
        Args:
            value: La valeur à sanitiser
            
        Returns:
            float: La valeur décimale sanitisée
            
        Raises:
            ValidationError: Si la valeur n'est pas un décimal valide
        """
        if value is None:
            return None
        
        try:
            # Convertir en chaîne et nettoyer
            str_value = str(value).strip()
            
            # Vérifier l'injection SQL
            if SQLInjectionProtection.detect_sql_injection(str_value):
                raise ValidationError(_("Valeur suspecte détectée"))
            
            # Vérifier que c'est un décimal
            if not re.match(r'^-?\d+(\.\d+)?$', str_value):
                raise ValidationError(_("Valeur décimale invalide"))
            
            return float(str_value)
        
        except (ValueError, TypeError):
            raise ValidationError(_("Valeur décimale invalide"))
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Sanitise une adresse email
        
        Args:
            email: L'email à sanitiser
            
        Returns:
            str: L'email sanitisé
            
        Raises:
            ValidationError: Si l'email n'est pas valide
        """
        if not email:
            return ""
        
        # Nettoyer l'email
        email = email.strip().lower()
        
        # Vérifier l'injection SQL
        if SQLInjectionProtection.detect_sql_injection(email):
            raise ValidationError(_("Email suspect détecté"))
        
        # Vérifier le format email avec validation flexible
        basic_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(basic_pattern, cleaned_email):
            raise ValidationError(_("Format d'email invalide"))
        
        # Vérification plus stricte pour les caractères autorisés
        strict_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._+-]*[a-zA-Z0-9])?@([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$'
        if not re.match(strict_pattern, cleaned_email):
            raise ValidationError(_("Format d'email invalide"))
        
        # Vérifier les doubles points
        if '..' in cleaned_email:
            raise ValidationError(_("Format d'email invalide"))
        
        # Limiter la longueur
        if len(email) > 254:
            raise ValidationError(_("Email trop long"))
        
        return email
    
    @classmethod
    def sanitize_phone(cls, phone: str) -> str:
        """
        Sanitise un numéro de téléphone
        
        Args:
            phone: Le téléphone à sanitiser
            
        Returns:
            str: Le téléphone sanitisé
            
        Raises:
            ValidationError: Si le téléphone n'est pas valide
        """
        if not phone:
            return ""
        
        # Nettoyer le téléphone
        phone = phone.strip()
        
        # Vérifier l'injection SQL
        if SQLInjectionProtection.detect_sql_injection(phone):
            raise ValidationError(_("Téléphone suspect détecté"))
        
        # Supprimer les caractères non numériques sauf + au début
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # Vérifier le format
        phone_pattern = r'^(\+?[1-9]\d{0,3})?[1-9]\d{7,14}$'
        if not re.match(phone_pattern, cleaned_phone):
            raise ValidationError(_("Format de téléphone invalide"))
        
        return cleaned_phone
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitise un dictionnaire de données
        
        Args:
            data: Le dictionnaire à sanitiser
            
        Returns:
            Dict: Le dictionnaire sanitisé
        """
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Sanitiser la clé
            clean_key = cls.sanitize_string(str(key), 100)
            
            # Sanitiser la valeur selon son type
            if isinstance(value, str):
                clean_value = cls.sanitize_string(value)
            elif isinstance(value, int):
                clean_value = cls.sanitize_integer(value)
            elif isinstance(value, float):
                clean_value = cls.sanitize_decimal(value)
            elif isinstance(value, dict):
                clean_value = cls.sanitize_dict(value)
            elif isinstance(value, list):
                clean_value = cls.sanitize_list(value)
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    @classmethod
    def sanitize_list(cls, data: List[Any]) -> List[Any]:
        """
        Sanitise une liste de données
        
        Args:
            data: La liste à sanitiser
            
        Returns:
            List: La liste sanitisée
        """
        if not isinstance(data, list):
            return []
        
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(cls.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized
