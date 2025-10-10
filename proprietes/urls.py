from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views, views_unites, document_views, views_charges_bailleur, document_export_views
from .views import ajouter_charge_bailleur_rapide

# Router pour l'API
router = DefaultRouter()
router.register(r'api/proprietes', api_views.ProprieteViewSet, basename='propriete')
router.register(r'api/bailleurs', api_views.BailleurViewSet, basename='bailleur')
router.register(r'api/locataires', api_views.LocataireViewSet, basename='locataire')
router.register(r'api/charges-communes', api_views.ChargeCommuneViewSet, basename='charge-commune')
router.register(r'api/pieces', api_views.PieceViewSet, basename='piece')

app_name = 'proprietes'

urlpatterns = [
    # Dashboard principal des propriétés
    path('', views.proprietes_dashboard, name='proprietes_dashboard'),
    
    # URLs pour les propriétés (avec aliases pour compatibilité)
    path('liste/', views.liste_proprietes, name='liste'),
    path('ajouter/', views.ajouter_propriete, name='ajouter'),
    path('<int:pk>/', views.detail_propriete, name='detail'),
    path('<int:pk>/ajax/<str:section>/', views.detail_propriete_ajax, name='detail_ajax'),
    path('<int:pk>/modifier/', views.modifier_propriete, name='modifier'),
    path('<int:pk>/supprimer/', views.SupprimerProprieteView.as_view(), name='supprimer_propriete'),
    
    # URLs pour les charges bailleur (anciennes vues)
    path('charges-bailleur/', views.liste_charges_bailleur, name='liste_charges_bailleur'),
    path('charges-bailleur/ajouter/', views.ajouter_charge_bailleur, name='ajouter_charge_bailleur'),
    path('ajouter_charge_bailleur_rapide/', views.ajouter_charge_bailleur_rapide, name='ajouter_charge_bailleur_rapide'),
    
    # URLs pour les charges bailleur (nouvelles vues intelligentes)
    path('charges-bailleur-intelligent/', views_charges_bailleur.liste_charges_bailleur, name='liste_charges_bailleur_intelligent'),
    path('charges-bailleur-intelligent/creer/', views_charges_bailleur.creer_charge_bailleur, name='creer_charge_bailleur'),
    path('charges-bailleur-intelligent/<int:pk>/', views_charges_bailleur.detail_charge_bailleur, name='detail_charge_bailleur'),
    path('charges-bailleur-intelligent/<int:pk>/modifier/', views_charges_bailleur.modifier_charge_bailleur, name='modifier_charge_bailleur'),
    path('charges-bailleur-intelligent/<int:pk>/annuler/', views_charges_bailleur.annuler_charge_bailleur, name='annuler_charge_bailleur'),
    path('charges-bailleur-intelligent/rapport/', views_charges_bailleur.rapport_charges_bailleur, name='rapport_charges_bailleur'),
    path('api/charges-bailleur-mois/', views_charges_bailleur.api_charges_bailleur_mois, name='api_charges_bailleur_mois'),
    path('charges-bailleur/<int:pk>/', views.detail_charge_bailleur, name='detail_charge_bailleur'),
    path('charges-bailleur/<int:pk>/modifier/', views.modifier_charge_bailleur, name='modifier_charge_bailleur'),
    path('charges-bailleur/<int:pk>/deduction/', views.deduction_charge_bailleur, name='deduction_charge_bailleur'),
    path('charges-bailleur/<int:pk>/remboursement/', views.marquer_charge_remboursee, name='marquer_charge_remboursee'),
    
    # URLs pour les bailleurs
    path('bailleurs/', views.liste_bailleurs, name='bailleurs_liste'),
    path('bailleurs/ajouter/', views.ajouter_bailleur, name='ajouter_bailleur'),
    path('bailleurs/<int:pk>/', views.detail_bailleur, name='detail_bailleur'),
    path('bailleurs/<int:pk>/modifier/', views.modifier_bailleur, name='modifier_bailleur'),
    path('bailleurs/<int:pk>/supprimer/', views.SupprimerBailleurView.as_view(), name='supprimer_bailleur'),
    path('bailleurs/<int:pk>/proprietes/', views.proprietes_bailleur, name='proprietes_bailleur'),
    path('bailleurs/recherche-avancee/', views.recherche_avancee_bailleurs, name='recherche_avancee_bailleurs'),
    path('test-actions-rapides/', views.test_quick_actions, name='test_quick_actions'),

    # URLs pour les locataires
    path('locataires/', views.liste_locataires, name='locataires_liste'),
    path('locataires/ajouter/', views.ajouter_locataire, name='ajouter_locataire'),
    path('locataires/<int:pk>/', views.detail_locataire, name='detail_locataire'),
    path('locataires/<int:pk>/modifier/', views.modifier_locataire, name='modifier_locataire'),
    path('locataires/<int:pk>/supprimer/', views.SupprimerLocataireView.as_view(), name='supprimer_locataire'),
    path('locataires/recherche-avancee/', views.recherche_avancee_locataires, name='recherche_avancee_locataires'),
    path('locataires/desactiver/<int:pk>/', views.desactiver_locataire, name='desactiver_locataire'),
    path('locataires/corbeille/', views.corbeille_locataires, name='corbeille_locataires'),
    
    # API URLs
    path('api/<int:propriete_id>/calcul-loyer-net/', views.api_calcul_loyer_net, name='api_calcul_loyer_net'),

    # URLs pour la gestion des photos
    path('propriete/<int:propriete_id>/photos/', views.PhotoListView.as_view(), name='photo_list'),
    path('propriete/<int:propriete_id>/photos/ajouter/', views.PhotoCreateView.as_view(), name='photo_create'),
    path('propriete/<int:propriete_id>/photos/upload-multiple/', views.PhotoMultipleUploadView.as_view(), name='photo_multiple_upload'),
    path('photos/<int:pk>/modifier/', views.PhotoUpdateView.as_view(), name='photo_update'),
    path('photos/<int:pk>/supprimer/', views.PhotoDeleteView.as_view(), name='photo_delete'),
    path('propriete/<int:pk>/galerie/', views.PhotoGalleryView.as_view(), name='photo_gallery'),
    
    # URLs AJAX pour les photos
    path('photos/<int:photo_id>/definir-principale/', views.PhotoSetMainView.as_view(), name='photo_set_main'),
    path('photos/<int:photo_id>/supprimer-ajax/', views.PhotoDeleteAjaxView.as_view(), name='photo_delete_ajax'),
    path('propriete/<int:propriete_id>/photos/reorganiser/', views.PhotoReorderView.as_view(), name='photo_reorder'),

    # URLs pour les documents
    path('documents/', views.document_list, name='document_list'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/ajouter/', views.document_create, name='document_create'),
    path('documents/<int:pk>/modifier/', views.document_update, name='document_update'),
    path('documents/<int:pk>/supprimer/', views.document_delete, name='document_delete'),
    path('documents/<int:pk>/telecharger/', views.document_download, name='document_download'),
    
    # URLs pour l'archivage des documents par entité
    path('documents/archivage/', document_views.document_archive_by_entity, name='document_archive'),
    path('documents/recherche-avancee/', document_views.document_search_advanced, name='document_search_advanced'),
    path('documents/upload-rapide/', document_views.document_quick_upload, name='document_quick_upload'),
    path('documents/propriete/<int:propriete_id>/', document_views.document_list_by_propriete, name='document_list_by_propriete'),
    path('documents/bailleur/<int:bailleur_id>/', document_views.document_list_by_bailleur, name='document_list_by_bailleur'),
    path('documents/locataire/<int:locataire_id>/', document_views.document_list_by_locataire, name='document_list_by_locataire'),
    path('documents/api/stats/', document_views.document_stats_api, name='document_stats_api'),
    
    # URLs pour l'export des documents
    path('documents/export/', document_export_views.document_export, name='document_export'),
    path('documents/export/preview/', document_export_views.document_export_preview, name='document_export_preview'),
    path('documents/export/statistics/', document_export_views.document_export_statistics, name='document_export_statistics'),
    path('documents/export/bulk/', document_export_views.document_bulk_export, name='document_bulk_export'),
    
    # URLs pour le visualiseur universel
    path('documents/<int:pk>/viewer/', views.DocumentViewerView.as_view(), name='document_viewer'),
    path('documents/<int:pk>/viewer/<str:viewer_type>/', views.DocumentViewerView.as_view(), name='document_viewer_typed'),
    path('documents/<int:pk>/content/', views.document_content_view, name='document_content_view'),
    path('documents/<int:pk>/pdf-viewer/', views.document_pdf_viewer, name='document_pdf_viewer'),
    path('documents/<int:pk>/proxy/', views.document_secure_proxy, name='document_secure_proxy'),
    
    # URLs de debug et vues simplifiées
    path('documents/<int:pk>/debug/', views.document_debug_info, name='document_debug_info'),
    path('documents/<int:pk>/test-download/', views.document_test_download, name='document_test_download'),
    path('documents/<int:pk>/simple-download/', views.simple_document_download, name='simple_document_download'),
    path('documents/<int:pk>/simple-view/', views.simple_document_view, name='simple_document_view'),
    path('documents/test-page/', views.document_test_page, name='document_test_page'),
    
    # URLs pour les formulaires spécialisés
    path('formulaires/diagnostics/', views.diagnostic_form_view, name='diagnostic_form'),
    path('formulaires/assurances/', views.assurance_form_view, name='assurance_form'),
    path('formulaires/etat-lieux/', views.etat_lieux_form_view, name='etat_lieux_form'),
    
    # URLs pour la gestion des pièces
    path('<int:propriete_id>/pieces/', views.gestion_pieces, name='gestion_pieces'),
    path('<int:propriete_id>/pieces/creer/', views.creer_piece, name='creer_piece'),
    path('<int:propriete_id>/pieces/creer-auto/', views.creer_pieces_auto, name='creer_pieces_auto'),
    path('<int:propriete_id>/pieces/planifier-renovation/', views.planifier_renovation, name='planifier_renovation'),
    path('<int:propriete_id>/pieces/export/', views.export_pieces, name='export_pieces'),
    
    # URLs pour les pièces individuelles
    path('piece/<int:piece_id>/', views.detail_piece, name='piece_detail'),
    path('piece/<int:piece_id>/modifier/', views.modifier_piece, name='piece_modifier'),
    path('piece/<int:piece_id>/liberer/', views.liberer_piece, name='piece_liberer'),
    
    # URLs API pour les pièces
    path('api/<int:propriete_id>/pieces-disponibles/', views.api_pieces_disponibles, name='api_pieces_disponibles'),
    path('api/verifier-disponibilite/', views.api_verifier_disponibilite, name='api_verifier_disponibilite'),
    
    # URLs pour les unités locatives
    path('unites/', views_unites.UniteLocativeListView.as_view(), name='unites_liste'),
    path('unites/recherche/', views_unites.recherche_unites, name='recherche_unites'),
    path('unites/ajouter/', views_unites.unite_create, name='unite_create'),
    path('unites/ajouter/<int:propriete_id>/', views_unites.unite_create, name='unite_create_propriete'),
    path('unites/<int:pk>/', views_unites.unite_detail, name='unite_detail'),
    path('unites/<int:pk>/detail-complet/', views_unites.unite_detail_complet, name='unite_detail_complet'),
    path('unites/<int:pk>/modifier/', views_unites.unite_edit, name='unite_edit'),
    
    # Tableau de bord pour grandes propriétés
    path('<int:propriete_id>/dashboard/', views_unites.tableau_bord_propriete, name='dashboard_propriete'),
    
    # Réservations
    path('unites/<int:unite_id>/reserver/', views_unites.reservation_create, name='reservation_create'),
    path('reservations/<int:reservation_id>/convertir-en-contrat/', views_unites.convertir_reservation_en_contrat, name='convertir_reservation_en_contrat'),
    
    # APIs pour les unités
    path('api/unites-disponibles/', views_unites.api_unites_disponibles, name='api_unites_disponibles'),
    path('api/recherche-unites-live/', views_unites.api_recherche_unites_live, name='api_recherche_unites_live'),
    path('api/statistiques-recherche/', views_unites.api_statistiques_recherche, name='api_statistiques_recherche'),
    path('api/statistiques-propriete/<int:propriete_id>/', views_unites.api_statistiques_propriete, name='api_statistiques_propriete'),
    
    # URLs pour les types de biens
    path('types-bien/', views.TypeBienListView.as_view(), name='liste_types_bien'),
    path('types-bien/<int:pk>/supprimer/', views.SupprimerTypeBienView.as_view(), name='supprimer_type_bien'),
    
    # URLs API REST
    path('api/', include(router.urls)),
]
