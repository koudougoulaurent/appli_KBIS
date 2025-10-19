from django.urls import path
from . import views_avance, views_monitoring_avance

urlpatterns = [
    # Dashboard des avances
    path('', views_avance.dashboard_avances, name='dashboard_avances'),
    
    # URLs pour les avances de loyer
    path('ajouter/', views_avance.creer_avance, name='ajouter_avance'),
    path('liste/', views_avance.liste_avances, name='liste_avances'),
    path('detail/<int:avance_id>/', views_avance.detail_avance, name='detail_avance'),
    # URL alternative pour les paiements d'avance
    path('paiement/<int:paiement_id>/', views_avance.detail_avance_paiement, name='detail_avance_paiement'),
    path('paiement/', views_avance.paiement_avance, name='paiement_avance'),
    path('contrat-details-ajax/', views_avance.get_contrat_details_ajax, name='get_contrat_details_ajax'),
    path('calculer-ajax/', views_avance.calculer_avance_ajax, name='calculer_avance_ajax'),
    path('suggestions-mois-ajax/', views_avance.get_suggestions_mois_ajax, name='get_suggestions_mois_ajax'),
    path('historique/<int:contrat_id>/', views_avance.historique_paiements_contrat, name='historique_contrat'),
    path('rapport-historique-pdf/<int:contrat_id>/', views_avance.generer_rapport_avances_pdf, name='generer_rapport_avances_pdf'),
    path('recu/<int:avance_id>/', views_avance.generer_recu_avance_unifie, name='generer_recu_avance'),
    
    # URLs pour le monitoring des avances
    path('monitoring/', views_monitoring_avance.monitoring_avances, name='monitoring_avances'),
    path('progression/<int:avance_id>/', views_monitoring_avance.detail_progression_avance, name='detail_progression_avance'),
    path('synchroniser-ajax/', views_monitoring_avance.synchroniser_avances_ajax, name='synchroniser_avances_ajax'),
    path('envoyer-alertes-ajax/', views_monitoring_avance.envoyer_alertes_ajax, name='envoyer_alertes_ajax'),
    path('rapport-progression-ajax/', views_monitoring_avance.rapport_progression_ajax, name='rapport_progression_ajax'),
    
    # API pour la progression dynamique
    path('api/progression/<int:avance_id>/', views_avance.api_progression_avance, name='api_progression_avance'),
    path('api/consommer-auto/', views_avance.api_consommer_auto, name='api_consommer_auto'),
]
