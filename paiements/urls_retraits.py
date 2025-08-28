from django.urls import path
from . import views_retraits
from . import views_intelligentes_retraits

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

    # 🚀 SYSTÈME INTELLIGENT DES RETRAITS - NOUVEAU !
    # Page d'accueil
    path('intelligent/', views_intelligentes_retraits.accueil_systeme_intelligent, name='accueil_systeme_intelligent'),
    
    # Dashboard intelligent
    path('intelligent/dashboard/', views_intelligentes_retraits.dashboard_intelligent_retraits, name='dashboard_intelligent'),
    
    # Création intelligente
    path('intelligent/creer/', views_intelligentes_retraits.retrait_intelligent_create, name='retrait_intelligent_create'),
    path('intelligent/creer/class/', views_intelligentes_retraits.RetraitIntelligentCreateView.as_view(), name='retrait_intelligent_create_class'),
    
    # Modification intelligente
    path('intelligent/<int:pk>/modifier/', views_intelligentes_retraits.retrait_intelligent_update, name='retrait_intelligent_update'),
    path('intelligent/<int:pk>/modifier/class/', views_intelligentes_retraits.RetraitIntelligentUpdateView.as_view(), name='retrait_intelligent_update_class'),
    
    # Recherche intelligente
    path('intelligent/recherche/', views_intelligentes_retraits.recherche_bailleurs_intelligente, name='recherche_bailleurs_intelligente'),
    
    # Contexte et suggestions
    path('intelligent/contexte/<int:bailleur_id>/', views_intelligentes_retraits.contexte_bailleur_rapide, name='contexte_bailleur_rapide'),
    path('intelligent/suggestions/<int:bailleur_id>/', views_intelligentes_retraits.suggestions_retrait_automatiques, name='suggestions_retrait_automatiques'),
    
    # API intelligente
    path('intelligent/api/contexte/<int:bailleur_id>/', views_intelligentes_retraits.api_contexte_bailleur, name='api_contexte_bailleur'),
    path('intelligent/api/suggestions/<int:bailleur_id>/', views_intelligentes_retraits.api_suggestions_retrait, name='api_suggestions_retrait'),
]
