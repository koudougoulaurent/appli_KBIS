"""
Filtres et tags personnalisés pour les templates Django
"""

from django import template
from django.http import QueryDict

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtre pour accéder aux éléments d'un dictionnaire ou QueryDict
    Usage dans les templates : {{ request.GET|get_item:filter.name }}
    """
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return dictionary.get(key, None) if isinstance(dictionary, dict) else None

@register.filter
def get_list(dictionary, key):
    """
    Filtre pour accéder aux listes dans un QueryDict
    Usage dans les templates : {{ request.GET|get_list:filter.name }}
    """
    if isinstance(dictionary, QueryDict):
        return dictionary.getlist(key)
    elif hasattr(dictionary, 'get'):
        value = dictionary.get(key)
        return [value] if value else []
    return []

@register.filter
def currency_format(value):
    """
    Formate un nombre avec la devise XOF selon les standards du Franc CFA
    Usage : {{ montant|currency_format }}
    
    Exemples:
    - 1000 → "1 000 XOF"
    - 1234.50 → "1 234,50 XOF" 
    - None → "0 XOF"
    """
    try:
        if value is None or value == '':
            return "0 XOF"
        
        # Convertir en float
        amount = float(value)
        
        # Formatage spécial pour le Franc CFA
        # Séparer les milliers avec des espaces et les décimales avec une virgule
        if amount == int(amount):
            # Si c'est un nombre entier, ne pas afficher les décimales
            formatted = f"{int(amount):,}".replace(',', ' ')
        else:
            # Afficher avec 2 décimales
            formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        
        return f"{formatted} XOF"
        
    except (ValueError, TypeError):
        return f"{value} XOF"

@register.filter
def currency_symbol(value):
    """
    Ajoute simplement le symbole XOF avec formatage basique
    Usage : {{ montant|currency_symbol }}
    """
    try:
        if value is None or value == '':
            return "0 XOF"
        amount = float(value)
        if amount == int(amount):
            return f"{int(amount)} XOF"
        else:
            return f"{amount:,.2f}".replace(',', ' ').replace('.', ',') + " XOF"
    except (ValueError, TypeError):
        return f"{value} XOF"

@register.filter
def currency_short(value):
    """
    Format court pour les montants (sans décimales si entier)
    Usage : {{ montant|currency_short }}
    """
    try:
        if value is None or value == '':
            return "0 XOF"
        
        amount = float(value)
        
        # Pour les gros montants, utiliser des abréviations
        if amount >= 1000000:
            return f"{amount/1000000:,.1f}M XOF".replace(',', ' ').replace('.', ',')
        elif amount >= 1000:
            return f"{amount/1000:,.0f}K XOF".replace(',', ' ')
        elif amount == int(amount):
            return f"{int(amount)} XOF"
        else:
            return f"{amount:,.2f} XOF".replace(',', ' ').replace('.', ',')
            
    except (ValueError, TypeError):
        return f"{value} XOF"

@register.filter
def get_attribute(obj, attr_name):
    """
    Filtre pour accéder aux attributs d'un objet de manière dynamique
    Usage dans les templates : {{ object|get_attribute:field_name }}
    """
    try:
        # Gérer les relations et attributs imbriqués (ex: "propriete__titre")
        if '__' in attr_name:
            parts = attr_name.split('__')
            current = obj
            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return ''
            return current
        else:
            # Attribut simple
            if hasattr(obj, attr_name):
                return getattr(obj, attr_name)
            return ''
    except (AttributeError, TypeError):
        return ''

@register.filter
def remove_page_param(query_string):
    """
    Filtre pour supprimer le paramètre 'page' d'une query string
    Usage dans les templates : {{ request.GET.urlencode|remove_page_param }}
    """
    if not query_string:
        return ''
    
    # Séparer les paramètres
    params = []
    for param in query_string.split('&'):
        if param and not param.startswith('page='):
            params.append(param)
    
    # Retourner la query string sans le paramètre page
    result = '&'.join(params)
    return f'&{result}' if result else ''

@register.simple_tag
def get_query_param(request, param_name):
    """
    Tag pour récupérer un paramètre de requête
    Usage : {% get_query_param request 'param_name' %}
    """
    return request.GET.get(param_name, '')

@register.filter
def div(value, arg):
    """
    Filtre pour effectuer une division
    Usage dans les templates : {{ value|div:arg }}
    """
    try:
        if arg == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """
    Filtre pour effectuer une multiplication
    Usage dans les templates : {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0