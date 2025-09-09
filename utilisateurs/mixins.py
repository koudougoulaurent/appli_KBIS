from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Utilisateur
from core.models import AuditLog
import json


class PrivilegeButtonsMixin:
    """
    Mixin pour ajouter automatiquement les boutons de privilège (modifier, supprimer, désactiver)
    aux vues de liste pour les utilisateurs du groupe PRIVILEGE.
    """
    
    def get_privilege_actions(self, object_list):
        """
        Génère les actions de privilège pour chaque objet de la liste.
        Retourne un dictionnaire {object_id: [actions]}.
        """
        if not hasattr(self.request.user, 'is_privilege_user') or not self.request.user.is_privilege_user():
            return {}
        
        privilege_actions = {}
        
        for obj in object_list:
            actions = []
            
            # Bouton Modifier - supprimé car déjà présent dans les actions des vues
            # actions.append({
            #     'type': 'edit',
            #     'url': self.get_edit_url(obj),
            #     'icon': 'pencil',
            #     'style': 'outline-warning',
            #     'title': 'Modifier',
            #     'class': 'btn-edit-privilege'
            # })
            
            # Vérifier si l'élément peut être supprimé ou désactivé
            peut_supprimer, peut_désactiver, raison, détails_références = self.request.user.can_delete_any_element(obj)
            
            # Vérifier les contrats actifs pour la suppression forcée
            from core.utils import check_active_contracts_before_force_delete
            contract_check = check_active_contracts_before_force_delete(obj)
            
            if peut_supprimer:
                # Bouton Supprimer - disponible si pas de références
                actions.append({
                    'type': 'delete',
                    'url': self.get_delete_url(obj),
                    'icon': 'trash',
                    'style': 'outline-danger',
                    'title': 'Supprimer définitivement',
                    'class': 'btn-delete-privilege',
                    'data': {
                        'object-id': obj.id,
                        'object-name': str(obj),
                        'model-name': obj._meta.model_name,
                        'can-delete': 'true'
                    }
                })
            elif peut_désactiver:
                # Bouton Désactiver - disponible si référencé ailleurs
                actions.append({
                    'type': 'disable',
                    'url': self.get_disable_url(obj),
                    'icon': 'pause-circle',
                    'style': 'outline-secondary',
                    'title': f'Désactiver (référencé par: {raison})',
                    'class': 'btn-disable-privilege',
                    'data': {
                        'object-id': obj.id,
                        'object-name': str(obj),
                        'model-name': obj._meta.model_name,
                        'can-delete': 'false',
                        'reason': raison,
                        'details-references': détails_références
                    }
                })
            else:
                # Bouton Désactiver - disponible même si pas de références
                actions.append({
                    'type': 'disable',
                    'url': self.get_disable_url(obj),
                    'icon': 'pause-circle',
                    'style': 'outline-secondary',
                    'title': 'Désactiver',
                    'class': 'btn-disable-privilege',
                    'data': {
                        'object-id': obj.id,
                        'object-name': str(obj),
                        'model-name': obj._meta.model_name,
                        'can-delete': 'false',
                        'details-references': détails_références if détails_références else ''
                    }
                })
            
            # Bouton Suppression Forcée/Urgente - TOUJOURS visible pour PRIVILEGE
            actions.append({
                'type': 'force_delete',
                'url': self.get_force_delete_url(obj),
                'icon': 'exclamation-triangle-fill',
                'style': 'danger',
                'title': 'Suppression Forcée/Urgente - Vérification des contrats actifs',
                'class': 'btn-force-delete-privilege',
                'data': {
                    'object-id': obj.id,
                    'object-name': str(obj),
                    'model-name': obj._meta.model_name,
                    'can-force-delete': str(contract_check['can_force_delete']).lower(),
                    'contracts-count': contract_check['contracts_count'],
                    'force-delete-message': contract_check['message']
                }
            })
            
            privilege_actions[obj.id] = actions
        
        return privilege_actions
    
    def get_edit_url(self, obj):
        """Génère l'URL de modification pour un objet."""
        model_name = obj._meta.model_name
        app_label = obj._meta.app_label
        
        # Mapping des URLs de modification par modèle
        edit_urls = {
            'bailleur': 'bailleurs:modifier_bailleur',
            'locataire': 'proprietes:modifier_locataire',
            'propriete': 'proprietes:modifier_propriete',
            'typebien': 'proprietes:modifier_type_bien',
            'chargesbailleur': 'proprietes:modifier_charges_bailleur',
            'utilisateur': 'utilisateurs:modifier_utilisateur',
            'template_recu': 'core:modifier_template_recu',
            'devise': 'core:modifier_devise',
        }
        
        url_name = edit_urls.get(model_name, f'{app_label}:modifier_{model_name}')
        
        try:
            from django.urls import reverse
            return reverse(url_name, args=[obj.id])
        except:
            return '#'
    
    def get_delete_url(self, obj):
        """Génère l'URL de suppression pour un objet."""
        model_name = obj._meta.model_name
        app_label = obj._meta.app_label
        
        # Mapping des URLs de suppression par modèle
        delete_urls = {
            'bailleur': 'bailleurs:supprimer_bailleur',
            'locataire': 'proprietes:supprimer_locataire',
            'propriete': 'proprietes:supprimer_propriete',
            'typebien': 'proprietes:supprimer_type_bien',
            'chargesbailleur': 'proprietes:supprimer_charges_bailleur',
            'utilisateur': 'utilisateurs:supprimer_utilisateur',
            'template_recu': 'core:supprimer_template_recu',
            'devise': 'core:supprimer_devise',
        }
        
        url_name = delete_urls.get(model_name, f'{app_label}:supprimer_{model_name}')
        
        try:
            from django.urls import reverse
            return reverse(url_name, args=[obj.id])
        except:
            return '#'
    
    def get_disable_url(self, obj):
        """Génère l'URL de désactivation pour un objet."""
        model_name = obj._meta.model_name
        app_label = obj._meta.app_label
        
        # Mapping des URLs de désactivation par modèle
        disable_urls = {
            'bailleur': 'bailleurs:desactiver_bailleur',
            'locataire': 'proprietes:desactiver_locataire',
            'propriete': 'proprietes:desactiver_propriete',
            'typebien': 'proprietes:desactiver_type_bien',
            'chargesbailleur': 'proprietes:desactiver_charges_bailleur',
            'utilisateur': 'utilisateurs:desactiver_utilisateur',
            'template_recu': 'core:desactiver_template_recu',
            'devise': 'core:desactiver_devise',
        }
        
        url_name = disable_urls.get(model_name, f'{app_label}:desactiver_{model_name}')
        
        try:
            from django.urls import reverse
            return reverse(url_name, args=[obj.id])
        except:
            return '#'
    
    def get_force_delete_url(self, obj):
        """Génère l'URL de suppression forcée pour un objet."""
        model_name = obj._meta.model_name
        
        try:
            from django.urls import reverse
            return reverse('utilisateurs:privilege_force_delete_element', args=[model_name, obj.id])
        except:
            return '#'
    
    def get_context_data(self, **kwargs):
        """Ajoute les actions de privilège au contexte."""
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'request') and hasattr(self.request, 'user'):
            # Vérifier que l'utilisateur est authentifié avant d'appeler is_privilege_user()
            if self.request.user.is_authenticated:
                context['privilege_actions'] = self.get_privilege_actions(context.get('object_list', []))
                context['is_privilege_user'] = self.request.user.is_privilege_user()
            else:
                # Utilisateur anonyme - pas de privilèges
                context['privilege_actions'] = []
                context['is_privilege_user'] = False
        
        return context


