"""
Module de sécurité pour les sessions
"""
import time
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class SessionSecurityManager:
    """Gestionnaire de sécurité des sessions"""
    
    @staticmethod
    def get_session_timeout():
        """Retourne le timeout de session configuré"""
        return getattr(settings, 'SESSION_COOKIE_AGE', 1209600)  # 2 semaines par défaut
    
    @staticmethod
    def is_session_expired(session_key):
        """Vérifie si une session est expirée"""
        try:
            session = Session.objects.get(session_key=session_key)
            now = timezone.now()
            session_age = (now - session.expire_date).total_seconds()
            return session_age > 0
        except Session.DoesNotExist:
            return True
    
    @staticmethod
    def invalidate_user_sessions(user):
        """Invalide toutes les sessions d'un utilisateur"""
        try:
            # Récupérer toutes les sessions de l'utilisateur
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            sessions_to_delete = []
            
            for session in sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user.id):
                    sessions_to_delete.append(session.session_key)
            
            # Supprimer les sessions
            for session_key in sessions_to_delete:
                try:
                    Session.objects.get(session_key=session_key).delete()
                    logger.info(f"Session invalidée pour l'utilisateur {user.username}: {session_key}")
                except Session.DoesNotExist:
                    pass
            
            return len(sessions_to_delete)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation des sessions: {e}")
            return 0
    
    @staticmethod
    def invalidate_session(session_key):
        """Invalide une session spécifique"""
        try:
            Session.objects.get(session_key=session_key).delete()
            logger.info(f"Session invalidée: {session_key}")
            return True
        except Session.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_active_sessions(user):
        """Retourne les sessions actives d'un utilisateur"""
        try:
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            active_sessions = []
            
            for session in sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user.id):
                    active_sessions.append({
                        'session_key': session.session_key,
                        'expire_date': session.expire_date,
                        'last_activity': session_data.get('last_activity', 'Unknown')
                    })
            
            return active_sessions
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sessions: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_sessions():
        """Nettoie les sessions expirées"""
        try:
            expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
            count = expired_sessions.count()
            expired_sessions.delete()
            logger.info(f"Sessions expirées nettoyées: {count}")
            return count
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des sessions: {e}")
            return 0
    
    @staticmethod
    def track_session_activity(request):
        """Enregistre l'activité de session"""
        if request.user.is_authenticated:
            session = request.session
            session['last_activity'] = timezone.now().isoformat()
            session['last_ip'] = request.META.get('REMOTE_ADDR', 'Unknown')
            session['user_agent'] = request.META.get('HTTP_USER_AGENT', 'Unknown')
            session.save()

class SessionSecurityMiddleware:
    """Middleware de sécurité des sessions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier la sécurité de la session
        if request.user.is_authenticated:
            self._check_session_security(request)
        
        response = self.get_response(request)
        
        # Ajouter des headers de sécurité
        self._add_security_headers(response)
        
        return response
    
    def _check_session_security(self, request):
        """Vérifie la sécurité de la session"""
        session = request.session
        
        # Vérifier l'expiration
        if SessionSecurityManager.is_session_expired(session.session_key):
            logger.warning(f"Session expirée détectée pour {request.user.username}")
            logout(request)
            return
        
        # Vérifier l'IP (optionnel, peut causer des problèmes avec les proxies)
        if 'last_ip' in session:
            current_ip = request.META.get('REMOTE_ADDR', 'Unknown')
            if session['last_ip'] != current_ip:
                logger.warning(f"Changement d'IP détecté pour {request.user.username}: {session['last_ip']} -> {current_ip}")
                # Optionnel: invalider la session en cas de changement d'IP
                # SessionSecurityManager.invalidate_session(session.session_key)
                # logout(request)
                # return
        
        # Enregistrer l'activité
        SessionSecurityManager.track_session_activity(request)
    
    def _add_security_headers(self, response):
        """Ajoute des headers de sécurité pour les sessions"""
        # Sécuriser les cookies de session
        if hasattr(settings, 'SESSION_COOKIE_SECURE'):
            response.cookies['sessionid']['secure'] = settings.SESSION_COOKIE_SECURE
        
        if hasattr(settings, 'SESSION_COOKIE_HTTPONLY'):
            response.cookies['sessionid']['httponly'] = settings.SESSION_COOKIE_HTTPONLY
        
        if hasattr(settings, 'SESSION_COOKIE_SAMESITE'):
            response.cookies['sessionid']['samesite'] = settings.SESSION_COOKIE_SAMESITE

class RateLimitMiddleware:
    """Middleware de limitation du taux de requêtes"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT', 100)  # 100 requêtes par minute
        self.rate_window = getattr(settings, 'RATE_WINDOW', 60)  # 1 minute
    
    def __call__(self, request):
        # Vérifier le rate limiting
        if self._is_rate_limited(request):
            from django.http import HttpResponseTooManyRequests
            return HttpResponseTooManyRequests("Trop de requêtes. Veuillez réessayer plus tard.")
        
        response = self.get_response(request)
        return response
    
    def _is_rate_limited(self, request):
        """Vérifie si l'utilisateur a dépassé la limite de taux"""
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        cache_key = f"rate_limit:{client_ip}"
        
        # Récupérer le nombre de requêtes
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.rate_limit:
            logger.warning(f"Rate limit dépassé pour IP {client_ip}: {request_count} requêtes")
            return True
        
        # Incrémenter le compteur
        cache.set(cache_key, request_count + 1, self.rate_window)
        return False

class SecurityLoggingMiddleware:
    """Middleware de logging de sécurité"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log des actions sensibles
        self._log_sensitive_actions(request)
        
        response = self.get_response(request)
        
        # Log des réponses d'erreur
        if response.status_code >= 400:
            self._log_error_response(request, response)
        
        return response
    
    def _log_sensitive_actions(self, request):
        """Log les actions sensibles"""
        if request.user.is_authenticated:
            path = request.path
            method = request.method
            
            # Actions sensibles à logger
            sensitive_patterns = [
                '/admin/',
                '/utilisateurs/',
                '/paiements/ajouter/',
                '/paiements/supprimer/',
                '/contrats/ajouter/',
                '/contrats/supprimer/',
                '/proprietes/ajouter/',
                '/proprietes/supprimer/',
            ]
            
            for pattern in sensitive_patterns:
                if pattern in path:
                    logger.info(f"Action sensible: {request.user.username} - {method} {path}")
                    break
    
    def _log_error_response(self, request, response):
        """Log les réponses d'erreur"""
        if response.status_code in [403, 404, 500]:
            logger.warning(f"Erreur {response.status_code}: {request.user.username if request.user.is_authenticated else 'Anonyme'} - {request.method} {request.path}")

