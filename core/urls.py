from django.urls import path
from django.shortcuts import redirect
from .main_views import (
    dashboard,
    configuration_entreprise,
    changer_devise,
    rapports_audit,
    detection_anomalies,
    detail_audit_log,
    audit_statistiques
)
# from .views.test_templates import test_template_kbis
from .views import (
    configuration_entreprise_admin,
    supprimer_entete,
    supprimer_logo,
    valider_fichier_upload
)
from .views.tableaux_bord_securises import (
    tableau_bord_principal,
    configuration_tableau_bord,
    widget_statistiques_generales,
    widget_activite_recente,
    widget_alertes_securite,
    export_donnees_securise,
    intelligent_search
)
from .api_views import (
    quick_actions_api,
    performance_stats,
    clear_cache,
    health_check
)
from .navigation_api import (
    get_navigation_context,
    smart_search_api,
    recent_searches_api,
    save_search_api,
    trending_searches_api,
    module_stats_api
)
from .views_ajax_validation import (
    validate_property_number,
    validate_email,
    validate_contract_number,
    get_suggested_property_number,
    get_suggested_contract_number
)
from .demo_views import demo_kbis_design

app_name = 'core'

def redirect_to_dashboard(request):
    """Redirige vers le tableau de bord principal"""
    return redirect('core:tableau_bord_principal')

urlpatterns = [
    # Route racine - redirection vers le tableau de bord
    path('', redirect_to_dashboard, name='home'),
    
    # Dashboard principal
    path('dashboard/', dashboard, name='dashboard'),
    
    # Configuration
    path('configuration-entreprise/', configuration_entreprise, name='configuration_entreprise'),
    path('configuration-entreprise-admin/', configuration_entreprise_admin, name='configuration_entreprise_admin'),
    path('supprimer-entete/', supprimer_entete, name='supprimer_entete'),
    path('supprimer-logo/', supprimer_logo, name='supprimer_logo'),
    path('valider-fichier-upload/', valider_fichier_upload, name='valider_fichier_upload'),
    path('changer-devise/', changer_devise, name='changer_devise'),
    
    # Tableaux de bord sécurisés
    path('tableau-bord/', tableau_bord_principal, name='tableau_bord_principal'),
    path('configuration-tableau/', configuration_tableau_bord, name='configuration_tableau_bord'),
    
    # Recherche intelligente
    path('recherche-intelligente/', intelligent_search, name='intelligent_search'),
    
    # Widgets AJAX
    path('widget/statistiques/', widget_statistiques_generales, name='widget_statistiques_generales'),
    path('widget/activite/', widget_activite_recente, name='widget_activite_recente'),
    path('widget/alertes/', widget_alertes_securite, name='widget_alertes_securite'),
    
    # Export sécurisé
    path('export/<str:type_donnees>/', export_donnees_securise, name='export_donnees_securise'),
    
    # Audit et sécurité
    path('rapports-audit/', rapports_audit, name='rapports_audit'),
    path('detection-anomalies/', detection_anomalies, name='detection_anomalies'),
    path('audit/log/<int:log_id>/', detail_audit_log, name='detail_audit_log'),
    path('audit/statistiques/', audit_statistiques, name='audit_statistiques'),
    
    # API pour les actions rapides et performance
    path('api/quick-actions/', quick_actions_api, name='quick_actions_api'),
    path('api/performance-stats/', performance_stats, name='performance_stats'),
    
    # API pour la navigation dynamique
    path('api/navigation-context/', get_navigation_context, name='navigation_context_api'),
    path('api/smart-search/', smart_search_api, name='smart_search_api'),
    path('api/recent-searches/', recent_searches_api, name='recent_searches_api'),
    path('api/save-search/', save_search_api, name='save_search_api'),
    path('api/trending-searches/', trending_searches_api, name='trending_searches_api'),
    path('api/module-stats/', module_stats_api, name='module_stats_api'),
    path('api/clear-cache/', clear_cache, name='clear_cache'),
    path('api/health-check/', health_check, name='health_check'),
    
    # API pour la validation intelligente
    path('ajax/validate-property-number/', validate_property_number, name='validate_property_number'),
    path('ajax/validate-email/', validate_email, name='validate_email'),
    path('ajax/validate-contract-number/', validate_contract_number, name='validate_contract_number'),
    path('ajax/suggested-property-number/', get_suggested_property_number, name='suggested_property_number'),
    path('ajax/suggested-contract-number/', get_suggested_contract_number, name='suggested_contract_number'),
    
    # Démonstration du design KBIS
    path('demo-kbis-design/', demo_kbis_design, name='demo_kbis_design'),
    
    # Test du système de templates KBIS - DÉSACTIVÉ TEMPORAIREMENT
    # path('test-template-kbis/', test_template_kbis, name='test_template_kbis'),
]