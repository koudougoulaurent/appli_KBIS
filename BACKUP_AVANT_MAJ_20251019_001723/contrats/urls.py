from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views, views_contrat_pdf_updated
from .views import contrat_list, quittance_list, etat_lieux_list

app_name = 'contrats'

# Router pour les API REST
router = DefaultRouter()
router.register(r'api/contrats', api_views.ContratViewSet)
router.register(r'api/quittances', api_views.QuittanceViewSet)
router.register(r'api/etats-lieux', api_views.EtatLieuxViewSet)
router.register(r'api/cautions', api_views.CautionViewSet, basename='caution')

urlpatterns = [
    # Autocomplete intelligent désactivé (DAL non compatible)
    # Dashboard principal des contrats
    path('', views.contrats_dashboard, name='dashboard'),
    # API REST
    path('api/', include(router.urls)),
    # URLs pour les pages web (avec aliases pour compatibilité)
    # ...existing code...
    path('liste/', contrat_list, name='liste'),
    path('detail/<int:pk>/', views.detail_contrat, name='detail'),
    path('ajouter/', views.ajouter_contrat, name='ajouter'),
    path('modifier/<int:pk>/', views.modifier_contrat, name='modifier'),
    path('resilier/<int:pk>/', views.resilier_contrat, name='resilier'),
    path('supprimer/<int:pk>/', views.SupprimerContratView.as_view(), name='supprimer_contrat'),
    
    # URLs pour les quittances
    path('quittances/', quittance_list, name='quittances_liste'),
    path('quittances/detail/<int:pk>/', views.detail_quittance, name='quittance_detail'),
    path('quittances/ajouter/', views.ajouter_quittance, name='quittance_ajouter'),
    
    # URLs pour les états des lieux
    path('etats-lieux/', etat_lieux_list, name='etats_lieux_liste'),
    path('etats-lieux/detail/<int:pk>/', views.detail_etat_lieux, name='etat_lieux_detail'),
    path('etats-lieux/ajouter/', views.ajouter_etat_lieux, name='etat_lieux_ajouter'),
    path('etats-lieux/modifier/<int:pk>/', views.modifier_etat_lieux, name='etat_lieux_modifier'),
    path('etats-lieux/supprimer/<int:pk>/', views.supprimer_etat_lieux, name='etat_lieux_supprimer'),
    
    # URLs pour les contrats orphelins
    path('orphelins/', views.contrats_orphelins, name='orphelins'),
    
    # Vue d'occupation des propriétés
    path('occupation-propriete/<int:propriete_id>/', views.occupation_propriete, name='occupation_propriete'),

    # URLs pour la gestion des cautions et avances
    path('cautions/', views.liste_contrats_caution, name='liste_contrats_caution'),
    path('cautions/<int:contrat_id>/', views.detail_contrat_caution, name='detail_contrat_caution'),
    path('cautions/<int:contrat_id>/marquer-caution/', views.marquer_caution_payee, name='marquer_caution_payee'),
    path('cautions/<int:contrat_id>/marquer-avance/', views.marquer_avance_payee, name='marquer_avance_payee'),
    path('cautions/<int:contrat_id>/imprimer-recu/', views.imprimer_recu_caution, name='imprimer_recu_caution'),
    path('cautions/<int:contrat_id>/imprimer-contrat/', views.imprimer_document_contrat, name='imprimer_document_contrat'),
    
    # URL pour la gestion globale des cautions
    path('gestion-cautions/', views.gestion_cautions, name='gestion_cautions'),
    path('forcer-correction-statuts/', views.forcer_correction_statuts, name='forcer_correction_statuts'),

    # URLs pour la gestion des résiliations
    path('resiliations/', views.liste_resiliations, name='liste_resiliations'),
    path('resiliations/selectionner-contrat/', views.selectionner_contrat_resiliation, name='selectionner_contrat_resiliation'),
    path('resiliations/professionnelle/<int:pk>/', views.resiliation_professionnelle, name='resiliation_professionnelle'),
    path('resiliations/telecharger-pdf/<int:pk>/', views.telecharger_resiliation_pdf, name='telecharger_resiliation_pdf'),
    path('resiliations/creer/<int:contrat_id>/', views.creer_resiliation, name='creer_resiliation'),
    path('resiliations/<int:resiliation_id>/', views.detail_resiliation, name='detail_resiliation'),
    path('resiliations/<int:resiliation_id>/valider/', views.valider_resiliation, name='valider_resiliation'),
    path('resiliations/<int:resiliation_id>/supprimer/', views.supprimer_resiliation, name='supprimer_resiliation'),
    
    # URLs pour la génération PDF
    path('generer-pdf/<int:pk>/', views.generer_contrat_pdf, name='generer_contrat_pdf'),
    path('resiliations/generer-pdf/<int:pk>/', views.generer_resiliation_pdf, name='generer_resiliation_pdf'),
    path('generer-resiliation-pdf/<int:pk>/', views.generer_resiliation_contrat_pdf, name='generer_resiliation_contrat_pdf'),
    
    # URLs pour la génération PDF avec templates mis à jour
    path('generer-pdf-updated/<int:pk>/', views_contrat_pdf_updated.generer_contrat_pdf_updated, name='generer_contrat_pdf_updated'),
    path('generer-etat-lieux-pdf/<int:pk>/', views_contrat_pdf_updated.generer_etat_lieux_pdf, name='generer_etat_lieux_pdf'),
    path('generer-garantie-pdf/<int:pk>/', views_contrat_pdf_updated.generer_garantie_pdf, name='generer_garantie_pdf'),
    path('generer-documents-complets/<int:pk>/', views_contrat_pdf_updated.generer_documents_complets, name='generer_documents_complets'),
    path('auto-remplir/<int:pk>/', views_contrat_pdf_updated.auto_remplir_contrat, name='auto_remplir_contrat'),
] 