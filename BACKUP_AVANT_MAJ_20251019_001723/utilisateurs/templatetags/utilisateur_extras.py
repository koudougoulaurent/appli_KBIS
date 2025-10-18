from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter pour accéder aux éléments d'un dictionnaire par clé"""
    return dictionary.get(key)

@register.filter
def has_group_permission(user, group_name):
    """
    Template filter pour vérifier si un utilisateur appartient à un groupe spécifique
    ou a les permissions nécessaires pour ce groupe
    """
    if not user or not user.is_authenticated:
        return False
    
    # Vérifier si l'utilisateur appartient au groupe
    if user.groups.filter(name=group_name).exists():
        return True
    
    # Vérifier si l'utilisateur est superuser (accès à tout)
    if user.is_superuser:
        return True
    
    # Vérifier les permissions spécifiques basées sur le nom du groupe
    permission_map = {
        'paiements': ['paiements.add_paiement', 'paiements.change_paiement', 'paiements.delete_paiement'],
        'contrats': ['contrats.add_contrat', 'contrats.change_contrat', 'contrats.delete_contrat'],
        'proprietes': ['proprietes.add_propriete', 'proprietes.change_propriete', 'proprietes.delete_propriete'],
        'utilisateurs': ['utilisateurs.add_utilisateur', 'utilisateurs.change_utilisateur', 'utilisateurs.delete_utilisateur'],
        'notifications': ['notifications.add_notification', 'notifications.change_notification', 'notifications.delete_notification'],
    }
    
    if group_name in permission_map:
        required_permissions = permission_map[group_name]
        return user.has_perms(required_permissions)
    
    return False 