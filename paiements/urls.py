from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views, views_retraits, views_recapitulatifs

app_name = 'paiements'

# Router pour les API REST
router = DefaultRouter()
router.register(r'api/paiements', api_views.PaiementViewSet)
router.register(r'api/cautions-avances', api_views.PaiementCautionAvanceViewSet, basename='paiement-caution-avance')

urlpatterns = [
    # API REST
    path('', include(router.urls)),
    
    # URLs pour les paiements (avec aliases pour compatibilité)
    path('dashboard/', views.paiements_dashboard, name='dashboard'),
    path('liste/', views.paiement_list, name='liste'),  # Alias principal pour compatibilité
    path('detail/<int:pk>/', views.paiement_detail, name='detail'),  # Alias principal pour compatibilité
    path('ajouter/', views.ajouter_paiement, name='ajouter'),  # Alias principal pour compatibilité
    
    # Aliases pour compatibilité avec les templates existants
    path('paiement_list/', views.paiement_list, name='paiement_list'),
    path('paiement_detail/<int:pk>/', views.paiement_detail, name='paiement_detail'),
    
    # URLs manquantes pour compatibilité avec les templates existants
    path('recus/', views.liste_recus, name='recus_liste'),
    
    # RÉCAPITULATIFS MENSUELS - NOUVEAU SYSTÈME COMPLET
    # Redirection de l'ancien système vers le nouveau pour compatibilité
    path('recaps-mensuels/', views_recapitulatifs.liste_recapitulatifs, name='liste_recaps_mensuels'),
    path('recaps-mensuels/creer/', views_recapitulatifs.creer_recapitulatif, name='creer_recap_mensuel'),
    path('recaps-mensuels/<int:recap_id>/', views_recapitulatifs.detail_recapitulatif, name='detail_recap_mensuel'),
    path('recaps-mensuels/<int:recap_id>/valider/', views_recapitulatifs.valider_recapitulatif, name='valider_recap_mensuel'),
    path('recaps-mensuels/<int:recap_id>/marquer-envoye/', views_recapitulatifs.envoyer_recapitulatif, name='marquer_recap_envoye'),
    path('recaps-mensuels/<int:recap_id>/marquer-paye/', views_recapitulatifs.marquer_paye_recapitulatif, name='marquer_recap_paye'),
    path('recaps-mensuels/<int:recap_id>/imprimer/', views_recapitulatifs.apercu_recapitulatif, name='imprimer_recap_mensuel'),
    
    # NOUVELLES FONCTIONNALITÉS AVANCÉES pour l'ancien système
    path('recaps-mensuels/<int:recap_id>/pdf/', views_recapitulatifs.telecharger_pdf_recapitulatif, name='telecharger_pdf_recap_mensuel'),
    path('recaps-mensuels/<int:recap_id>/apercu/', views_recapitulatifs.apercu_recapitulatif, name='apercu_recap_mensuel'),
    path('recaps-mensuels/statistiques/', views_recapitulatifs.statistiques_recapitulatifs, name='statistiques_recaps_mensuels'),
    path('recaps-mensuels/generer-automatique/', views_recapitulatifs.generer_recapitulatif_automatique, name='generer_recap_automatique'),
    path('retraits-bailleur/', views.liste_retraits_bailleur, name='liste_retraits_bailleur'),
    path('modifier/<int:pk>/', views.modifier_paiement, name='modifier_paiement'),
    path('supprimer/<int:pk>/', views.supprimer_paiement, name='supprimer_paiement'),
    path('valider/<int:pk>/', views.valider_paiement, name='valider_paiement'),
    
    # URLs pour les charges déductibles
    path('charges/', views.charge_deductible_list, name='charge_deductible_list'),
    path('charges/ajouter/', views.ajouter_charge_deductible, name='ajouter_charge_deductible'),
    path('charges/modifier/<int:pk>/', views.modifier_charge_deductible, name='modifier_charge_deductible'),
    
    # API pour les données des paiements
    path('api/data/', views.api_paiements_data, name='api_paiements_data'),
    
    # Recherche intelligente
    path('recherche/', views.recherche_intelligente_paiements, name='recherche_intelligente'),
    
    # URLs pour les retraits (placeholder views)
    path('retraits/', views_retraits.retrait_list, name='retraits_liste'),
    path('retrait/ajouter/', views_retraits.retrait_create, name='retrait_ajouter'),
    path('retrait/<int:pk>/', views_retraits.retrait_detail, name='retrait_detail'),
    path('retrait/<int:pk>/modifier/', views_retraits.retrait_edit, name='retrait_modifier'),
    
    # Actions sur les retraits
    path('retrait/<int:pk>/validate/', views_retraits.retrait_validate, name='retrait_validate'),
    path('retrait/<int:pk>/mark-paid/', views_retraits.retrait_mark_paid, name='retrait_mark_paid'),
    path('retrait/<int:pk>/cancel/', views_retraits.retrait_cancel, name='retrait_cancel'),
    
    # Gestion des reçus de retrait
    path('recu/<int:recu_id>/', views_retraits.recu_retrait_view, name='recu_view'),
    path('recu/<int:recu_id>/print/', views_retraits.recu_retrait_print, name='recu_print'),
    
    # Alias pour compatibilité
    path('retraits_liste/', views_retraits.retrait_list, name='retraits_liste'),
    path('retrait_ajouter/', views_retraits.retrait_create, name='retrait_ajouter'),
    path('retrait_detail/<int:pk>/', views_retraits.retrait_detail, name='retrait_detail'),
    path('retrait_modifier/<int:pk>/', views_retraits.retrait_edit, name='retrait_modifier'),
    
    # URLs pour les paiements de caution et avance
    path('caution-avance/ajouter/', views.paiement_caution_avance_create, name='paiement_caution_avance_create'),
    path('caution-avance/liste/', views.paiement_caution_avance_list, name='paiement_caution_avance_list'),
    
    # URLs pour les tableaux de bord
    path('tableaux-bord/', views.tableau_bord_list, name='tableau_bord_list'),
    path('tableaux-bord/dashboard/', views.tableau_bord_dashboard, name='tableau_bord_dashboard'),
    path('tableaux-bord/ajouter/', views.tableau_bord_create, name='tableau_bord_create'),
    path('tableaux-bord/<int:pk>/', views.tableau_bord_detail, name='tableau_bord_detail'),
    path('tableaux-bord/<int:pk>/modifier/', views.tableau_bord_update, name='tableau_bord_update'),
    path('tableaux-bord/<int:pk>/supprimer/', views.tableau_bord_delete, name='tableau_bord_delete'),
    path('tableaux-bord/<int:pk>/export-pdf/', views.tableau_bord_export_pdf, name='tableau_bord_export_pdf'),
    
    # URLs pour les quittances de paiement
    path('quittances/', views.quittance_list, name='quittance_list'),
    path('quittance/<int:pk>/', views.quittance_detail, name='quittance_detail'),
    path('quittance/<int:pk>/imprimee/', views.marquer_quittance_imprimee, name='marquer_quittance_imprimee'),
    path('quittance/<int:pk>/envoyee/', views.marquer_quittance_envoyee, name='marquer_quittance_envoyee'),
    path('quittance/<int:pk>/archivee/', views.marquer_quittance_archivee, name='marquer_quittance_archivee'),
    path('paiement/<int:paiement_pk>/generer-quittance/', views.generer_quittance_manuelle, name='generer_quittance_manuelle'),
    
    # URLs pour les retraits aux bailleurs (nouveau système)
    path('retraits-bailleurs/', include('paiements.urls_retraits')),

    # URLs pour les récapitulatifs mensuels
    path('recapitulatifs/', views_recapitulatifs.liste_recapitulatifs, name='liste_recapitulatifs'),
    path('recapitulatifs/creer/', views_recapitulatifs.creer_recapitulatif, name='creer_recapitulatif'),
    path('recapitulatifs/<int:recapitulatif_id>/', views_recapitulatifs.detail_recapitulatif, name='detail_recapitulatif'),
    path('recapitulatifs/<int:recapitulatif_id>/valider/', views_recapitulatifs.valider_recapitulatif, name='valider_recapitulatif'),
    path('recapitulatifs/<int:recapitulatif_id>/envoyer/', views_recapitulatifs.envoyer_recapitulatif, name='envoyer_recapitulatif'),
    path('recapitulatifs/<int:recapitulatif_id>/marquer-paye/', views_recapitulatifs.marquer_paye_recapitulatif, name='marquer_paye_recapitulatif'),
    path('recapitulatifs/<int:recapitulatif_id>/pdf/', views_recapitulatifs.telecharger_pdf_recapitulatif, name='telecharger_pdf_recapitulatif'),
    path('recapitulatifs/<int:recapitulatif_id>/apercu/', views_recapitulatifs.apercu_recapitulatif, name='apercu_recapitulatif'),
    path('recapitulatifs/statistiques/', views_recapitulatifs.statistiques_recapitulatifs, name='statistiques_recapitulatifs'),
    path('recapitulatifs/generer-automatique/', views_recapitulatifs.generer_recapitulatif_automatique, name='generer_recapitulatif_automatique'),
]
