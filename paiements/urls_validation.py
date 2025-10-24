"""
URLs pour la validation intelligente des paiements
"""

from django.urls import path
from . import views_validation_paiements

app_name = 'validation_paiements'

urlpatterns = [
    # Validation AJAX
    path('valider-paiement-ajax/', views_validation_paiements.valider_paiement_ajax, name='valider_paiement_ajax'),
    
    # Statut des paiements
    path('statut-paiements/<int:contrat_id>/', views_validation_paiements.statut_paiements_contrat, name='statut_paiements_contrat'),
    
    # Suggestions
    path('suggerer-mois/<int:contrat_id>/', views_validation_paiements.suggerer_mois_paiement, name='suggerer_mois_paiement'),
    
    # Vérification des doublons
    path('verifier-doublons/<int:contrat_id>/', views_validation_paiements.verifier_doublons_mois, name='verifier_doublons_mois'),
    
    # Historique des validations
    path('historique-validation/<int:contrat_id>/', views_validation_paiements.historique_validation_paiements, name='historique_validation_paiements'),
]
