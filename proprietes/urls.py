from django.urls import path
from . import views
from .views import ajouter_charge_bailleur_rapide

app_name = 'proprietes'

urlpatterns = [
    # Dashboard principal des propriétés
    path('', views.proprietes_dashboard, name='dashboard'),
    
    # URLs pour les propriétés (avec aliases pour compatibilité)
    path('liste/', views.liste_proprietes, name='liste'),
    path('ajouter/', views.ajouter_propriete, name='ajouter'),
    path('<int:pk>/', views.detail_propriete, name='detail'),
    path('<int:pk>/modifier/', views.modifier_propriete, name='modifier'),
    
    # URLs pour les charges bailleur
    path('charges-bailleur/', views.liste_charges_bailleur, name='liste_charges_bailleur'),
    path('charges-bailleur/ajouter/', views.ajouter_charge_bailleur, name='ajouter_charge_bailleur'),
    path('ajouter_charge_bailleur_rapide/', views.ajouter_charge_bailleur_rapide, name='ajouter_charge_bailleur_rapide'),
    path('charges-bailleur/<int:pk>/', views.detail_charge_bailleur, name='detail_charge_bailleur'),
    path('charges-bailleur/<int:pk>/modifier/', views.modifier_charge_bailleur, name='modifier_charge_bailleur'),
    path('charges-bailleur/<int:pk>/deduction/', views.deduction_charge_bailleur, name='deduction_charge_bailleur'),
    path('charges-bailleur/<int:pk>/remboursement/', views.marquer_charge_remboursee, name='marquer_charge_remboursee'),
    
    # URLs pour les bailleurs
    path('bailleurs/', views.liste_bailleurs, name='bailleurs_liste'),
    path('bailleurs/ajouter/', views.ajouter_bailleur, name='ajouter_bailleur'),
    path('bailleurs/<int:pk>/', views.detail_bailleur, name='detail_bailleur'),
    path('bailleurs/<int:pk>/', views.detail_bailleur, name='bailleur_detail'),  # Alias pour compatibilité
    path('bailleurs/<int:pk>/modifier/', views.modifier_bailleur, name='modifier_bailleur'),
    path('bailleurs/<int:pk>/supprimer/', views.supprimer_bailleur, name='supprimer_bailleur'),
    path('bailleurs/recherche-avancee/', views.recherche_avancee_bailleurs, name='recherche_avancee_bailleurs'),

    # URLs pour les locataires
    path('locataires/', views.liste_locataires, name='locataires_liste'),
    path('locataires/ajouter/', views.ajouter_locataire, name='ajouter_locataire'),
    path('locataires/<int:pk>/', views.detail_locataire, name='detail_locataire'),
    path('locataires/<int:pk>/modifier/', views.modifier_locataire, name='modifier_locataire'),
    path('locataires/<int:pk>/supprimer/', views.supprimer_locataire, name='supprimer_locataire'),
    path('locataires/recherche-avancee/', views.recherche_avancee_locataires, name='recherche_avancee_locataires'),
    path('locataires/supprimer/<int:pk>/', views.supprimer_locataire, name='supprimer_locataire'),
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
    
    # URLs pour les formulaires spécialisés
    path('formulaires/diagnostics/', views.diagnostic_form_view, name='diagnostic_form'),
    path('formulaires/assurances/', views.assurance_form_view, name='assurance_form'),
    path('formulaires/etat-lieux/', views.etat_lieux_form_view, name='etat_lieux_form'),
]
