"""
Système de monitoring de sécurité pour KBIS IMMOBILIER
Surveillance en temps réel des menaces
"""
import logging
import time
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from datetime import datetime, timedelta
import json

logger = logging.getLogger('security')


class SecurityMonitor:
    """Moniteur de sécurité en temps réel"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
        self.alert_thresholds = {
            'failed_logins': 5,
            'suspicious_requests': 10,
            'data_access_anomalies': 3,
        }
    
    def check_failed_logins(self, ip_address):
        """Vérifier les tentatives de connexion échouées"""
        cache_key = f"failed_logins_{ip_address}"
        failed_count = cache.get(cache_key, 0)
        
        if failed_count >= self.alert_thresholds['failed_logins']:
            self.trigger_alert('MULTIPLE_FAILED_LOGINS', {
                'ip': ip_address,
                'count': failed_count,
                'timestamp': timezone.now().isoformat()
            })
            return True
        return False
    
    def check_suspicious_activity(self, ip_address, request_path):
        """Vérifier les activités suspectes"""
        cache_key = f"suspicious_requests_{ip_address}"
        suspicious_requests = cache.get(cache_key, [])
        
        # Ajouter la requête actuelle
        suspicious_requests.append({
            'path': request_path,
            'timestamp': timezone.now().isoformat()
        })
        
        # Garder seulement les 10 dernières requêtes
        suspicious_requests = suspicious_requests[-10:]
        cache.set(cache_key, suspicious_requests, self.cache_timeout)
        
        if len(suspicious_requests) >= self.alert_thresholds['suspicious_requests']:
            self.trigger_alert('SUSPICIOUS_ACTIVITY', {
                'ip': ip_address,
                'requests': suspicious_requests,
                'timestamp': timezone.now().isoformat()
            })
            return True
        return False
    
    def check_data_access_patterns(self, user, action):
        """Vérifier les patterns d'accès aux données"""
        if not user.is_authenticated:
            return False
        
        cache_key = f"data_access_{user.id}"
        access_log = cache.get(cache_key, [])
        
        # Ajouter l'action actuelle
        access_log.append({
            'action': action,
            'timestamp': timezone.now().isoformat()
        })
        
        # Garder seulement les 20 dernières actions
        access_log = access_log[-20:]
        cache.set(cache_key, access_log, self.cache_timeout)
        
        # Vérifier les anomalies
        if self.detect_access_anomalies(access_log):
            self.trigger_alert('DATA_ACCESS_ANOMALY', {
                'user': user.username,
                'user_id': user.id,
                'actions': access_log,
                'timestamp': timezone.now().isoformat()
            })
            return True
        return False
    
    def detect_access_anomalies(self, access_log):
        """Détecter les anomalies dans l'accès aux données"""
        if len(access_log) < 5:
            return False
        
        # Vérifier si l'utilisateur accède à trop de données sensibles rapidement
        sensitive_actions = ['view_paiement', 'view_contrat', 'view_propriete']
        recent_actions = access_log[-5:]  # 5 dernières actions
        
        sensitive_count = sum(1 for action in recent_actions 
                            if any(sensitive in action['action'] for sensitive in sensitive_actions))
        
        return sensitive_count >= 3
    
    def trigger_alert(self, alert_type, data):
        """Déclencher une alerte de sécurité"""
        alert = {
            'type': alert_type,
            'data': data,
            'timestamp': timezone.now().isoformat(),
            'severity': self.get_alert_severity(alert_type)
        }
        
        # Logger l'alerte
        logger.error(f"SECURITY_ALERT: {json.dumps(alert)}")
        
        # Stocker l'alerte dans le cache
        alerts_key = "security_alerts"
        alerts = cache.get(alerts_key, [])
        alerts.append(alert)
        
        # Garder seulement les 50 dernières alertes
        alerts = alerts[-50:]
        cache.set(alerts_key, alerts, 3600)  # 1 heure
    
    def get_alert_severity(self, alert_type):
        """Déterminer la sévérité de l'alerte"""
        severity_map = {
            'MULTIPLE_FAILED_LOGINS': 'HIGH',
            'SUSPICIOUS_ACTIVITY': 'MEDIUM',
            'DATA_ACCESS_ANOMALY': 'HIGH',
        }
        return severity_map.get(alert_type, 'LOW')
    
    def get_security_dashboard_data(self):
        """Obtenir les données pour le tableau de bord de sécurité"""
        alerts = cache.get("security_alerts", [])
        
        # Statistiques des dernières 24h
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        recent_alerts = [
            alert for alert in alerts 
            if datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')) > yesterday
        ]
        
        # Compter par type
        alert_counts = {}
        for alert in recent_alerts:
            alert_type = alert['type']
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        return {
            'total_alerts_24h': len(recent_alerts),
            'alert_breakdown': alert_counts,
            'recent_alerts': recent_alerts[-10:],  # 10 dernières alertes
            'security_score': self.calculate_security_score(recent_alerts)
        }
    
    def calculate_security_score(self, alerts):
        """Calculer un score de sécurité (0-100)"""
        if not alerts:
            return 100
        
        # Pénaliser selon le nombre et le type d'alertes
        penalty = 0
        for alert in alerts:
            if alert['severity'] == 'HIGH':
                penalty += 20
            elif alert['severity'] == 'MEDIUM':
                penalty += 10
            else:
                penalty += 5
        
        score = max(0, 100 - penalty)
        return score


