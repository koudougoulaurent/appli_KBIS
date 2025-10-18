"""
Vues de sécurité pour KBIS IMMOBILIER
Tableau de bord de sécurité et monitoring
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json

from .security_monitoring import SecurityMonitor, DataIntegrityChecker, SecurityReportGenerator
from .security import AccessControl
from .adaptive_security import AdaptiveSecurity, UserFriendlySecurity


@staff_member_required
def security_dashboard(request):
    """Tableau de bord de sécurité"""
    monitor = SecurityMonitor()
    dashboard_data = monitor.get_security_dashboard_data()
    
    integrity_checker = DataIntegrityChecker()
    financial_issues = integrity_checker.check_financial_data_integrity()
    user_issues = integrity_checker.check_user_data_integrity()
    
    context = {
        'title': 'Tableau de Bord de Sécurité',
        'security_score': dashboard_data['security_score'],
        'total_alerts_24h': dashboard_data['total_alerts_24h'],
        'alert_breakdown': dashboard_data['alert_breakdown'],
        'recent_alerts': dashboard_data['recent_alerts'],
        'financial_issues': financial_issues,
        'user_issues': user_issues,
        'security_level': get_security_level(dashboard_data['security_score']),
    }
    
    return render(request, 'core/security_dashboard.html', context)


@staff_member_required
def security_alerts_api(request):
    """API pour récupérer les alertes de sécurité"""
    alerts = cache.get("security_alerts", [])
    
    # Filtrer par type si spécifié
    alert_type = request.GET.get('type')
    if alert_type:
        alerts = [alert for alert in alerts if alert['type'] == alert_type]
    
    # Limiter le nombre de résultats
    limit = int(request.GET.get('limit', 50))
    alerts = alerts[-limit:]
    
    return JsonResponse({
        'alerts': alerts,
        'total': len(alerts)
    })


@staff_member_required
def security_report(request):
    """Générer un rapport de sécurité"""
    report = SecurityReportGenerator.generate_daily_report()
    
    return JsonResponse(report)


@login_required
def user_security_status(request):
    """Statut de sécurité de l'utilisateur connecté"""
    user = request.user
    adaptive_security = AdaptiveSecurity()
    user_friendly = UserFriendlySecurity()
    
    # Vérifier les permissions
    can_access_sensitive = AccessControl.can_access_sensitive_data(user)
    
    # Vérifier la dernière connexion
    last_login = user.last_login
    days_since_login = (timezone.now() - last_login).days if last_login else 0
    
    # Vérifier les groupes
    user_groups = [group.name for group in user.groups.all()]
    
    # Obtenir le niveau de confiance
    trust_level = adaptive_security.get_user_trust_level(user)
    security_params = adaptive_security.get_security_parameters(user, request)
    
    # Obtenir le message de statut convivial
    status_message = user_friendly.get_security_status_message(user)
    security_tips = adaptive_security.get_security_tips(user)
    
    status = {
        'user': user.username,
        'groups': user_groups,
        'can_access_sensitive': can_access_sensitive,
        'last_login': last_login.isoformat() if last_login else None,
        'days_since_login': days_since_login,
        'is_secure': days_since_login < 30 and can_access_sensitive,
        'trust_level': trust_level,
        'security_params': security_params,
        'status_message': status_message,
        'security_tips': security_tips,
        'show_warning': adaptive_security.should_show_security_warning(user)
    }
    
    return JsonResponse(status)


def security_health_check(request):
    """Vérification de santé de sécurité"""
    monitor = SecurityMonitor()
    dashboard_data = monitor.get_security_dashboard_data()
    
    # Vérifier l'intégrité des données
    integrity_checker = DataIntegrityChecker()
    financial_issues = integrity_checker.check_financial_data_integrity()
    user_issues = integrity_checker.check_user_data_integrity()
    
    # Déterminer le statut global
    has_issues = len(financial_issues) > 0 or len(user_issues) > 0
    security_score = dashboard_data['security_score']
    
    if security_score >= 80 and not has_issues:
        status = 'HEALTHY'
        message = 'Système de sécurité opérationnel'
    elif security_score >= 60:
        status = 'WARNING'
        message = 'Système de sécurité avec avertissements'
    else:
        status = 'CRITICAL'
        message = 'Système de sécurité critique'
    
    return JsonResponse({
        'status': status,
        'message': message,
        'security_score': security_score,
        'issues': {
            'financial': financial_issues,
            'user': user_issues
        },
        'timestamp': timezone.now().isoformat()
    })


def get_security_level(score):
    """Déterminer le niveau de sécurité basé sur le score"""
    if score >= 90:
        return {'level': 'EXCELLENT', 'color': 'success', 'icon': '🛡️'}
    elif score >= 80:
        return {'level': 'GOOD', 'color': 'info', 'icon': '✅'}
    elif score >= 60:
        return {'level': 'WARNING', 'color': 'warning', 'icon': '⚠️'}
    else:
        return {'level': 'CRITICAL', 'color': 'danger', 'icon': '🚨'}
