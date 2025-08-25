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
from .views.tableaux_bord_securises import (
    tableau_bord_principal,
    configuration_tableau_bord,
    widget_statistiques_generales,
    widget_activite_recente,
    widget_alertes_securite,
    export_donnees_securise,
    intelligent_search
)

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
]