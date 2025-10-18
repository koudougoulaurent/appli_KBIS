"""
Template tags personnalisés pour la gestion des permissions utilisateurs
"""

from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()

@register.filter
def can_add(user):
    """Vérifie si l'utilisateur peut ajouter des éléments"""
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False
    
    if not user.actif:
        return False
    
    return True

@register.filter
def can_modify(user):
    """Vérifie si l'utilisateur peut modifier des éléments"""
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False
    
    if not user.actif:
        return False
    
    return user.groupe_travail.nom.upper() == 'PRIVILEGE'

@register.filter
def can_delete(user):
    """Vérifie si l'utilisateur peut supprimer des éléments"""
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False
    
    if not user.actif:
        return False
    
    return user.groupe_travail.nom.upper() == 'PRIVILEGE'

@register.filter
def is_privilege_user(user):
    """Vérifie si l'utilisateur appartient au groupe PRIVILEGE"""
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False
    
    if not user.actif:
        return False
    
    return user.groupe_travail.nom.upper() == 'PRIVILEGE'

@register.filter
def get_group_name(user):
    """Retourne le nom du groupe de l'utilisateur"""
    if not user.is_authenticated:
        return "Non connecté"
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return "Aucun groupe"
    
    return user.groupe_travail.nom

@register.filter
def get_group_description(user):
    """Retourne la description du groupe de l'utilisateur"""
    if not user.is_authenticated:
        return "Utilisateur non connecté"
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return "Aucun groupe assigné"
    
    return user.groupe_travail.description

@register.simple_tag
def permission_message(user):
    """Retourne un message d'information sur les permissions de l'utilisateur"""
    if not user.is_authenticated:
        return "Vous devez être connecté pour utiliser l'application."
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return "Vous n'avez pas de groupe de travail assigné. Contactez l'administrateur."
    
    if not user.actif:
        return "Votre compte est désactivé. Contactez l'administrateur."
    
    if user.groupe_travail.nom.upper() == 'PRIVILEGE':
        return "Vous avez accès complet à toutes les fonctionnalités."
    else:
        return f"Vous pouvez ajouter des éléments. Seuls les utilisateurs du groupe PRIVILEGE peuvent modifier ou supprimer les éléments existants."

@register.simple_tag
def show_add_button(user):
    """Retourne True si le bouton d'ajout doit être affiché"""
    return can_add(user)

@register.simple_tag
def show_modify_button(user):
    """Retourne True si le bouton de modification doit être affiché"""
    return can_modify(user)

@register.simple_tag
def show_delete_button(user):
    """Retourne True si le bouton de suppression doit être affiché"""
    return can_delete(user)

@register.inclusion_tag('utilisateurs/permission_info.html')
def permission_info(user):
    """Affiche les informations de permissions de l'utilisateur"""
    return {
        'user': user,
        'can_add': can_add(user),
        'can_modify': can_modify(user),
        'can_delete': can_delete(user),
        'is_privilege': is_privilege_user(user),
        'group_name': get_group_name(user),
        'group_description': get_group_description(user),
        'permission_message': permission_message(user)
    }
