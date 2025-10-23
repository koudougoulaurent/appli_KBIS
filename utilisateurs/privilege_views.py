from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
import json

from .models import Utilisateur
from .mixins import PrivilegeDeleteMixin, PrivilegeRequiredMixin
from core.models import AuditLog
from proprietes.models import Bailleur, Locataire, Propriete, TypeBien, ChargesBailleur


class PrivilegeActionView(PrivilegeRequiredMixin, PrivilegeDeleteMixin, View):
    """
    Vue de base pour les actions de privilège (suppression et désactivation).
    """
    
    def post(self, request, model_name, element_id):
        """Gère les actions POST pour la suppression et désactivation."""
        if not request.user.is_privilege_user():
            return JsonResponse({
                'success': False,
                'message': 'Permissions insuffisantes. Seuls les utilisateurs du groupe PRIVILEGE peuvent effectuer cette action.'
            }, status=403)
        
        try:
            # Récupérer le modèle approprié
            model_class = self.get_model_class(model_name)
            if not model_class:
                return JsonResponse({
                    'success': False,
                    'message': f'Modèle {model_name} non reconnu.'
                }, status=400)
            
            # Effectuer l'action
            return self.delete_element(request, model_class, element_id)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors de l\'exécution de l\'action: {str(e)}'
            }, status=500)
    
    def get_model_class(self, model_name):
        """Retourne la classe du modèle basée sur le nom."""
        model_mapping = {
            'bailleur': Bailleur,
            'locataire': Locataire,
            'propriete': Propriete,
            'typebien': TypeBien,
            'chargesbailleur': ChargesBailleur,
            'utilisateur': Utilisateur,
        }
        return model_mapping.get(model_name.lower())






# Vue de gestion des actions de privilège en lot
@require_POST
@login_required
def privilege_bulk_actions(request):
    """
    Vue pour effectuer des actions en lot sur plusieurs éléments.
    """
    if not request.user.is_privilege_user():
        return JsonResponse({
            'success': False,
            'message': 'Permissions insuffisantes'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        element_ids = data.get('element_ids', [])
        model_name = data.get('model_name')
        
        if not action or not element_ids or not model_name:
            return JsonResponse({
                'success': False,
                'message': 'Paramètres manquants'
            }, status=400)
        
        # Récupérer le modèle approprié
        model_class = PrivilegeActionView().get_model_class(model_name)
        if not model_class:
            return JsonResponse({
                'success': False,
                'message': f'Modèle {model_name} non reconnu.'
            }, status=400)
        
        results = []
        success_count = 0
        
        for element_id in element_ids:
            try:
                element = get_object_or_404(model_class, id=element_id)
                
                if action == 'delete':
                    success, message, action_effectuee = request.user.safe_delete_element(element, request)
                elif action == 'disable':
                    # Utiliser la logique de désactivation
                    view = PrivilegeDisableView()
                    success = view.disable_element(element)
                    message = f'Élément désactivé' if success else 'Échec de la désactivation'
                    action_effectuee = 'désactivation' if success else None
                else:
                    success = False
                    message = f'Action {action} non reconnue'
                    action_effectuee = None
                
                if success:
                    success_count += 1
                    # Log d'audit
                    if action_effectuee:
                        view = PrivilegeActionView()
                        view._log_privilege_action(request.user, element, action_effectuee, request)
                
                results.append({
                    'element_id': element_id,
                    'element_name': str(element),
                    'success': success,
                    'message': message
                })
                
            except Exception as e:
                results.append({
                    'element_id': element_id,
                    'success': False,
                    'message': f'Erreur: {str(e)}'
                })
        
        return JsonResponse({
            'success': True,
            'message': f'{success_count}/{len(element_ids)} éléments traités avec succès',
            'results': results,
            'success_count': success_count,
            'total_count': len(element_ids)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du traitement en lot: {str(e)}'
        }, status=500)
