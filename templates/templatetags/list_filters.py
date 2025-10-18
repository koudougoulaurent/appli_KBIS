from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Filtre pour obtenir un attribut d'un objet"""
    try:
        return getattr(obj, attr)
    except AttributeError:
        return None

@register.filter
def format_currency(value):
    """Formater une valeur en devise F CFA"""
    if value is None:
        return "-"
    try:
        return f"{float(value):,.0f} F CFA"
    except (ValueError, TypeError):
        return str(value)

@register.filter
def format_surface(value):
    """Formater une surface en m²"""
    if value is None:
        return "-"
    try:
        return f"{float(value):,.0f} m²"
    except (ValueError, TypeError):
        return str(value)

@register.filter
def format_phone(value):
    """Formater un numéro de téléphone"""
    if not value:
        return "-"
    # Nettoyer le numéro
    clean_phone = ''.join(filter(str.isdigit, str(value)))
    if len(clean_phone) >= 8:
        # Formater selon la longueur
        if len(clean_phone) == 8:
            return f"{clean_phone[:4]} {clean_phone[4:6]} {clean_phone[6:8]}"
        elif len(clean_phone) == 10:
            return f"{clean_phone[:2]} {clean_phone[2:4]} {clean_phone[4:6]} {clean_phone[6:8]} {clean_phone[8:10]}"
        else:
            return value
    return value

@register.filter
def format_date(value):
    """Formater une date"""
    if not value:
        return "-"
    try:
        return value.strftime("%d/%m/%Y")
    except AttributeError:
        return str(value)

@register.filter
def format_datetime(value):
    """Formater une date et heure"""
    if not value:
        return "-"
    try:
        return value.strftime("%d/%m/%Y %H:%M")
    except AttributeError:
        return str(value)

@register.filter
def format_status(value):
    """Formater un statut avec badge coloré"""
    if not value:
        return "-"
    
    status_map = {
        'valide': ('success', 'Validé'),
        'en_attente': ('warning', 'En attente'),
        'refuse': ('danger', 'Refusé'),
        'actif': ('success', 'Actif'),
        'inactif': ('secondary', 'Inactif'),
        'disponible': ('success', 'Disponible'),
        'occupee': ('primary', 'Occupée'),
        'reservee': ('warning', 'Réservée'),
        'oui': ('success', 'Oui'),
        'non': ('secondary', 'Non'),
        True: ('success', 'Oui'),
        False: ('secondary', 'Non'),
    }
    
    color, label = status_map.get(value, ('secondary', str(value)))
    return mark_safe(f'<span class="badge bg-{color}">{label}</span>')

@register.filter
def format_type_paiement(value):
    """Formater un type de paiement"""
    if not value:
        return "-"
    
    type_map = {
        'loyer': ('primary', 'Loyer'),
        'caution': ('info', 'Caution'),
        'avance': ('warning', 'Avance'),
        'charges': ('secondary', 'Charges'),
    }
    
    color, label = type_map.get(value, ('secondary', str(value)))
    return mark_safe(f'<span class="badge bg-{color}">{label}</span>')

@register.filter
def format_mode_paiement(value):
    """Formater un mode de paiement"""
    if not value:
        return "-"
    
    mode_map = {
        'especes': ('success', 'Espèces'),
        'virement': ('info', 'Virement'),
        'cheque': ('warning', 'Chèque'),
        'mobile_money': ('primary', 'Mobile Money'),
        'carte': ('secondary', 'Carte'),
    }
    
    color, label = mode_map.get(value, ('secondary', str(value)))
    return mark_safe(f'<span class="badge bg-{color}">{label}</span>')

@register.filter
def truncate_text(value, length=50):
    """Tronquer un texte"""
    if not value:
        return "-"
    
    text = str(value)
    if len(text) <= length:
        return text
    
    return text[:length] + "..."

@register.filter
def get_nom_complet(obj):
    """Obtenir le nom complet d'un objet"""
    if hasattr(obj, 'get_nom_complet'):
        return obj.get_nom_complet()
    elif hasattr(obj, 'nom') and hasattr(obj, 'prenom'):
        return f"{obj.prenom} {obj.nom}".strip()
    elif hasattr(obj, 'titre'):
        return obj.titre
    else:
        return str(obj)

@register.filter
def check_condition(user, condition):
    """Vérifier une condition sur l'utilisateur"""
    if not condition:
        return True
    
    # Conditions simples
    if condition == 'user.is_privilege_user':
        return hasattr(user, 'groupe_travail') and user.groupe_travail.nom == 'PRIVILEGE'
    elif condition == 'user.is_admin':
        return user.is_staff
    elif condition == 'user.is_authenticated':
        return user.is_authenticated
    
    return False
