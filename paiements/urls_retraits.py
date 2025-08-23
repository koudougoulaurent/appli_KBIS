from django.urls import path
from . import views_retraits

urlpatterns = [
    # Liste des retraits
    path('', views_retraits.retrait_list, name='retrait_list'),
    
    # Création de retraits
    path('create/', views_retraits.retrait_create, name='retrait_create'),
    path('auto-create/', views_retraits.retrait_auto_create, name='retrait_auto_create'),
    
    # Détails et modification des retraits
    path('<int:pk>/', views_retraits.retrait_detail, name='retrait_detail'),
    path('<int:pk>/edit/', views_retraits.retrait_edit, name='retrait_edit'),
    
    # Actions sur les retraits
    path('<int:pk>/validate/', views_retraits.retrait_validate, name='retrait_validate'),
    path('<int:pk>/mark-paid/', views_retraits.retrait_mark_paid, name='retrait_mark_paid'),
    path('<int:pk>/cancel/', views_retraits.retrait_cancel, name='retrait_cancel'),
    
    # Gestion des reçus
    path('recu/<int:recu_id>/', views_retraits.recu_retrait_view, name='recu_view'),
    path('recu/<int:recu_id>/print/', views_retraits.recu_retrait_print, name='recu_print'),
    
    # Rapports et statistiques
    path('report/', views_retraits.retrait_report, name='retrait_report'),
    
    # API pour récupérer les données des bailleurs
    path('api/bailleur/<int:bailleur_id>/data/', views_retraits.get_bailleur_retrait_data, name='bailleur_data'),
]
