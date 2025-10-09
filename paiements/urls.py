from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views, views_retraits, views_recapitulatifs, views_recus, api_intelligente_retraits, views_charges_avancees, views_validation, views_unites_locatives, views_quick_actions, views_kbis_recus, views_retraits_charges, views_retrait_ameliore, views_avance
# from . import views_locataire_paiements

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
    # path('dashboard-recaps/', views.dashboard_recaps_simple, name='dashboard_recaps_simple'),  # Fonction non disponible
    path('liste/', views.paiement_list, name='liste'),  # Alias principal pour compatibilité
    path('detail/<int:pk>/', views.paiement_detail, name='detail'),  # Alias principal pour compatibilité
    path('ajouter/', views.ajouter_paiement, name='ajouter'),  # Alias principal pour compatibilité
    
    # URLs pour les quittances de paiement bailleur (fonctions non disponibles)
    # path('quittances-bailleur/', views.liste_quittances_bailleur, name='liste_quittances_bailleur'),
    # path('quittance-bailleur/<int:pk>/', views.quittance_bailleur_detail, name='quittance_bailleur_detail'),
    # path('quittance-bailleur/<int:pk>/telecharger/', views.telecharger_quittance_bailleur, name='telecharger_quittance_bailleur'),
    # path('generer-quittance-bailleur/<int:retrait_id>/', views.generer_quittance_bailleur, name='generer_quittance_bailleur'),
    
    # URLs pour les paiements des locataires
    path('locataire/<int:locataire_id>/', views_quick_actions.liste_paiements, name='paiements_locataire'),
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
    path('retraits-bailleur/recap/<int:bailleur_id>/', views.recap_retrait_bailleur, name='recap_retrait_bailleur'),
    path('retraits-bailleur/creer-depuis-recap/', views.creer_retrait_depuis_recap, name='creer_retrait_depuis_recap'),
    path('modifier/<int:pk>/', views.modifier_paiement, name='modifier_paiement'),
    path('supprimer/<int:pk>/', views.SupprimerPaiementView.as_view(), name='supprimer_paiement'),
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
    path('retraits/', views.liste_retraits_bailleur, name='retraits_liste'),
    path('retrait/ajouter/', views.ajouter_retrait, name='retrait_ajouter'),
    path('retrait/<int:pk>/', views.detail_retrait, name='retrait_detail'),
    path('retrait/<int:pk>/modifier/', views.modifier_retrait, name='retrait_modifier'),
    
    # Actions sur les retraits (déjà définies plus haut)
    
    # Gestion des reçus de retrait (à implémenter)
    
    # Alias pour compatibilité
    path('retraits_liste/', views.liste_retraits_bailleur, name='retraits_liste'),
    path('retrait_ajouter/', views.ajouter_retrait, name='retrait_ajouter'),
    path('retrait_detail/<int:pk>/', views.detail_retrait, name='retrait_detail'),
    path('retrait_modifier/<int:pk>/', views.modifier_retrait, name='retrait_modifier'),
    
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
    path('retraits-bailleurs/', views_retraits.liste_retraits, name='retraits_liste'),
    path('retraits-bailleurs/auto-create/', views_retraits.creer_retrait_automatique, name='retrait_auto_create'),
    path('retraits-bailleurs/auto-create-ameliore/', views_retrait_ameliore.creer_retrait_automatique_ameliore, name='retrait_auto_create_ameliore'),
    path('retraits-bailleurs/api/contrat-details/', views_retrait_ameliore.get_contrat_details_ajax, name='api_contrat_details'),
    path('retraits-bailleurs/<int:pk>/', views_retraits.detail_retrait, name='retrait_detail'),
    path('retraits-bailleurs/<int:pk>/valider/', views_retraits.valider_retrait, name='valider_retrait'),
    path('retraits-bailleurs/<int:pk>/marquer-paye/', views_retraits.marquer_paye, name='marquer_retrait_paye'),
    path('retraits-bailleurs/<int:pk>/generer-quittance/', views_retraits.generer_quittance, name='generer_quittance_retrait'),
    path('retraits-bailleurs/<int:pk>/telecharger-quittance/', views_retraits.telecharger_quittance, name='telecharger_quittance_retrait'),
    path('retraits-bailleurs/<int:pk>/supprimer/', views_retraits.supprimer_retrait, name='supprimer_retrait'),
    
    # URLs pour l'intégration des charges dans les retraits
    path('retraits-bailleurs/<int:retrait_id>/integrer-charges/', views_retraits_charges.integrer_charges_retrait, name='integrer_charges_retrait'),
    path('retraits-bailleurs/<int:retrait_id>/integrer-charge/<int:charge_id>/', views_retraits_charges.integrer_charge_specifique, name='integrer_charge_specifique'),
    path('retraits-bailleurs/<int:retrait_id>/retirer-charge/<int:charge_id>/', views_retraits_charges.retirer_charge_retrait, name='retirer_charge_retrait'),
    path('retraits-bailleurs/<int:retrait_id>/charges-disponibles/', views_retraits_charges.ajax_charges_disponibles, name='ajax_charges_disponibles'),

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
    
    # URLs pour la suppression des récapitulatifs (superuser et PRIVILEGE uniquement)
    path('recaps-mensuels-automatiques/<int:recap_id>/supprimer/', views.supprimer_recap_mensuel, name='supprimer_recap_mensuel'),
    path('recaps-mensuels-automatiques/<int:recap_id>/restaurer/', views.restaurer_recap_mensuel, name='restaurer_recap_mensuel'),
    path('recaps-mensuels-automatiques/supprimes/', views.liste_recaps_supprimes, name='liste_recaps_supprimes'),
    
    

    # ✅ SYSTÈME DE VALIDATION DES PAIEMENTS
    path('paiement/<int:pk>/valider/', views.valider_paiement, name='valider_paiement'),
    path('paiement/<int:pk>/refuser/', views.refuser_paiement, name='refuser_paiement'),
    
    # 🔍 API DE RECHERCHE INTELLIGENTE
    path('api/recherche-rapide/', api_views.api_recherche_contrats_rapide, name='api_recherche_rapide'),
    path('api/recherche-bailleur/', api_views.api_recherche_bailleur, name='api_recherche_bailleur'),
    path('api/contexte-intelligent/contrat/<int:contrat_id>/', api_views.api_contexte_intelligent_contrat, name='api_contexte_intelligent'),
    path('api/creer-avance-rapide/', api_views.api_creer_avance_rapide, name='api_creer_avance_rapide'),
    path('api/convertir-avances-existantes/', api_views.api_convertir_avances_existantes, name='api_convertir_avances_existantes'),
    path('api/convertir-toutes-avances-existantes/', api_views.api_convertir_toutes_avances_existantes, name='api_convertir_toutes_avances_existantes'),
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
    
    # 📄 RÉCÉPISSÉS KBIS DYNAMIQUES
    path('paiement/<int:paiement_pk>/recu-kbis/', views_kbis_recus.generer_recu_kbis_dynamique, name='generer_recu_kbis_dynamique'),
    
    # 📄 QUITTANCES DE RETRAIT KBIS DYNAMIQUES
    path('retrait/<int:retrait_pk>/quittance-kbis/', views_kbis_recus.generer_quittance_retrait_kbis, name='generer_quittance_retrait_kbis'),
    
    # 🔧 VUE DE TEST POUR RÉCAPITULATIFS
    path('recaps-mensuels/creer-test/', views_recapitulatifs.creer_recapitulatif_test, name='creer_recapitulatif_test'),
    
    # 📄 RÉCAPITULATIFS KBIS A4 PAYSAGE
    path('recapitulatifs/<int:recapitulatif_id>/kbis/', views_recapitulatifs.generer_recapitulatif_kbis, name='generer_recapitulatif_kbis'),
    
    # 🏠 SYSTÈME D'AVANCES DE LOYER - NOUVEAU !
    path('avances/', include(('paiements.urls_avance', 'avances'))),
    
    # Redirection pour compatibilité avec les anciens liens
    path('historique/contrat/<int:contrat_id>/', views_avance.historique_paiements_contrat, name='historique_contrat_old'),
    
    # 📄 GÉNÉRATION PDF DES RETRAITS AVEC TEMPLATES
    path('retraits/<int:retrait_id>/pdf/', views_retrait_ameliore.generer_pdf_retrait, name='generer_pdf_retrait'),
    path('retraits/pdf-multiple/', views_retrait_ameliore.generer_pdf_retraits_multiple, name='generer_pdf_retraits_multiple'),
    path('retraits/pdf-mois/', views_retrait_ameliore.generer_pdf_retraits_mois, name='generer_pdf_retraits_mois'),
]
