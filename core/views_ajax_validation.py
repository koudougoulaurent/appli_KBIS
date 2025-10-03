"""
Vues AJAX pour la validation intelligente
Remplace les erreurs brutes par des suggestions intelligentes
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.smart_validation import SmartValidationSystem
import json

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def validate_property_number(request):
    """
    API pour valider un numéro de propriété avec suggestion intelligente
    """
    try:
        data = json.loads(request.body)
        numero_propriete = data.get('numero_propriete', '').strip()
        exclude_pk = data.get('exclude_pk')
        
        if not numero_propriete:
            return JsonResponse({
                'success': True,
                'message': 'Numéro valide'
            })
        
        is_valid, suggestion, message = SmartValidationSystem.validate_property_number_with_suggestion(
            numero_propriete, exclude_pk
        )
        
        return JsonResponse({
            'success': is_valid,
            'suggestion': suggestion,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def validate_email(request):
    """
    API pour valider un email avec suggestion intelligente
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        exclude_pk = data.get('exclude_pk')
        
        if not email:
            return JsonResponse({
                'success': True,
                'message': 'Email valide'
            })
        
        is_valid, suggestion, message = SmartValidationSystem.validate_tenant_email_with_suggestion(
            email, exclude_pk
        )
        
        return JsonResponse({
            'success': is_valid,
            'suggestion': suggestion,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def validate_contract_number(request):
    """
    API pour valider un numéro de contrat avec suggestion intelligente
    """
    try:
        data = json.loads(request.body)
        numero_contrat = data.get('numero_contrat', '').strip()
        exclude_pk = data.get('exclude_pk')
        
        if not numero_contrat:
            return JsonResponse({
                'success': True,
                'message': 'Numéro valide'
            })
        
        is_valid, suggestion, message = SmartValidationSystem.validate_contract_number_with_suggestion(
            numero_contrat, exclude_pk
        )
        
        return JsonResponse({
            'success': is_valid,
            'suggestion': suggestion,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_suggested_property_number(request):
    """
    API pour obtenir un numéro de propriété suggéré
    """
    try:
        from core.id_generator import IDGenerator
        
        generator = IDGenerator()
        suggested_number = generator.generate_id('propriete')
        
        return JsonResponse({
            'success': True,
            'suggestion': suggested_number,
            'message': 'Numéro suggéré généré automatiquement'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_suggested_contract_number(request):
    """
    API pour obtenir un numéro de contrat suggéré
    """
    try:
        from core.id_generator import IDGenerator
        
        generator = IDGenerator()
        suggested_number = generator.generate_id('contrat')
        
        return JsonResponse({
            'success': True,
            'suggestion': suggested_number,
            'message': 'Numéro de contrat suggéré généré automatiquement'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