class DataIntegrityChecker:
    """Vérificateur d'intégrité des données"""
    
    @staticmethod
    def check_financial_data_integrity():
        """Vérifier l'intégrité des données financières"""
        from paiements.models import Paiement, PlanPaiementPartiel
        
        issues = []
        
        # Vérifier les paiements avec des montants négatifs
        negative_payments = Paiement.objects.filter(montant__lt=0)
        if negative_payments.exists():
            issues.append(f"Paiements avec montants négatifs: {negative_payments.count()}")
        
        # Vérifier les plans de paiement avec des montants incohérents
        plans_with_issues = PlanPaiementPartiel.objects.filter(
            montant_total__lt=models.F('montant_deja_paye')
        )
        if plans_with_issues.exists():
            issues.append(f"Plans avec montants incohérents: {plans_with_issues.count()}")
        
        return issues
    
    @staticmethod
    def check_user_data_integrity():
        """Vérifier l'intégrité des données utilisateur"""
        from utilisateurs.models import Utilisateur
        
        issues = []
        
        # Vérifier les utilisateurs sans email
        users_without_email = Utilisateur.objects.filter(email__isnull=True)
        if users_without_email.exists():
            issues.append(f"Utilisateurs sans email: {users_without_email.count()}")
        
        # Vérifier les utilisateurs inactifs depuis plus d'un an
        from django.utils import timezone
        from datetime import timedelta
        one_year_ago = timezone.now() - timedelta(days=365)
        inactive_users = Utilisateur.objects.filter(
            last_login__lt=one_year_ago,
            is_active=True
        )
        if inactive_users.exists():
            issues.append(f"Utilisateurs inactifs depuis plus d'un an: {inactive_users.count()}")
        
        return issues


class SecurityReportGenerator:
    """Générateur de rapports de sécurité"""
    
    @staticmethod
    def generate_daily_report():
        """Générer un rapport de sécurité quotidien"""
        monitor = SecurityMonitor()
        dashboard_data = monitor.get_security_dashboard_data()
        
        integrity_checker = DataIntegrityChecker()
        financial_issues = integrity_checker.check_financial_data_integrity()
        user_issues = integrity_checker.check_user_data_integrity()
        
        report = {
            'date': timezone.now().date().isoformat(),
            'security_score': dashboard_data['security_score'],
            'total_alerts': dashboard_data['total_alerts_24h'],
            'alert_breakdown': dashboard_data['alert_breakdown'],
            'data_integrity_issues': {
                'financial': financial_issues,
                'user': user_issues
            },
            'recommendations': SecurityReportGenerator.get_recommendations(dashboard_data)
        }
        
        # Logger le rapport
        logger.info(f"DAILY_SECURITY_REPORT: {json.dumps(report)}")
        
        return report
    
    @staticmethod
    def get_recommendations(dashboard_data):
        """Obtenir des recommandations de sécurité"""
        recommendations = []
        
        if dashboard_data['security_score'] < 70:
            recommendations.append("Score de sécurité faible - Vérifier les alertes récentes")
        
        if dashboard_data['total_alerts_24h'] > 10:
            recommendations.append("Nombre élevé d'alertes - Investiguer les menaces")
        
        if not recommendations:
            recommendations.append("Système de sécurité stable")
        
        return recommendations
