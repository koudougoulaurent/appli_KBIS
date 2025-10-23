"""
Validateurs pour les numéros de téléphone du Burkina Faso
Format: +226 XX XX XX XX
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_burkina_faso_phone(value):
    """
    Valide le format du numéro de téléphone du Burkina Faso
    Formats acceptés:
    - +226 XX XX XX XX
    - +226XXXXXXXX
    - 226 XX XX XX XX
    - 226XXXXXXXX
    """
    if not value:
        return
    
    # Nettoyer le numéro
    cleaned = re.sub(r'[^\d+]', '', str(value))
    
    # Patterns acceptés
    patterns = [
        r'^\+226\d{8}$',  # +226XXXXXXXX
        r'^226\d{8}$',    # 226XXXXXXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return
    
    # Si aucun pattern ne correspond, essayer de formater
    if cleaned.startswith('+226') and len(cleaned) == 12:
        return
    elif cleaned.startswith('226') and len(cleaned) == 11:
        return
    elif len(cleaned) == 8:  # Juste les 8 chiffres
        return
    
    raise ValidationError(
        _('Format de numéro de téléphone invalide pour le Burkina Faso. '
          'Utilisez le format: +226 XX XX XX XX ou +226XXXXXXXX')
    )


def format_burkina_faso_phone(value):
    """
    Formate un numéro de téléphone du Burkina Faso
    """
    if not value:
        return value
    
    # Nettoyer le numéro
    cleaned = re.sub(r'[^\d+]', '', str(value))
    
    # Si le numéro commence par +226, le garder tel quel
    if cleaned.startswith('+226') and len(cleaned) == 12:
        return cleaned
    
    # Si le numéro commence par 226, ajouter le +
    if cleaned.startswith('226') and len(cleaned) == 11:
        return '+' + cleaned
    
    # Si c'est juste 8 chiffres, ajouter +226
    if len(cleaned) == 8 and cleaned.isdigit():
        return '+226' + cleaned
    
    # Si c'est 10 chiffres (avec 0 au début), enlever le 0 et ajouter +226
    if len(cleaned) == 10 and cleaned.startswith('0'):
        return '+226' + cleaned[1:]
    
    return value


def clean_phone_number(value):
    """
    Nettoie et formate un numéro de téléphone du Burkina Faso
    """
    if not value:
        return value
    
    # Nettoyer
    cleaned = re.sub(r'[^\d+]', '', str(value))
    
    # Appliquer le formatage
    formatted = format_burkina_faso_phone(cleaned)
    
    # Valider
    validate_burkina_faso_phone(formatted)
    
    return formatted


