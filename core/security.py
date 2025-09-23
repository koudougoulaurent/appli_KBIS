"""
Module de sécurité pour KBIS IMMOBILIER
Protection des données sensibles immobilières
"""
import re
import hashlib
import secrets
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('security')


class SecurityValidator:
    """Validateur de sécurité pour les données immobilières"""
    
    @staticmethod
    def validate_phone_number(phone):
        """Valider un numéro de téléphone"""
        if not phone:
            return True
        
        # Pattern pour numéros français et internationaux
        phone_pattern = r'^(\+33|0)[1-9](\d{8})$'
        if not re.match(phone_pattern, phone.replace(' ', '')):
            raise ValidationError(_('Format de numéro de téléphone invalide'))
        return True
    
    @staticmethod
    def validate_email(email):
        """Valider un email avec sécurité renforcée"""
        if not email:
            return True
        
        validator = EmailValidator()
        validator(email)
        
        # Vérifier les domaines suspects
        suspicious_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1].lower()
        if domain in suspicious_domains:
            raise ValidationError(_('Adresse email temporaire non autorisée'))
        
        return True
    
    @staticmethod
    def validate_iban(iban):
        """Valider un IBAN"""
        if not iban:
            return True
        
        # Nettoyer l'IBAN
        iban = iban.replace(' ', '').upper()
        
        # Vérifier la longueur (entre 15 et 34 caractères)
        if len(iban) < 15 or len(iban) > 34:
            raise ValidationError(_('IBAN invalide'))
        
        # Vérifier le format (2 lettres + 2 chiffres + caractères alphanumériques)
        if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', iban):
            raise ValidationError(_('Format IBAN invalide'))
        
        return True
    
    @staticmethod
    def validate_amount(amount):
        """Valider un montant financier"""
        if amount is None:
            return True
        
        try:
            amount = float(amount)
            if amount < 0:
                raise ValidationError(_('Le montant ne peut pas être négatif'))
            if amount > 999999999.99:
                raise ValidationError(_('Montant trop élevé'))
        except (ValueError, TypeError):
            raise ValidationError(_('Montant invalide'))
        
        return True
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Valider une plage de dates"""
        if not start_date or not end_date:
            return True
        
        if start_date >= end_date:
            raise ValidationError(_('La date de début doit être antérieure à la date de fin'))
        
        # Vérifier que les dates ne sont pas trop éloignées (max 10 ans)
        if (end_date - start_date).days > 3650:
            raise ValidationError(_('La plage de dates ne peut pas dépasser 10 ans'))
        
        return True


class DataSanitizer:
    """Nettoyeur de données pour prévenir les injections"""
    
    @staticmethod
    def sanitize_string(value):
        """Nettoyer une chaîne de caractères"""
        if not value:
            return value
        
        # Supprimer les caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', 'script', 'javascript']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        # Limiter la longueur
        return value[:1000]
    
    @staticmethod
    def sanitize_number(value):
        """Nettoyer un nombre"""
        if not value:
            return None
        
        try:
            # Supprimer tous les caractères non numériques sauf le point et la virgule
            cleaned = re.sub(r'[^\d.,]', '', str(value))
            # Remplacer la virgule par un point
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def sanitize_phone(phone):
        """Nettoyer un numéro de téléphone"""
        if not phone:
            return phone
        
        # Garder seulement les chiffres et le +
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned


class AccessControl:
    """Contrôle d'accès basé sur les rôles"""
    
    # Définir les permissions par groupe
    PERMISSIONS = {
        'ADMINISTRATION': [
            'view_utilisateur', 'add_utilisateur', 'change_utilisateur', 'delete_utilisateur',
            'view_propriete', 'add_propriete', 'change_propriete', 'delete_propriete',
            'view_contrat', 'add_contrat', 'change_contrat', 'delete_contrat',
            'view_paiement', 'add_paiement', 'change_paiement', 'delete_paiement',
        ],
        'CAISSE': [
            'view_paiement', 'add_paiement', 'change_paiement',
            'view_contrat', 'view_propriete',
            'view_utilisateur',
        ],
        'CONTROLES': [
            'view_paiement', 'view_contrat', 'view_propriete', 'view_utilisateur',
        ],
        'PRIVILEGE': [
            'view_utilisateur', 'add_utilisateur', 'change_utilisateur', 'delete_utilisateur',
            'view_propriete', 'add_propriete', 'change_propriete', 'delete_propriete',
            'view_contrat', 'add_contrat', 'change_contrat', 'delete_contrat',
            'view_paiement', 'add_paiement', 'change_paiement', 'delete_paiement',
            'view_admin', 'add_admin', 'change_admin', 'delete_admin',
        ],
    }
    
    @classmethod
    def has_permission(cls, user, permission):
        """Vérifier si un utilisateur a une permission"""
        if not user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur a le groupe approprié
        user_groups = [group.name for group in user.groups.all()]
        
        for group in user_groups:
            if group in cls.PERMISSIONS and permission in cls.PERMISSIONS[group]:
                return True
        
        return False
    
    @classmethod
    def can_access_sensitive_data(cls, user):
        """Vérifier si l'utilisateur peut accéder aux données sensibles"""
        return cls.has_permission(user, 'view_paiement') or cls.has_permission(user, 'view_contrat')


class SecurityLogger:
    """Logger de sécurité pour l'audit"""
    
    @staticmethod
    def log_login_attempt(user, ip, success=True):
        """Logger une tentative de connexion"""
        status = "SUCCESS" if success else "FAILED"
        logger.warning(f"LOGIN_{status}: User={user}, IP={ip}, Time={timezone.now()}")
    
    @staticmethod
    def log_sensitive_action(user, action, details, ip):
        """Logger une action sensible"""
        logger.warning(f"SENSITIVE_ACTION: User={user}, Action={action}, Details={details}, IP={ip}, Time={timezone.now()}")
    
    @staticmethod
    def log_security_violation(violation_type, details, ip):
        """Logger une violation de sécurité"""
        logger.error(f"SECURITY_VIOLATION: Type={violation_type}, Details={details}, IP={ip}, Time={timezone.now()}")


class PasswordSecurity:
    """Sécurité des mots de passe"""
    
    @staticmethod
    def generate_secure_password(length=12):
        """Générer un mot de passe sécurisé"""
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def validate_password_strength(password):
        """Valider la force d'un mot de passe"""
        if len(password) < 12:
            raise ValidationError(_('Le mot de passe doit contenir au moins 12 caractères'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Le mot de passe doit contenir au moins une majuscule'))
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Le mot de passe doit contenir au moins une minuscule'))
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(_('Le mot de passe doit contenir au moins un chiffre'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('Le mot de passe doit contenir au moins un caractère spécial'))
        
        return True


class DataEncryption:
    """Chiffrement des données sensibles"""
    
    @staticmethod
    def hash_sensitive_data(data):
        """Hasher des données sensibles"""
        if not data:
            return None
        
        # Utiliser SHA-256 avec un salt
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((data + salt).encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    @staticmethod
    def verify_hashed_data(data, hashed_data):
        """Vérifier des données hachées"""
        if not data or not hashed_data:
            return False
        
        try:
            salt, hashed = hashed_data.split(':')
            return hashlib.sha256((data + salt).encode()).hexdigest() == hashed
        except ValueError:
            return False
