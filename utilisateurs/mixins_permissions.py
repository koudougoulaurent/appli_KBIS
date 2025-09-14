"""
Mixins de permissions ajustés pour GESTIMMOB
- Tous les utilisateurs peuvent AJOUTER
- Seuls les utilisateurs PRIVILEGE peuvent MODIFIER et SUPPRIMER
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


class AddPermissionMixin:
    """
    Mixin pour permettre l'ajout à tous les utilisateurs connectés
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour effectuer cette action.")
            return redirect('utilisateurs:connexion_groupes')
        
        if not hasattr(request.user, 'groupe_travail') or not request.user.groupe_travail:
            messages.error(request, "Vous n'avez pas de groupe de travail assigné.")
            return redirect('utilisateurs:connexion_groupes')
        
        if not request.user.actif:
            messages.error(request, "Votre compte est désactivé.")
            return redirect('utilisateurs:connexion_groupes')
        
        return super().dispatch(request, *args, **kwargs)


class ModifyPermissionMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre la modification aux utilisateurs PRIVILEGE uniquement
    """
    
    def test_func(self):
        """Vérifie si l'utilisateur appartient au groupe PRIVILEGE."""
        if not self.request.user.is_authenticated:
            return False
        
        if not hasattr(self.request.user, 'groupe_travail') or not self.request.user.groupe_travail:
            return False
        
        if not self.request.user.actif:
            return False
        
        return self.request.user.groupe_travail.nom.upper() == 'PRIVILEGE'
    
    def handle_no_permission(self):
        """Gère le refus d'accès."""
        messages.error(
            self.request, 
            "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent modifier les éléments."
        )
        return redirect('utilisateurs:dashboard_groupe', 
                       groupe_nom=self.request.user.groupe_travail.nom if self.request.user.groupe_travail else 'default')


class DeletePermissionMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre la suppression aux utilisateurs PRIVILEGE uniquement
    """
    
    def test_func(self):
        """Vérifie si l'utilisateur appartient au groupe PRIVILEGE."""
        if not self.request.user.is_authenticated:
            return False
        
        if not hasattr(self.request.user, 'groupe_travail') or not self.request.user.groupe_travail:
            return False
        
        if not self.request.user.actif:
            return False
        
        return self.request.user.groupe_travail.nom.upper() == 'PRIVILEGE'
    
    def handle_no_permission(self):
        """Gère le refus d'accès."""
        messages.error(
            self.request, 
            "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent supprimer les éléments."
        )
        return redirect('utilisateurs:dashboard_groupe', 
                       groupe_nom=self.request.user.groupe_travail.nom if self.request.user.groupe_travail else 'default')


class ViewPermissionMixin:
    """
    Mixin pour permettre la consultation à tous les utilisateurs connectés
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour accéder à cette page.")
            return redirect('utilisateurs:connexion_groupes')
        
        if not hasattr(request.user, 'groupe_travail') or not request.user.groupe_travail:
            messages.error(request, "Vous n'avez pas de groupe de travail assigné.")
            return redirect('utilisateurs:connexion_groupes')
        
        if not request.user.actif:
            messages.error(request, "Votre compte est désactivé.")
            return redirect('utilisateurs:connexion_groupes')
        
        return super().dispatch(request, *args, **kwargs)


class PrivilegeOnlyMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux utilisateurs PRIVILEGE uniquement
    (pour les fonctionnalités très sensibles)
    """
    
    def test_func(self):
        """Vérifie si l'utilisateur appartient au groupe PRIVILEGE."""
        if not self.request.user.is_authenticated:
            return False
        
        if not hasattr(self.request.user, 'groupe_travail') or not self.request.user.groupe_travail:
            return False
        
        if not self.request.user.actif:
            return False
        
        return self.request.user.groupe_travail.nom.upper() == 'PRIVILEGE'
    
    def handle_no_permission(self):
        """Gère le refus d'accès."""
        messages.error(
            self.request, 
            "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder à cette fonctionnalité."
        )
        return redirect('utilisateurs:dashboard_groupe', 
                       groupe_nom=self.request.user.groupe_travail.nom if self.request.user.groupe_travail else 'default')


def check_add_permission(user):
    """
    Vérifie si l'utilisateur peut ajouter des éléments
    Tous les utilisateurs connectés et actifs peuvent ajouter
    """
    if not user.is_authenticated:
        return False, "Vous devez être connecté pour effectuer cette action."
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False, "Vous n'avez pas de groupe de travail assigné."
    
    if not user.actif:
        return False, "Votre compte est désactivé."
    
    return True, "Autorisé"


def check_modify_permission(user):
    """
    Vérifie si l'utilisateur peut modifier des éléments
    Seuls les utilisateurs PRIVILEGE peuvent modifier
    """
    if not user.is_authenticated:
        return False, "Vous devez être connecté pour effectuer cette action."
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False, "Vous n'avez pas de groupe de travail assigné."
    
    if not user.actif:
        return False, "Votre compte est désactivé."
    
    if user.groupe_travail.nom.upper() != 'PRIVILEGE':
        return False, "Seuls les utilisateurs du groupe PRIVILEGE peuvent modifier les éléments."
    
    return True, "Autorisé"


def check_delete_permission(user):
    """
    Vérifie si l'utilisateur peut supprimer des éléments
    Seuls les utilisateurs PRIVILEGE peuvent supprimer
    """
    if not user.is_authenticated:
        return False, "Vous devez être connecté pour effectuer cette action."
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False, "Vous n'avez pas de groupe de travail assigné."
    
    if not user.actif:
        return False, "Votre compte est désactivé."
    
    if user.groupe_travail.nom.upper() != 'PRIVILEGE':
        return False, "Seuls les utilisateurs du groupe PRIVILEGE peuvent supprimer les éléments."
    
    return True, "Autorisé"


def check_privilege_permission(user):
    """
    Vérifie si l'utilisateur appartient au groupe PRIVILEGE
    """
    if not user.is_authenticated:
        return False, "Vous devez être connecté pour effectuer cette action."
    
    if not hasattr(user, 'groupe_travail') or not user.groupe_travail:
        return False, "Vous n'avez pas de groupe de travail assigné."
    
    if not user.actif:
        return False, "Votre compte est désactivé."
    
    if user.groupe_travail.nom.upper() != 'PRIVILEGE':
        return False, "Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder à cette fonctionnalité."
    
    return True, "Autorisé"