class PrivilegeDeleteMixin:
    """
    Mixin pour gérer la suppression sécurisée des éléments par les utilisateurs PRIVILEGE.
    """
    
    def delete_element(self, request, model_class, element_id):
        """
        Supprime ou désactive un élément selon les permissions PRIVILEGE.
        """
        if not request.user.is_privilege_user():
            return JsonResponse({
                'success': False,
                'message': 'Permissions insuffisantes'
            }, status=403)
        
        try:
            element = get_object_or_404(model_class, id=element_id)
            
            # Utiliser la méthode safe_delete_element du modèle Utilisateur
            success, message, action_effectuee = request.user.safe_delete_element(element, request)
            
            if success:
                # Log d'audit avec répudiation
                self._log_privilege_action(request.user, element, action_effectuee, request)
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'action': action_effectuee,
                    'object_name': str(element)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors de la suppression: {str(e)}'
            }, status=500)
    
    def _log_privilege_action(self, user, element, action, request):
        """
        Enregistre l'action de privilège avec répudiation.
        """
        try:
            # Log d'audit détaillé
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(element),
                object_id=element.id,
                action=f'privilege_{action.lower()}',
                details={
                    'old_data': {
                        'object_name': str(element),
                        'model_name': element._meta.model_name,
                        'app_label': element._meta.app_label
                    },
                    'new_data': {
                        'action_performed': action,
                        'performed_by': user.username,
                        'performed_at': timezone.now().isoformat(),
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT')
                    }
                },
                object_repr=str(element),
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                description=f"Action PRIVILEGE: {action} effectuée par {user.username} sur {element._meta.verbose_name} '{str(element)}'"
            )
            
            # Message de confirmation pour l'utilisateur
            if action == 'suppression':
                messages.success(request, f"Élément '{str(element)}' supprimé avec succès. Action tracée dans l'audit.")
            elif action == 'désactivation':
                messages.warning(request, f"Élément '{str(element)}' désactivé car référencé ailleurs. Action tracée dans l'audit.")
                
        except Exception as e:
            # En cas d'erreur de log, on continue mais on enregistre l'erreur
            messages.error(request, f"Action effectuée mais erreur lors de la traçabilité: {str(e)}")


class PrivilegeRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour restreindre l'accès aux vues aux utilisateurs du groupe PRIVILEGE uniquement.
    """
    
    def test_func(self):
        """Vérifie si l'utilisateur appartient au groupe PRIVILEGE."""
        return hasattr(self.request.user, 'is_privilege_user') and self.request.user.is_privilege_user()
    
    def handle_no_permission(self):
        """Gère le refus d'accès."""
        from django.contrib import messages
        from django.shortcuts import redirect
        
        messages.error(self.request, "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder à cette fonctionnalité.")
        return redirect('utilisateurs:dashboard_groupe', groupe_nom=self.request.user.groupe_travail.nom if self.request.user.groupe_travail else 'default')
