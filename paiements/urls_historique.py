"""
URLs pour l'historique des paiements
"""

from django.urls import path
from . import views_historique, views_historique_accueil

app_name = 'historique'

urlpatterns = [
    # Page d'accueil de l'historique
    path('', views_historique_accueil.accueil_historique_paiements, name='accueil'),
    
    # Historique par contrat
    path('contrat/<int:contrat_id>/', views_historique.historique_paiements_contrat, name='historique_contrat'),
    path('contrat/<int:contrat_id>/imprimer/', views_historique.historique_paiements_contrat_imprimer, name='historique_contrat_imprimer'),
    path('contrat/<int:contrat_id>/ajax/', views_historique.historique_paiements_ajax, name='historique_contrat_ajax'),
    
    # Historique par locataire
    path('locataire/<int:locataire_id>/', views_historique.historique_paiements_locataire, name='historique_locataire'),
]
