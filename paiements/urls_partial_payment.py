"""
URLs spécialisées pour le système de paiement partiel
"""

from django.urls import path
from . import views_partial_payment

app_name = 'paiements_partiels'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', views_partial_payment.dashboard_paiements_partiels, name='dashboard'),
    
    # Gestion des plans
    path('plans/', views_partial_payment.liste_plans_paiement, name='liste_plans'),
    path('plans/creer/', views_partial_payment.creer_plan_paiement, name='creer_plan'),
    path('plans/<uuid:plan_id>/', views_partial_payment.detail_plan_paiement, name='detail_plan'),
    path('plans/<uuid:plan_id>/modifier/', views_partial_payment.modifier_plan_paiement, name='modifier_plan'),
    
    # Gestion des échelons
    path('plans/<uuid:plan_id>/echelons/generer/', views_partial_payment.generer_echelons, name='generer_echelons'),
    path('plans/<uuid:plan_id>/echelons/ajouter/', views_partial_payment.ajouter_echelon, name='ajouter_echelon'),
    
    # Paiements partiels
    path('plans/<uuid:plan_id>/paiement/', views_partial_payment.effectuer_paiement_partiel, name='effectuer_paiement'),
    path('paiements/', views_partial_payment.liste_paiements_partiels, name='liste_paiements'),
    
    # Alertes
    path('alertes/', views_partial_payment.alertes_paiements_partiels, name='alertes'),
    path('alertes/<uuid:alerte_id>/traiter/', views_partial_payment.traiter_alerte, name='traiter_alerte'),
    
    # Rapports
    path('rapport/', views_partial_payment.rapport_paiements_partiels, name='rapport'),
    
    # API
    path('api/plans/<uuid:plan_id>/echelons/', views_partial_payment.api_echelons_plan, name='api_echelons'),
    path('api/plans/<uuid:plan_id>/statistiques/', views_partial_payment.api_statistiques_plan, name='api_statistiques'),
]
