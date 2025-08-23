from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps

def groupe_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur est connecté et a un groupe de travail
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('utilisateurs:connexion_groupes')
        
        if not hasattr(request.user, 'groupe_travail') or not request.user.groupe_travail:
            messages.error(request, "Vous n'avez pas de groupe de travail assigné. Contactez l'administrateur.")
            return redirect('utilisateurs:connexion_groupes')
        
        if not request.user.actif:
            messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
            return redirect('utilisateurs:connexion_groupes')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def module_required(module_name):
    """
    Décorateur pour vérifier qu'un utilisateur a accès à un module spécifique
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('utilisateurs:connexion_groupes')
            
            if not request.user.has_module_permission(module_name):
                messages.error(request, f"Vous n'avez pas accès au module {module_name}.")
                return redirect('utilisateurs:dashboard_groupe', groupe_nom=request.user.groupe_travail.nom)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def groupe_specific(*groupes_autorises):
    """
    Décorateur pour vérifier qu'un utilisateur appartient à un groupe spécifique
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('utilisateurs:connexion_groupes')
            
            if not request.user.groupe_travail or request.user.groupe_travail.nom not in groupes_autorises:
                messages.error(request, f"Vous n'avez pas accès à cette fonctionnalité. Groupes autorisés : {', '.join(groupes_autorises)}")
                return redirect('utilisateurs:dashboard_groupe', groupe_nom=request.user.groupe_travail.nom)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 