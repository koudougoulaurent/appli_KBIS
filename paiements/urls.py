from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, views_ajax, api_views, views_retraits, views_recapitulatifs, views_recus, api_intelligente_retraits, views_charges_avancees, views_validation, views_unites_locatives, views_retraits_bailleur, views_quick_actions
# from . import views_locataire_paiements

app_name = 'paiements'

# Router pour les API REST
router = DefaultRouter()
router.register(r'api/paiements', api_views.PaiementViewSet)
router.register(r'api/cautions-avances', api_views.PaiementCautionAvanceViewSet, basename='paiement-caution-avance')

urlpatterns = [
    # API REST
    path('', include(router.urls)),
    
    # URLs pour les accords de paiement
    path('accords/dashboard/', views.dashboard_paiements_partiels, name='dashboard_partiels'),
    path('accords/liste/', views.liste_plans_paiement, name='liste_plans_partiels'),
    path('accords/creer/', views.creer_plan_paiement, name='creer_plan_partiel'),
    path('accords/<uuid:plan_id>/', views.detail_plan_paiement, name='detail_plan_partiel'),
    
    # URLs AJAX pour les fonctionnalités avancées
    path('api/plans/<uuid:plan_id>/', views_ajax.get_plan_details, name='api_plan_details'),
    path('api/plans/quick-payment/', views_ajax.create_quick_payment, name='api_quick_payment'),
    path('api/plans/bulk-update/', views_ajax.bulk_update_plans, name='api_bulk_update'),
    path('api/plans/data/', views_ajax.get_plans_data, name='api_plans_data'),
    path('api/plans/calculate-schedule/', views_ajax.calculate_plan_schedule, name='api_calculate_schedule'),
    path('api/plans/search/', views_ajax.search_plans, name='api_search_plans'),
    
    # URLs pour les paiements (avec aliases pour compatibilité)
    path('dashboard/', views.paiements_dashboard, name='dashboard'),
    path('liste/', views.paiement_list, name='liste'),  # Alias principal pour compatibilité
    path('detail/<int:pk>/', views.paiement_detail, name='detail'),  # Alias principal pour compatibilité
    path('ajouter/', views.ajouter_paiement, name='ajouter'),  # Alias principal pour compatibilité
    path('ajouter-partiel/', views.ajouter_paiement_partiel, name='ajouter_partiel'),  # Vue spécialisée pour paiements partiels
    path('liste-partiels/', views.liste_paiements_partiels, name='liste_partiels'),  # Liste spécifique des paiements partiels
    
    # URLs pour les paiements des locataires
    path('locataire/<int:locataire_id>/', views_quick_actions.liste_paiements, name='paiements_locataire'),

    # Vue historique des paiements partiels
    path('historique-partiel/<int:contrat_id>/<int:mois>/<int:annee>/', views.historique_paiements_partiels, name='historique_partiel'),
    # path('locataire/<int:locataire_id>/api/', views_locataire_paiements.paiements_locataire_json, name='paiements_locataire_json'),
    
    # Aliases pour compatibilité avec les templates existants
    path('paiement_list/', views.paiement_list, name='paiement_list'),
    path('paiement_detail/<int:pk>/', views.paiement_detail, name='paiement_detail'),
    
    # URLs manquantes pour compatibilité avec les templates existants
    path('recus/', views.liste_recus, name='recus_liste'),
    
    # URLs pour la validation des paiements
    path('paiement/<int:pk>/valider/', views_validation.valider_paiement, name='valider_paiement'),
    path('paiement/<int:pk>/refuser/', views_validation.refuser_paiement, name='refuser_paiement'),
    path('paiement/<int:pk>/annuler/', views_validation.annuler_paiement, name='annuler_paiement'),
    path('paiement/<int:pk>/actions/', views_validation.paiement_actions_ajax, name='paiement_actions_ajax'),
    
    # RÉCAPITULATIFS MENSUELS - NOUVEAU SYSTÈME COMPLET
    # Redirection de l'ancien système vers le nouveau pour compatibilité
    path('recaps-mensuels/', views_recapitulatifs.liste_recapitulatifs, name='liste_recaps_mensuels'),
    path('recaps-mensuels/creer/', views_recapitulatifs.creer_recapitulatif, name='creer_recap_mensuel'),
    path('recaps-mensuels/<int:recapitulatif_id>/', views_recapitulatifs.detail_recapitulatif, name='detail_recap_mensuel'),
    path('recaps-mensuels/<int:recapitulatif_id>/valider/', views_recapitulatifs.valider_recapitulatif, name='valider_recap_mensuel'),
    path('recaps-mensuels/<int:recapitulatif_id>/marquer-envoye/', views_recapitulatifs.envoyer_recapitulatif, name='marquer_recap_envoye'),
    path('recaps-mensuels/<int:recapitulatif_id>/marquer-paye/', views_recapitulatifs.marquer_paye_recapitulatif, name='marquer_recap_paye'),
    path('recaps-mensuels/<int:recapitulatif_id>/imprimer/', views_recapitulatifs.apercu_recapitulatif, name='imprimer_recap_mensuel'),
    
    # NOUVELLES FONCTIONNALITÉS AVANCÉES pour l'ancien système
    path('recaps-mensuels/<int:recapitulatif_id>/pdf/', views_recapitulatifs.telecharger_pdf_recapitulatif, name='telecharger_pdf_recap_mensuel'),
    path('recaps-mensuels/<int:recapitulatif_id>/apercu/', views_recapitulatifs.apercu_recapitulatif, name='apercu_recap_mensuel'),
    path('recaps-mensuels/statistiques/', views_recapitulatifs.statistiques_recapitulatifs, name='statistiques_recaps_mensuels'),
    path('recaps-mensuels/generer-automatique/', views_recapitulatifs.generer_recapitulatif_automatique, name='generer_recap_automatique'),
    
    # NOUVELLES URLs pour le système automatisé
    path('recaps-mensuels-automatiques/', views.liste_recaps_mensuels, name='liste_recaps_mensuels_auto'),
    path('recaps-mensuels-automatiques/creer/', views.creer_recap_mensuel, name='creer_recap_mensuel_auto'),
    path('recaps-mensuels-automatiques/creer/<int:bailleur_id>/', views.creer_recap_mensuel_bailleur, name='creer_recap_mensuel_bailleur'),
    path('recaps-mensuels-automatiques/api/calcul-preview/', views.get_calculation_preview, name='api_calculation_preview'),
    path('recaps-mensuels-automatiques/creer-avec-detection/<int:bailleur_id>/', views.creer_recap_avec_detection_auto, name='creer_recap_avec_detection_auto'),
    path('recaps-mensuels-automatiques/<int:recap_id>/', views.detail_recap_mensuel, name='detail_recap_mensuel_auto'),
    path('recaps-mensuels-automatiques/<int:recap_id>/pdf-detaille/', views.generer_pdf_recap_detaille_paysage, name='generer_pdf_recap_detaille_paysage'),
    path('recaps-mensuels-automatiques/<int:recap_id>/creer-retrait/', views.creer_retrait_depuis_recap, name='creer_retrait_depuis_recap'),
    path('recaps-mensuels-automatiques/generer/', views.generer_recap_mensuel_automatique, name='generer_recap_mensuel_automatique'),
    
    # Tableau de bord spécialisé
    path('recaps-mensuels-automatiques/tableau-bord/', views.tableau_bord_recaps_mensuels, name='tableau_bord_recaps_mensuels'),
    path('recaps-mensuels-automatiques/bailleurs/', views.liste_bailleurs_recaps, name='liste_bailleurs_recaps'),
    
    path('retraits-bailleur/', views.liste_retraits_bailleur, name='liste_retraits_bailleur'),
    path('modifier/<int:pk>/', views.modifier_paiement, name='modifier_paiement'),
    path('supprimer/<int:pk>/', views.supprimer_paiement, name='supprimer_paiement'),
    path('valider/<int:pk>/', views.valider_paiement, name='valider_paiement'),
    
    # URLs pour les charges déductibles
    path('charges/', views.charge_deductible_list, name='charge_deductible_list'),
    path('charges/ajouter/', views.ajouter_charge_deductible, name='ajouter_charge_deductible'),
    path('charges/modifier/<int:pk>/', views.modifier_charge_deductible, name='modifier_charge_deductible'),
    
    # URLs pour la gestion avancée des charges
    path('charges-avancees/', views_charges_avancees.liste_charges_avancees, name='liste_charges_avancees'),
    path('charges-avancees/creer/', views_charges_avancees.creer_charge_avancee, name='creer_charge_avancee'),
    path('charges-avancees/creer/<int:bailleur_id>/', views_charges_avancees.creer_charge_avancee, name='creer_charge_avancee_bailleur'),
    path('charges-avancees/modifier/<int:charge_id>/', views_charges_avancees.modifier_charge_avancee, name='modifier_charge_avancee'),
    path('charges-avancees/detail/<int:charge_id>/', views_charges_avancees.detail_charge_avancee, name='detail_charge_avancee'),
    path('charges-avancees/valider/', views_charges_avancees.valider_charges, name='valider_charges'),
    path('charges-avancees/dashboard/<int:bailleur_id>/', views_charges_avancees.dashboard_charges_bailleur, name='dashboard_charges_bailleur'),
    path('charges-avancees/rapport/', views_charges_avancees.rapport_charges, name='rapport_charges'),
    path('api/charges-bailleur/<int:bailleur_id>/', views_charges_avancees.api_charges_bailleur, name='api_charges_bailleur'),
    
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
    
    # URLs spécifiques pour les retraits des bailleurs
    path('retraits-bailleur/<int:pk>/', views_retraits_bailleur.retraits_bailleur, name='retraits_bailleur'),
    path('retrait-bailleur/<int:pk>/', views_retraits_bailleur.detail_retrait_bailleur, name='detail_retrait_bailleur'),
    path('retrait-bailleur/ajouter/<int:bailleur_id>/', views_retraits_bailleur.ajouter_retrait_bailleur, name='ajouter_retrait_bailleur'),
    path('retrait-bailleur/modifier/<int:pk>/', views_retraits_bailleur.modifier_retrait_bailleur, name='modifier_retrait_bailleur'),
    path('retrait-bailleur/valider/<int:pk>/', views_retraits_bailleur.valider_retrait, name='valider_retrait'),
    path('retrait-bailleur/marquer-paye/<int:pk>/', views_retraits_bailleur.marquer_paye_retrait, name='marquer_paye_retrait'),
    path('retrait-bailleur/generer-recu/<int:pk>/', views_retraits_bailleur.generer_recu_retrait, name='generer_recu_retrait'),
    path('retrait-bailleur/export/<int:bailleur_id>/', views_retraits_bailleur.export_retraits_bailleur, name='export_retraits_bailleur'),
    path('retrait-bailleur/rapport/<int:bailleur_id>/', views_retraits_bailleur.generer_rapport_retraits, name='generer_rapport_retraits'),

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
    
    # URLs pour les reçus de récapitulatifs
    path('recus-recapitulatifs/', views_recus.liste_recus_recapitulatifs, name='liste_recus_recapitulatifs'),
    path('recus-recapitulatifs/statistiques/', views_recus.statistiques_recus_recapitulatifs, name='statistiques_recus_recapitulatifs'),
    path('recus-recapitulatifs/creer/<int:recapitulatif_id>/', views_recus.creer_recu_recapitulatif, name='creer_recu_recapitulatif'),
    path('recus-recapitulatifs/<int:pk>/', views_recus.detail_recu_recapitulatif, name='detail_recu_recapitulatif'),
    path('recus-recapitulatifs/<int:pk>/apercu/', views_recus.apercu_recu_recapitulatif, name='apercu_recu_recapitulatif'),
    path('recus-recapitulatifs/<int:pk>/imprimer/', views_recus.imprimer_recu_recapitulatif, name='imprimer_recu_recapitulatif'),
    path('recus-recapitulatifs/<int:pk>/marquer-envoye/', views_recus.marquer_recu_envoye, name='marquer_recu_envoye'),
    path('recus-recapitulatifs/<int:pk>/valider/', views_recus.valider_recu_recapitulatif, name='valider_recu_recapitulatif'),
    
    # URLs pour les reçus GESTIMMOB
    path('recus-recapitulatifs/<int:pk>/apercu-gestimmob/', views_recus.apercu_recu_recapitulatif_gestimmob, name='apercu_recu_recapitulatif_gestimmob'),
    path('recus-recapitulatifs/<int:pk>/imprimer-gestimmob/', views_recus.imprimer_recu_recapitulatif_gestimmob, name='imprimer_recu_recapitulatif_gestimmob'),
    path('recus-recapitulatifs/creer-gestimmob/<int:recapitulatif_id>/', views_recus.creer_recu_gestimmob_recapitulatif, name='creer_recu_gestimmob_recapitulatif'),

    # URLs pour la génération PDF
    path('recaps-mensuels-automatiques/<int:recap_id>/pdf/', views.generer_pdf_recap_mensuel, name='generer_pdf_recap_mensuel'),
    path('recaps-mensuels-automatiques/<int:recap_id>/apercu/', views.apercu_pdf_recap_mensuel, name='apercu_pdf_recap_mensuel'),
    path('recaps-mensuels-automatiques/pdf-lot/', views.generer_pdf_recaps_lot, name='generer_pdf_recaps_lot'),

    # ✅ SYSTÈME DE VALIDATION DES PAIEMENTS
    path('paiement/<int:pk>/valider/', views.valider_paiement, name='valider_paiement'),
    path('paiement/<int:pk>/refuser/', views.refuser_paiement, name='refuser_paiement'),
    
    # 🔍 API DE RECHERCHE INTELLIGENTE
    path('api/recherche-rapide/', api_views.api_recherche_contrats_rapide, name='api_recherche_rapide'),
    path('api/recherche-bailleur/', api_views.api_recherche_bailleur, name='api_recherche_bailleur'),
    path('api/contexte-intelligent/contrat/<int:contrat_id>/', api_views.api_contexte_intelligent_contrat, name='api_contexte_intelligent'),
    path('api/verifier-doublon/', api_views.api_verifier_doublon_paiement, name='api_verifier_doublon'),
    # 🚀 API INTELLIGENTE DES RETRAITS - NOUVEAU !
    path('api/contexte-bailleur/<int:bailleur_id>/', api_intelligente_retraits.APIContexteIntelligentRetraits.as_view(), name='api_contexte_bailleur'),
    path('api/retraits-intelligents/contexte/<int:bailleur_id>/', api_intelligente_retraits.APIContexteIntelligentRetraits.as_view(), name='api_retraits_intelligents_contexte'),
    path('api/retraits-intelligents/suggestions/<int:bailleur_id>/', api_intelligente_retraits.api_suggestions_retrait, name='api_retraits_intelligents_suggestions'),
    path('api/retraits-intelligents/contexte-rapide/<int:bailleur_id>/', api_intelligente_retraits.api_contexte_rapide_retrait, name='api_retraits_intelligents_contexte_rapide'),
    path('api/retraits-intelligents/historique/<int:bailleur_id>/', api_intelligente_retraits.api_historique_retraits, name='api_retraits_intelligents_historique'),
    path('api/retraits-intelligents/alertes/<int:bailleur_id>/', api_intelligente_retraits.api_alertes_retrait, name='api_retraits_intelligents_alertes'),

    # ✅ SYSTÈME DES UNITÉS LOCATIVES
    path('unites-locatives/rapport/<int:bailleur_id>/', views_unites_locatives.rapport_unites_locatives, name='rapport_unites_locatives'),
    path('unites-locatives/retrait/creer/<int:bailleur_id>/', views_unites_locatives.creer_retrait_avec_unites, name='creer_retrait_avec_unites'),
    path('unites-locatives/retrait/detail/<int:retrait_id>/', views_unites_locatives.detail_retrait_avec_unites, name='detail_retrait_avec_unites'),
    path('unites-locatives/api/donnees/<int:bailleur_id>/', views_unites_locatives.api_donnees_unites_locatives, name='api_donnees_unites_locatives'),
    path('unites-locatives/export/excel/<int:bailleur_id>/', views_unites_locatives.export_rapport_unites_excel, name='export_rapport_unites_excel'),
]
