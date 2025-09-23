"""
Système de sécurité adaptatif pour KBIS IMMOBILIER
Sécurité intelligente qui s'adapte à l'utilisateur
"""
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

logger = logging.getLogger('security')


class AdaptiveSecurity:
    """Sécurité adaptative basée sur le comportement utilisateur"""
    
    def __init__(self):
        self.trust_levels = {
            'NEW_USER': 0.3,      # Nouvel utilisateur - plus de vérifications
            'REGULAR_USER': 0.6,  # Utilisateur régulier - vérifications normales
            'TRUSTED_USER': 0.8,  # Utilisateur de confiance - moins de vérifications
            'ADMIN_USER': 0.9,    # Administrateur - vérifications minimales
        }
    
    def get_user_trust_level(self, user):
        """Calculer le niveau de confiance d'un utilisateur"""
        if not user or not user.is_authenticated:
            return 'NEW_USER'
        
        # Vérifier si c'est un administrateur
        if user.is_staff or user.is_superuser:
            return 'ADMIN_USER'
        
        # Calculer basé sur l'historique
        user_id = user.id
        cache_key = f"user_trust_{user_id}"
        trust_data = cache.get(cache_key, {
            'login_count': 0,
            'last_login': None,
            'failed_attempts': 0,
            'suspicious_activities': 0,
            'account_age_days': 0
        })
        
        # Calculer l'âge du compte
        if user.date_joined:
            account_age = (timezone.now() - user.date_joined).days
            trust_data['account_age_days'] = account_age
        
        # Calculer le score de confiance
        trust_score = 0.5  # Score de base
        
        # Bonus pour l'âge du compte
        if account_age > 30:
            trust_score += 0.2
        elif account_age > 7:
            trust_score += 0.1
        
        # Bonus pour les connexions régulières
        if trust_data['login_count'] > 10:
            trust_score += 0.2
        elif trust_data['login_count'] > 5:
            trust_score += 0.1
        
        # Malus pour les tentatives échouées
        if trust_data['failed_attempts'] > 5:
            trust_score -= 0.3
        elif trust_data['failed_attempts'] > 2:
            trust_score -= 0.1
        
        # Malus pour les activités suspectes
        if trust_data['suspicious_activities'] > 3:
            trust_score -= 0.4
        elif trust_data['suspicious_activities'] > 1:
            trust_score -= 0.2
        
        # Déterminer le niveau de confiance
        if trust_score >= 0.8:
            return 'TRUSTED_USER'
        elif trust_score >= 0.6:
            return 'REGULAR_USER'
        else:
            return 'NEW_USER'
    
    def should_apply_strict_security(self, user, request):
        """Déterminer si appliquer une sécurité stricte"""
        trust_level = self.get_user_trust_level(user)
        trust_score = self.trust_levels[trust_level]
        
        # IPs de confiance - sécurité minimale
        client_ip = self.get_client_ip(request)
        if client_ip in ['127.0.0.1', 'localhost']:
            return False
        
        # Utilisateurs de confiance - sécurité réduite
        if trust_score >= 0.8:
            return False
        
        # Nouveaux utilisateurs - sécurité renforcée
        if trust_score <= 0.4:
            return True
        
        # Vérifier l'heure d'accès (sécurité renforcée la nuit)
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 22:
            return True
        
        return False
    
    def get_security_parameters(self, user, request):
        """Obtenir les paramètres de sécurité adaptés"""
        trust_level = self.get_user_trust_level(user)
        
        if trust_level == 'ADMIN_USER':
            return {
                'max_attempts': 20,
                'lockout_duration': 60,  # 1 minute
                'check_headers': False,
                'check_sql_injection': False,
                'check_path_traversal': True,
            }
        elif trust_level == 'TRUSTED_USER':
            return {
                'max_attempts': 15,
                'lockout_duration': 120,  # 2 minutes
                'check_headers': False,
                'check_sql_injection': True,
                'check_path_traversal': True,
            }
        elif trust_level == 'REGULAR_USER':
            return {
                'max_attempts': 10,
                'lockout_duration': 180,  # 3 minutes
                'check_headers': True,
                'check_sql_injection': True,
                'check_path_traversal': True,
            }
        else:  # NEW_USER
            return {
                'max_attempts': 5,
                'lockout_duration': 300,  # 5 minutes
                'check_headers': True,
                'check_sql_injection': True,
                'check_path_traversal': True,
            }
    
    def update_user_activity(self, user, activity_type, success=True):
        """Mettre à jour l'activité utilisateur pour l'adaptation"""
        if not user or not user.is_authenticated:
            return
        
        user_id = user.id
        cache_key = f"user_trust_{user_id}"
        trust_data = cache.get(cache_key, {
            'login_count': 0,
            'last_login': None,
            'failed_attempts': 0,
            'suspicious_activities': 0,
            'account_age_days': 0
        })
        
        if activity_type == 'login':
            if success:
                trust_data['login_count'] += 1
                trust_data['last_login'] = timezone.now().isoformat()
            else:
                trust_data['failed_attempts'] += 1
        elif activity_type == 'suspicious_activity':
            trust_data['suspicious_activities'] += 1
        
        # Sauvegarder pour 24h
        cache.set(cache_key, trust_data, 86400)
    
    def get_client_ip(self, request):
        """Obtenir l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def should_show_security_warning(self, user):
        """Déterminer si afficher un avertissement de sécurité"""
        trust_level = self.get_user_trust_level(user)
        
        # Afficher des avertissements seulement aux nouveaux utilisateurs
        if trust_level == 'NEW_USER':
            return True
        
        # Vérifier s'il y a eu des activités suspectes récentes
        user_id = user.id
        cache_key = f"user_trust_{user_id}"
        trust_data = cache.get(cache_key, {})
        
        if trust_data.get('suspicious_activities', 0) > 0:
            return True
        
        return False
    
    def get_security_tips(self, user):
        """Obtenir des conseils de sécurité personnalisés"""
        trust_level = self.get_user_trust_level(user)
        
        if trust_level == 'NEW_USER':
            return [
                "Utilisez un mot de passe fort et unique",
                "Ne partagez jamais vos identifiants",
                "Déconnectez-vous après chaque session",
                "Signalez toute activité suspecte"
            ]
        elif trust_level == 'REGULAR_USER':
            return [
                "Vérifiez régulièrement votre activité",
                "Mettez à jour votre mot de passe périodiquement",
                "Soyez vigilant avec les emails suspects"
            ]
        else:
            return [
                "Maintenez vos bonnes pratiques de sécurité",
                "Surveillez les accès non autorisés"
            ]


class UserFriendlySecurity:
    """Interface de sécurité conviviale"""
    
    @staticmethod
    def create_security_notification(message, level='info'):
        """Créer une notification de sécurité conviviale"""
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'success': '✅',
            'error': '❌'
        }
        
        colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'success': '#2ecc71',
            'error': '#e74c3c'
        }
        
        return {
            'icon': icons.get(level, 'ℹ️'),
            'color': colors.get(level, '#3498db'),
            'message': message,
            'level': level
        }
    
    @staticmethod
    def get_security_status_message(user):
        """Obtenir un message de statut de sécurité convivial"""
        adaptive_security = AdaptiveSecurity()
        trust_level = adaptive_security.get_user_trust_level(user)
        
        messages = {
            'NEW_USER': "Bienvenue ! Votre compte est protégé par notre système de sécurité avancé.",
            'REGULAR_USER': "Votre compte est sécurisé. Continuez à utiliser l'application normalement.",
            'TRUSTED_USER': "Votre compte bénéficie d'un niveau de sécurité élevé et d'un accès prioritaire.",
            'ADMIN_USER': "Accès administrateur - Sécurité maximale activée."
        }
        
        return messages.get(trust_level, messages['NEW_USER'])
