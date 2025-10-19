"""
Middleware de sécurité renforcé
"""
import re
import logging
from django.http import HttpResponseForbidden, HttpResponseTooManyRequests
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from core.security_logging import SecurityLogger

logger = logging.getLogger(__name__)

class EnhancedSecurityMiddleware(MiddlewareMixin):
    """Middleware de sécurité renforcé"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT', 100)
        self.rate_window = getattr(settings, 'RATE_WINDOW', 60)
        
        # Patterns de sécurité
        self.sql_injection_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_',
            r'xp_',
            r'--',
            r'/\*.*?\*/',
            r';\s*drop',
            r';\s*delete',
            r';\s*insert',
            r';\s*update',
        ]
        
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'on\w+\s*=',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
        ]
        
        self.path_traversal_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'\.\.%2f',
            r'\.\.%5c',
        ]
    
    def process_request(self, request):
        """Traite la requête avant qu'elle ne soit traitée par la vue"""
        
        # 1. Vérification du rate limiting
        if self._is_rate_limited(request):
            SecurityLogger.log_event(
                'rate_limit_exceeded',
                f"Rate limit dépassé pour IP {request.META.get('REMOTE_ADDR')}",
                request=request,
                severity='medium'
            )
            return HttpResponseTooManyRequests("Trop de requêtes. Veuillez réessayer plus tard.")
        
        # 2. Vérification des injections SQL
        if self._detect_sql_injection(request):
            SecurityLogger.log_sql_injection_attempt(
                f"Requête: {request.path}",
                request=request
            )
            return HttpResponseForbidden("Requête suspecte détectée.")
        
        # 3. Vérification XSS
        if self._detect_xss(request):
            SecurityLogger.log_xss_attempt(
                f"Requête: {request.path}",
                request=request
            )
            return HttpResponseForbidden("Contenu suspect détecté.")
        
        # 4. Vérification path traversal
        if self._detect_path_traversal(request):
            SecurityLogger.log_event(
                'suspicious_activity',
                f"Tentative de path traversal détectée: {request.path}",
                request=request,
                severity='high'
            )
            return HttpResponseForbidden("Chemin non autorisé.")
        
        # 5. Vérification des headers suspects
        if self._detect_suspicious_headers(request):
            SecurityLogger.log_event(
                'suspicious_activity',
                f"Headers suspects détectés: {request.META.get('HTTP_USER_AGENT', 'Unknown')}",
                request=request,
                severity='medium'
            )
        
        return None
    
    def process_response(self, request, response):
        """Traite la réponse avant qu'elle ne soit envoyée au client"""
        
        # Ajouter des headers de sécurité
        self._add_security_headers(response)
        
        # Log des actions sensibles
        self._log_sensitive_actions(request, response)
        
        return response
    
    def _is_rate_limited(self, request):
        """Vérifie si l'IP a dépassé la limite de taux"""
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        cache_key = f"rate_limit:{client_ip}"
        
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.rate_limit:
            return True
        
        cache.set(cache_key, request_count + 1, self.rate_window)
        return False
    
    def _detect_sql_injection(self, request):
        """Détecte les tentatives d'injection SQL"""
        # Vérifier l'URL
        if self._check_patterns(request.path, self.sql_injection_patterns):
            return True
        
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if isinstance(value, str) and self._check_patterns(value, self.sql_injection_patterns):
                return True
        
        # Vérifier les paramètres POST
        for key, value in request.POST.items():
            if isinstance(value, str) and self._check_patterns(value, self.sql_injection_patterns):
                return True
        
        return False
    
    def _detect_xss(self, request):
        """Détecte les tentatives XSS"""
        # Vérifier l'URL
        if self._check_patterns(request.path, self.xss_patterns):
            return True
        
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if isinstance(value, str) and self._check_patterns(value, self.xss_patterns):
                return True
        
        # Vérifier les paramètres POST
        for key, value in request.POST.items():
            if isinstance(value, str) and self._check_patterns(value, self.xss_patterns):
                return True
        
        return False
    
    def _detect_path_traversal(self, request):
        """Détecte les tentatives de path traversal"""
        return self._check_patterns(request.path, self.path_traversal_patterns)
    
    def _detect_suspicious_headers(self, request):
        """Détecte les headers suspects"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # User agents suspects
        suspicious_agents = [
            'sqlmap',
            'nikto',
            'nmap',
            'masscan',
            'zap',
            'burp',
            'w3af',
            'havij',
            'pangolin',
        ]
        
        for agent in suspicious_agents:
            if agent.lower() in user_agent.lower():
                return True
        
        return False
    
    def _check_patterns(self, text, patterns):
        """Vérifie si un texte correspond à un des patterns"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True
        return False
    
    def _add_security_headers(self, response):
        """Ajoute des headers de sécurité"""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
    
    def _log_sensitive_actions(self, request, response):
        """Log les actions sensibles"""
        if request.user.is_authenticated:
            path = request.path
            method = request.method
            
            # Actions sensibles à logger
            sensitive_patterns = [
                '/admin/',
                '/utilisateurs/ajouter/',
                '/utilisateurs/supprimer/',
                '/paiements/ajouter/',
                '/paiements/supprimer/',
                '/contrats/ajouter/',
                '/contrats/supprimer/',
                '/proprietes/ajouter/',
                '/proprietes/supprimer/',
            ]
            
            for pattern in sensitive_patterns:
                if pattern in path:
                    SecurityLogger.log_event(
                        'data_modification',
                        f"Action sensible: {method} {path}",
                        user=request.user,
                        request=request,
                        severity='medium'
                    )
                    break
            
            # Log des erreurs
            if response.status_code >= 400:
                SecurityLogger.log_event(
                    'suspicious_activity',
                    f"Erreur {response.status_code}: {method} {path}",
                    user=request.user,
                    request=request,
                    severity='medium'
                )

class IPWhitelistMiddleware(MiddlewareMixin):
    """Middleware de whitelist IP (optionnel)"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = getattr(settings, 'IP_WHITELIST', [])
        self.enabled = getattr(settings, 'IP_WHITELIST_ENABLED', False)
    
    def process_request(self, request):
        if not self.enabled or not self.whitelist:
            return None
        
        client_ip = request.META.get('REMOTE_ADDR')
        
        if client_ip not in self.whitelist:
            SecurityLogger.log_event(
                'suspicious_activity',
                f"Accès refusé pour IP non autorisée: {client_ip}",
                request=request,
                severity='high'
            )
            return HttpResponseForbidden("Accès non autorisé.")
        
        return None

