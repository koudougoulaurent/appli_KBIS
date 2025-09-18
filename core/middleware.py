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
from .adaptive_security import AdaptiveSecurity, UserFriendlySecurity


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
    Middleware de sécurité intelligente et conviviale pour l'immobilier
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
        self.failed_attempts = {}
        self.adaptive_security = AdaptiveSecurity()
        self.user_friendly = UserFriendlySecurity()
        self.whitelist_ips = ['127.0.0.1', 'localhost']  # IPs de confiance
        
    def process_request(self, request):
        """Vérifications de sécurité adaptatives et conviviales"""
        client_ip = self.get_client_ip(request)
        user = getattr(request, 'user', None)
        
        # IPs de confiance - pas de vérifications strictes
        if client_ip in self.whitelist_ips:
            return None
        
        # Obtenir les paramètres de sécurité adaptés
        security_params = self.adaptive_security.get_security_parameters(user, request)
        
        # Vérifier les tentatives de connexion échouées (adaptatif)
        if self.is_ip_locked_out(client_ip, security_params):
            self.logger.warning(f"Tentative d'accès bloquée depuis IP verrouillée: {client_ip}")
            return self.create_friendly_error_response(
                "Accès temporairement limité", 
                "Trop de tentatives de connexion. Veuillez patienter quelques minutes."
            )
        
        # Vérifications adaptatives selon le niveau de confiance
        if security_params.get('check_headers', True) and self.has_suspicious_headers(request):
            self.logger.warning(f"Headers suspects détectés depuis {client_ip}")
            return self.create_friendly_error_response(
                "Requête non autorisée", 
                "Votre navigateur semble avoir un problème. Veuillez actualiser la page."
            )
        
        if security_params.get('check_path_traversal', True) and self.has_path_traversal(request):
            self.logger.warning(f"Tentative de path traversal depuis {client_ip}: {request.path}")
            return self.create_friendly_error_response(
                "Chemin non autorisé", 
                "La page demandée n'existe pas ou n'est pas accessible."
            )
        
        if security_params.get('check_sql_injection', True) and self.has_sql_injection_attempts(request):
            self.logger.warning(f"Tentative d'injection SQL depuis {client_ip}")
            return self.create_friendly_error_response(
                "Requête invalide", 
                "Les caractères saisis ne sont pas autorisés. Veuillez corriger votre saisie."
            )
        
        return None
    
    def create_friendly_error_response(self, title, message):
        """Créer une réponse d'erreur conviviale"""
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - KBIS International</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .error-container {{
                    background: white;
                    border-radius: 20px;
                    padding: 3rem;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 2rem;
                }}
                .error-icon {{
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }}
                .error-title {{
                    color: #e74c3c;
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                    font-weight: bold;
                }}
                .error-message {{
                    color: #7f8c8d;
                    font-size: 1rem;
                    line-height: 1.6;
                    margin-bottom: 2rem;
                }}
                .retry-btn {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 25px;
                    font-size: 1rem;
                    cursor: pointer;
                    transition: transform 0.3s ease;
                }}
                .retry-btn:hover {{
                    transform: translateY(-2px);
                }}
                .company-logo {{
                    margin-bottom: 2rem;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="company-logo">
                    <h2 style="color: #2c3e50; margin: 0;">🏢 KBIS INTERNATIONAL</h2>
                    <p style="color: #7f8c8d; margin: 0.5rem 0 0 0;">Immobilière et Construction</p>
                </div>
                <div class="error-icon">⚠️</div>
                <div class="error-title">{title}</div>
                <div class="error-message">{message}</div>
                <button class="retry-btn" onclick="window.location.reload()">
                    🔄 Réessayer
                </button>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html, content_type='text/html')
    
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
    
    def is_ip_locked_out(self, ip, security_params=None):
        """Vérifier si l'IP est verrouillée (adaptatif)"""
        if security_params is None:
            security_params = {'max_attempts': 10, 'lockout_duration': 180}
        
        if ip in self.failed_attempts:
            last_attempt = self.failed_attempts[ip]['last_attempt']
            lockout_duration = security_params.get('lockout_duration', 180)
            if timezone.now().timestamp() - last_attempt < lockout_duration:
                return True
            else:
                del self.failed_attempts[ip]
        return False
    
    def has_suspicious_headers(self, request):
        """Détecter les headers vraiment suspects (plus intelligent)"""
        # Seulement les headers vraiment dangereux
        dangerous_patterns = ['<script', 'javascript:', 'data:text/html', 'vbscript:']
        
        for header_name, header_value in request.META.items():
            if isinstance(header_value, str):
                header_value_lower = header_value.lower()
                # Vérifier seulement les patterns vraiment dangereux
                if any(pattern in header_value_lower for pattern in dangerous_patterns):
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
        """Détecter les tentatives d'injection SQL (plus intelligent)"""
        # Seulement les patterns vraiment dangereux et évidents
        dangerous_sql_patterns = [
            'union select',
            'drop table',
            'delete from',
            'insert into',
            'update set',
            'exec(',
            'execute(',
        ]
        
        # Vérifier les paramètres GET (seulement si vraiment suspects)
        for key, value in request.GET.items():
            if isinstance(value, str) and len(value) > 10:  # Ignorer les valeurs courtes
                value_lower = value.lower()
                if any(pattern in value_lower for pattern in dangerous_sql_patterns):
                    return True
        
        # Vérifier les paramètres POST (seulement si vraiment suspects)
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if isinstance(value, str) and len(value) > 10:  # Ignorer les valeurs courtes
                    value_lower = value.lower()
                    if any(pattern in value_lower for pattern in dangerous_sql_patterns):
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
