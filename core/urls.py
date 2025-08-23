from django.urls import path
from . import views
from . import api_views

app_name = 'core'

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.intelligent_search, name='intelligent_search'),
    
    # Interface API
    path('api-interface/', views.api_interface, name='api_interface'),
    
    # Configuration de l'entreprise
    path('configuration/', views.configuration_entreprise, name='configuration_entreprise'),
    path('templates/', views.gestion_templates, name='gestion_templates'),
    path('templates/<int:template_id>/apercu/', views.apercu_template, name='apercu_template'),
    path('templates/<int:template_id>/test/', views.test_template, name='test_template'),
    
    # API
    path('api/configuration/', views.api_configuration, name='api_configuration'),
    path('api/configuration/sauvegarder/', views.api_sauvegarder_configuration, name='api_sauvegarder_configuration'),
    path('api/dashboard/', api_views.api_dashboard_data, name='api_dashboard_data'),
    path('api/groupe-dashboard/<str:groupe_nom>/', api_views.api_groupe_dashboard_data, name='api_groupe_dashboard_data'),
    path('api/audit/realtime/', api_views.api_audit_data_realtime, name='api_audit_data_realtime'),
    path('api/audit/notifications/', api_views.api_audit_notifications, name='api_audit_notifications'),
    
    # API pour la gestion des cautions
    path('api/cautions/', api_views.api_gestion_cautions, name='api_gestion_cautions'),
    path('api/cautions/<int:contrat_id>/marquer-caution/', api_views.api_marquer_caution_payee, name='api_marquer_caution_payee'),
    path('api/cautions/<int:contrat_id>/marquer-avance/', api_views.api_marquer_avance_payee, name='api_marquer_avance_payee'),
    
    # API pour les identifiants uniques
    path('api/generate-unique-id/', api_views.GenerateUniqueIdView.as_view(), name='generate_unique_id'),
    path('changer-devise/', views.changer_devise, name='changer_devise'),
    path('devises/', views.liste_devises, name='liste_devises'),
    
    # Rapports et contrôles
    path('rapports-audit/', views.rapports_audit, name='rapports_audit'),
    path('audit/<int:log_id>/', views.detail_audit_log, name='detail_audit_log'),
    path('audit-statistiques/', views.audit_statistiques, name='audit_statistiques'),
    path('anomalies/', views.detection_anomalies, name='detection_anomalies'),
    
    # Test du composant téléphone
    path('test-phone-widget/', views.test_phone_widget, name='test_phone_widget'),
] 