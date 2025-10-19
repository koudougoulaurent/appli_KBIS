"""
Middleware de sécurité complet contre les injections SQL et XSS
"""
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .sql_security import SQLInjectionProtection
from .input_sanitizer import InputSanitizer

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """Middleware de sécurité complet"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Traite la requête entrante"""
        try:
            # Analyser les paramètres GET
            self._analyze_parameters(request.GET, 'GET', request)
            
            # Analyser les paramètres POST
            if request.method == 'POST':
                self._analyze_parameters(request.POST, 'POST', request)
            
            # Analyser les headers
            self._analyze_headers(request)
            
            # Analyser l'URL
            self._analyze_url(request)
            
        except SuspiciousOperation as e:
            logger.warning(f"Tentative d'attaque détectée: {e}")
            return self._create_security_response(str(e))
        
        return None
    
    def _analyze_parameters(self, params, method, request):
        """Analyse les paramètres de la requête"""
        for key, value in params.items():
            # Analyser la clé
            if SQLInjectionProtection.detect_sql_injection(str(key)):
                raise SuspiciousOperation(f"Clé de paramètre suspecte: {key}")
            
            # Analyser la valeur
            if isinstance(value, (list, tuple)):
                for item in value:
                    if SQLInjectionProtection.detect_sql_injection(str(item)):
                        raise SuspiciousOperation(f"Valeur de paramètre suspecte: {item}")
            else:
                if SQLInjectionProtection.detect_sql_injection(str(value)):
                    raise SuspiciousOperation(f"Valeur de paramètre suspecte: {value}")
    
    def _analyze_headers(self, request):
        """Analyse les headers de la requête"""
        suspicious_headers = [
            'User-Agent',
            'Referer',
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Forwarded-Host',
        ]
        
        for header in suspicious_headers:
            value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}')
            if value and SQLInjectionProtection.detect_sql_injection(str(value)):
                raise SuspiciousOperation(f"Header suspect: {header}")
    
    def _analyze_url(self, request):
        """Analyse l'URL de la requête"""
        if SQLInjectionProtection.detect_sql_injection(request.path):
            raise SuspiciousOperation(f"URL suspecte: {request.path}")
        
        # Analyser les paramètres GET
        for key, value in request.GET.items():
            if isinstance(value, str) and SQLInjectionProtection.detect_sql_injection(value):
                raise SuspiciousOperation(f"Paramètre GET suspect: {key}={value}")
    
    def _create_security_response(self, message):
        """Crée une réponse de sécurité"""
        if getattr(settings, 'SECURITY_RESPONSE_JSON', False):
            return JsonResponse({
                'error': 'Sécurité',
                'message': 'Tentative d\'attaque détectée',
                'details': message
            }, status=403)
        else:
            return HttpResponseForbidden(
                f"<h1>Accès refusé</h1>"
                f"<p>Tentative d'attaque détectée.</p>"
                f"<p>Détails: {message}</p>"
            )


class XSSProtectionMiddleware(MiddlewareMixin):
    """Middleware de protection XSS"""
    
    def process_response(self, request, response):
        """Traite la réponse sortante"""
        if hasattr(response, 'content') and response.content:
            # Ajouter des headers de sécurité
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response['Content-Security-Policy'] = csp
        
        return response


class SQLInjectionMiddleware(MiddlewareMixin):
    """Middleware spécialisé contre les injections SQL"""
    
    def process_request(self, request):
        """Analyse la requête pour les injections SQL"""
        # Analyser tous les paramètres
        all_params = {}
        all_params.update(request.GET)
        if request.method == 'POST':
            all_params.update(request.POST)
        
        for key, value in all_params.items():
            # Vérifier la clé
            if SQLInjectionProtection.detect_sql_injection(str(key)):
                logger.warning(f"Tentative d'injection SQL dans la clé: {key}")
                raise SuspiciousOperation("Tentative d'injection SQL détectée")
            
            # Vérifier la valeur
            if isinstance(value, (list, tuple)):
                for item in value:
                    if SQLInjectionProtection.detect_sql_injection(str(item)):
                        logger.warning(f"Tentative d'injection SQL dans la valeur: {item}")
                        raise SuspiciousOperation("Tentative d'injection SQL détectée")
            else:
                if SQLInjectionProtection.detect_sql_injection(str(value)):
                    logger.warning(f"Tentative d'injection SQL dans la valeur: {value}")
                    raise SuspiciousOperation("Tentative d'injection SQL détectée")
        
        return None

