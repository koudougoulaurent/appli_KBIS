"""
Module de logging de sécurité avancé
"""
import logging
import json
from datetime import datetime, timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
import hashlib
from .models import SecurityEvent

User = get_user_model()

# Configuration du logger de sécurité
security_logger = logging.getLogger('security')

# Le modèle SecurityEvent est défini dans core.models

class SecurityLogger:
    """Logger de sécurité centralisé"""
    
    @staticmethod
    def log_event(event_type, description, user=None, request=None, severity='medium', details=None):
        """Enregistre un événement de sécurité"""
        try:
            # Extraire les informations de la requête
            ip_address = 'Unknown'
            user_agent = 'Unknown'
            
            if request:
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            
            # Créer l'événement
            event = SecurityEvent.objects.create(
                event_type=event_type,
                severity=severity,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                description=description,
                details=details or {}
            )
            
            # Logger également dans les logs système
            security_logger.info(f"SECURITY_EVENT: {event_type} - {description} - User: {user} - IP: {ip_address}")
            
            return event
            
        except Exception as e:
            security_logger.error(f"Erreur lors de l'enregistrement de l'événement de sécurité: {e}")
            return None
    
    @staticmethod
    def log_login_success(user, request):
        """Log une connexion réussie"""
        SecurityLogger.log_event(
            'login_success',
            f"Connexion réussie pour {user.username}",
            user=user,
            request=request,
            severity='low'
        )
    
    @staticmethod
    def log_login_failed(username, request, reason="Mot de passe incorrect"):
        """Log un échec de connexion"""
        SecurityLogger.log_event(
            'login_failed',
            f"Échec de connexion pour {username}: {reason}",
            request=request,
            severity='medium',
            details={'username': username, 'reason': reason}
        )
    
    @staticmethod
    def log_logout(user, request):
        """Log une déconnexion"""
        SecurityLogger.log_event(
            'logout',
            f"Déconnexion de {user.username}",
            user=user,
            request=request,
            severity='low'
        )
    
    @staticmethod
    def log_permission_denied(user, action, resource, request):
        """Log un accès refusé"""
        SecurityLogger.log_event(
            'permission_denied',
            f"Accès refusé: {user.username} a tenté {action} sur {resource}",
            user=user,
            request=request,
            severity='medium',
            details={'action': action, 'resource': resource}
        )
    
    @staticmethod
    def log_suspicious_activity(description, user=None, request=None, details=None):
        """Log une activité suspecte"""
        SecurityLogger.log_event(
            'suspicious_activity',
            description,
            user=user,
            request=request,
            severity='high',
            details=details
        )
    
    @staticmethod
    def log_file_upload(user, filename, file_size, mime_type, request, success=True):
        """Log un upload de fichier"""
        event_type = 'file_upload'
        severity = 'low' if success else 'high'
        description = f"Upload {'réussi' if success else 'échoué'}: {filename} ({file_size} bytes, {mime_type})"
        
        SecurityLogger.log_event(
            event_type,
            description,
            user=user,
            request=request,
            severity=severity,
            details={
                'filename': filename,
                'file_size': file_size,
                'mime_type': mime_type,
                'success': success
            }
        )
    
    @staticmethod
    def log_sql_injection_attempt(query, user=None, request=None):
        """Log une tentative d'injection SQL"""
        SecurityLogger.log_event(
            'sql_injection_attempt',
            f"Tentative d'injection SQL détectée: {query[:100]}...",
            user=user,
            request=request,
            severity='critical',
            details={'query': query}
        )
    
    @staticmethod
    def log_xss_attempt(content, user=None, request=None):
        """Log une tentative XSS"""
        SecurityLogger.log_event(
            'xss_attempt',
            f"Tentative XSS détectée: {content[:100]}...",
            user=user,
            request=request,
            severity='high',
            details={'content': content}
        )
    
    @staticmethod
    def log_data_access(user, model_name, action, record_id=None, request=None):
        """Log un accès aux données"""
        description = f"Accès aux données: {user.username} a {action} {model_name}"
        if record_id:
            description += f" (ID: {record_id})"
        
        SecurityLogger.log_event(
            'data_access',
            description,
            user=user,
            request=request,
            severity='low',
            details={
                'model': model_name,
                'action': action,
                'record_id': record_id
            }
        )
    
    @staticmethod
    def log_data_modification(user, model_name, action, record_id, old_data=None, new_data=None, request=None):
        """Log une modification de données"""
        description = f"Modification de données: {user.username} a {action} {model_name} (ID: {record_id})"
        
        SecurityLogger.log_event(
            'data_modification',
            description,
            user=user,
            request=request,
            severity='medium',
            details={
                'model': model_name,
                'action': action,
                'record_id': record_id,
                'old_data': old_data,
                'new_data': new_data
            }
        )

# Signaux Django pour logging automatique
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log automatique des connexions"""
    SecurityLogger.log_login_success(user, request)

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log automatique des déconnexions"""
    SecurityLogger.log_logout(user, request)

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log automatique des échecs de connexion"""
    username = credentials.get('username', 'Unknown')
    SecurityLogger.log_login_failed(username, request)

class SecurityMonitoring:
    """Monitoring de sécurité en temps réel"""
    
    @staticmethod
    def get_recent_events(hours=24, severity=None):
        """Récupère les événements récents"""
        from datetime import timedelta
        since = timezone.now() - timedelta(hours=hours)
        
        queryset = SecurityEvent.objects.filter(timestamp__gte=since)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-timestamp')
    
    @staticmethod
    def get_suspicious_ips(hours=24):
        """Identifie les IPs suspectes"""
        from django.db.models import Count
        from datetime import timedelta
        
        since = timezone.now() - timedelta(hours=hours)
        
        # IPs avec beaucoup d'échecs de connexion
        failed_logins = SecurityEvent.objects.filter(
            event_type='login_failed',
            timestamp__gte=since
        ).values('ip_address').annotate(
            count=Count('id')
        ).filter(count__gte=5).order_by('-count')
        
        # IPs avec des activités suspectes
        suspicious_activities = SecurityEvent.objects.filter(
            event_type='suspicious_activity',
            timestamp__gte=since
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'failed_logins': list(failed_logins),
            'suspicious_activities': list(suspicious_activities)
        }
    
    @staticmethod
    def get_security_stats(days=7):
        """Retourne les statistiques de sécurité"""
        from django.db.models import Count
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        
        stats = SecurityEvent.objects.filter(
            timestamp__gte=since
        ).aggregate(
            total_events=Count('id'),
            login_failures=Count('id', filter=models.Q(event_type='login_failed')),
            suspicious_activities=Count('id', filter=models.Q(event_type='suspicious_activity')),
            critical_events=Count('id', filter=models.Q(severity='critical')),
            high_events=Count('id', filter=models.Q(severity='high')),
        )
        
        return stats
