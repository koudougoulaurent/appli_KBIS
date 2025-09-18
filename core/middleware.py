"""
Middleware personnalisé pour optimiser les performances et la sécurité
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.core.exceptions import SuspiciousOperation


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les performances
    """
    
    def process_request(self, request):
        """Ajouter des headers de performance"""
        request.start_time = time.time()
        
        # Headers de sécurité et performance
        response = None
        if hasattr(self, 'get_response'):
            response = self.get_response(request)
        
        if response:
            # Headers de cache pour les ressources statiques
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                response['Cache-Control'] = 'public, max-age=31536000'  # 1 an
                response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            
            # Headers de performance
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Header de temps de réponse
            if hasattr(request, 'start_time'):
                process_time = time.time() - request.start_time
                response['X-Process-Time'] = f"{process_time:.3f}s"
        
        return response


class DatabaseQueryOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les requêtes de base de données
    """
    
    def process_response(self, request, response):
        """Optimiser les réponses"""
        # Ajouter des headers de cache pour les pages dynamiques
        if response.status_code == 200:
            if request.path.startswith('/paiements/accords/dashboard/'):
                response['Cache-Control'] = 'private, max-age=300'  # 5 minutes
            elif request.path.startswith('/paiements/accords/liste/'):
                response['Cache-Control'] = 'private, max-age=180'  # 3 minutes
        
        return response


class StaticFilesOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les fichiers statiques
    """
    
    def process_request(self, request):
        """Optimiser les requêtes de fichiers statiques"""
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Ajouter des headers de cache
            response = HttpResponse()
            response['Cache-Control'] = 'public, max-age=31536000'
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            return response
        
        return None


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de sécurité renforcée pour l'immobilier
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
    def process_request(self, request):
        """Vérifications de sécurité avant traitement de la requête"""
        client_ip = self.get_client_ip(request)
        
        # Vérifier les tentatives de connexion échouées
        if self.is_ip_locked_out(client_ip):
            self.logger.warning(f"Tentative d'accès bloquée depuis IP verrouillée: {client_ip}")
            return HttpResponseForbidden("Accès temporairement bloqué")
        
        # Vérifier les headers suspects
        if self.has_suspicious_headers(request):
            self.logger.warning(f"Headers suspects détectés depuis {client_ip}: {request.META}")
            return HttpResponseForbidden("Requête suspecte détectée")
        
        # Vérifier les tentatives de path traversal
        if self.has_path_traversal(request):
            self.logger.warning(f"Tentative de path traversal depuis {client_ip}: {request.path}")
            return HttpResponseForbidden("Chemin non autorisé")
        
        # Vérifier les tentatives d'injection SQL
        if self.has_sql_injection_attempts(request):
            self.logger.warning(f"Tentative d'injection SQL depuis {client_ip}: {request.GET}")
            return HttpResponseForbidden("Requête malveillante détectée")
        
        return None
    
    def process_response(self, request, response):
        """Ajouter des headers de sécurité à la réponse"""
        # Headers de sécurité
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Headers de cache sécurisés
        if not request.path.startswith('/static/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
    
    def get_client_ip(self, request):
        """Obtenir l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_locked_out(self, ip):
        """Vérifier si l'IP est verrouillée"""
        if ip in self.failed_attempts:
            last_attempt = self.failed_attempts[ip]['last_attempt']
            if timezone.now().timestamp() - last_attempt < self.lockout_duration:
                return True
            else:
                del self.failed_attempts[ip]
        return False
    
    def has_suspicious_headers(self, request):
        """Détecter les headers suspects"""
        suspicious_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_X_CLUSTER_CLIENT_IP',
        ]
        
        for header in suspicious_headers:
            if header in request.META:
                value = request.META[header]
                if any(char in value for char in ['<', '>', '"', "'", '&', ';']):
                    return True
        return False
    
    def has_path_traversal(self, request):
        """Détecter les tentatives de path traversal"""
        suspicious_patterns = [
            '../',
            '..\\',
            '..%2f',
            '..%5c',
            '%2e%2e%2f',
            '%2e%2e%5c',
        ]
        
        path = request.path.lower()
        return any(pattern in path for pattern in suspicious_patterns)
    
    def has_sql_injection_attempts(self, request):
        """Détecter les tentatives d'injection SQL"""
        sql_patterns = [
            'union select',
            'drop table',
            'delete from',
            'insert into',
            'update set',
            'or 1=1',
            'and 1=1',
            'exec(',
            'execute(',
            'script>',
            '<script',
        ]
        
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if isinstance(value, str):
                value_lower = value.lower()
                if any(pattern in value_lower for pattern in sql_patterns):
                    return True
        
        # Vérifier les paramètres POST
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(pattern in value_lower for pattern in sql_patterns):
                        return True
        
        return False
    
    def record_failed_attempt(self, ip):
        """Enregistrer une tentative échouée"""
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = {'count': 0, 'last_attempt': 0}
        
        self.failed_attempts[ip]['count'] += 1
        self.failed_attempts[ip]['last_attempt'] = timezone.now().timestamp()
        
        if self.failed_attempts[ip]['count'] >= self.max_attempts:
            self.logger.warning(f"IP {ip} verrouillée après {self.max_attempts} tentatives échouées")


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware pour l'audit des actions utilisateur
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
    
    def process_request(self, request):
        """Enregistrer les requêtes importantes"""
        if request.user.is_authenticated:
            # Enregistrer les actions sensibles
            sensitive_paths = [
                '/paiements/',
                '/contrats/',
                '/proprietes/',
                '/utilisateurs/',
                '/admin/',
            ]
            
            if any(path in request.path for path in sensitive_paths):
                self.logger.info(
                    f"Action utilisateur: {request.user.username} - {request.method} {request.path} - IP: {self.get_client_ip(request)}"
                )
    
    def get_client_ip(self, request):
        """Obtenir l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
