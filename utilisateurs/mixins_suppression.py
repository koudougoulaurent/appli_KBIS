"""
Mixins pour la gestion de la suppression sécurisée des éléments
"""
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from core.models import AuditLog
from core.utils import check_group_permissions
from django.utils import timezone


class SuppressionMixin:
    """
    Mixin pour ajouter la fonctionnalité de suppression aux vues de liste
    """
    
    def get_suppression_url_name(self):
        """
        Retourne le nom de l'URL de suppression.
        Doit être surchargé par les classes filles.
        """
        model_name = self.model.__name__.lower()
        return f"{self.model._meta.app_label}:supprimer_{model_name}"
    
    def get_suppression_context_data(self, **kwargs):
        """
        Ajoute les données de contexte pour la suppression
        """
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        
        # Vérifier si l'utilisateur peut supprimer
        context['can_delete'] = self.request.user.is_privilege_user()
        context['suppression_url_name'] = self.get_suppression_url_name()
        
        return context


class SuppressionViewMixin:
    """
    Mixin pour les vues de suppression génériques
    """
    
    def can_delete(self, user, obj):
        """
        Vérifie si l'utilisateur peut supprimer l'objet
        """
        return user.is_privilege_user()
    
    def get_redirect_url(self, obj):
        """
        Retourne l'URL de redirection après suppression
        """
        model_name = obj.__class__.__name__.lower()
        return f"{obj._meta.app_label}:liste_{model_name}s"
    
    def get_success_message(self, obj):
        """
        Retourne le message de succès après suppression
        """
        return f"{obj._meta.verbose_name.title()} supprimé avec succès."
    
    def get_error_message(self, obj, error):
        """
        Retourne le message d'erreur en cas d'échec
        """
        return f"Erreur lors de la suppression : {str(error)}"


@method_decorator(login_required, name='dispatch')
class SuppressionGeneriqueView(SuppressionViewMixin, View):
    """
    Vue générique pour la suppression d'objets
    """
    
    def post(self, request, pk):
        """
        Traite la suppression de l'objet
        """
        # Vérification des permissions
        if not request.user.is_privilege_user():
            messages.error(request, "Permissions insuffisantes pour supprimer cet élément.")
            return redirect('core:dashboard')
        
        # Récupération de l'objet
        obj = get_object_or_404(self.model, pk=pk, is_deleted=False)
        
        # Vérification supplémentaire
        if not self.can_delete(request.user, obj):
            messages.error(request, "Vous n'avez pas l'autorisation de supprimer cet élément.")
            return redirect(self.get_redirect_url(obj))
        
        action = request.POST.get('action')
        
        if action == 'logical_delete':
            try:
                # Suppression logique
                old_data = {f.name: getattr(obj, f.name) for f in obj._meta.fields}
                obj.is_deleted = True
                obj.deleted_at = timezone.now()
                obj.deleted_by = request.user
                obj.save()
                
                # Log d'audit
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(obj.__class__),
                    object_id=obj.pk,
                    action='DELETE',
                    old_data=old_data,
                    new_data={'is_deleted': True, 'deleted_at': str(timezone.now())},
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, self.get_success_message(obj))
                return redirect(self.get_redirect_url(obj))
                
            except Exception as e:
                messages.error(request, self.get_error_message(obj, e))
                return redirect(self.get_redirect_url(obj))
        
        elif action == 'cancel':
            return redirect(self.get_redirect_url(obj))
        
        return redirect(self.get_redirect_url(obj))
    
    def get(self, request, pk):
        """
        Affiche la page de confirmation de suppression
        """
        # Vérification des permissions
        if not request.user.is_privilege_user():
            messages.error(request, "Permissions insuffisantes pour supprimer cet élément.")
            return redirect('core:dashboard')
        
        obj = get_object_or_404(self.model, pk=pk, is_deleted=False)
        
        if not self.can_delete(request.user, obj):
            messages.error(request, "Vous n'avez pas l'autorisation de supprimer cet élément.")
            return redirect(self.get_redirect_url(obj))
        
        # Prepare field data for display
        field_data = []
        for field in obj._meta.fields:
            if field.name in ['titre', 'nom', 'adresse', 'ville', 'email', 'telephone']:
                value = field.value_from_object(obj)
                if value:
                    field_data.append({
                        'name': field.name,
                        'verbose_name': field.verbose_name,
                        'value': value
                    })
        
        # Determine the correct list URL name based on the app
        list_url_name = 'liste'  # Default for most apps
        if obj._meta.app_label == 'contrats':
            list_url_name = 'contrats:liste'
        else:
            list_url_name = f"{obj._meta.app_label}:liste"
        
        context = {
            'obj': obj,
            'title': f'Supprimer {obj._meta.verbose_name}',
            'model_name': obj._meta.verbose_name,
            'app_name': obj._meta.app_label,
            'field_data': field_data,
            'list_url_name': list_url_name,
        }
        
        return render(request, 'core/confirm_supprimer_generique.html', context)


def create_suppression_view(model_class, app_name, model_name):
    """
    Factory function pour créer des vues de suppression génériques
    """
    class SuppressionView(SuppressionGeneriqueView):
        model = model_class
        
        def get_redirect_url(self, obj):
            return f"{app_name}:liste_{model_name}s"
        
        def get_success_message(self, obj):
            return f"{model_class._meta.verbose_name.title()} supprimé avec succès."
    
    return SuppressionView
