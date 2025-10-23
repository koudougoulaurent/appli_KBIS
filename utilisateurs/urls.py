from django.urls import path
from . import views
from .views import utilisateur_list

app_name = 'utilisateurs'

urlpatterns = [
    # Dashboard principal des utilisateurs
    path('', views.utilisateurs_dashboard, name='dashboard'),
    
    # Pages de connexion des groupes
    path('connexion-groupes/', views.connexion_groupes, name='connexion_groupes'),
    path('login/<str:groupe_nom>/', views.login_groupe, name='login_groupe'),
    path('logout/', views.logout_groupe, name='logout_groupe'),
    
    # Dashboards par groupe
    path('dashboard/<str:groupe_nom>/', views.dashboard_groupe, name='dashboard_groupe'),
    
    # Gestion des utilisateurs
    path('liste/', utilisateur_list, name='liste_utilisateurs'),
    path('utilisateurs/ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    path('utilisateurs/<int:pk>/', views.detail_utilisateur, name='detail_utilisateur'),
    path('utilisateurs/<int:pk>/modifier/', views.modifier_utilisateur, name='modifier_utilisateur'),
    
    # Gestion des groupes de travail
    path('groupes/', views.liste_groupes, name='liste_groupes'),
    path('groupes/ajouter/', views.ajouter_groupe, name='ajouter_groupe'),
    path('groupes/<int:pk>/', views.detail_groupe, name='detail_groupe'),
    path('groupes/<int:pk>/modifier/', views.modifier_groupe, name='modifier_groupe'),
    
    # Profil utilisateur
    path('profile/', views.profile, name='profile'),
    
    # === URLs SPÉCIALES POUR LE GROUPE PRIVILEGE ===
    
    # Dashboard avancé PRIVILEGE
    path('privilege/dashboard/', views.privilege_dashboard_advanced, name='privilege_dashboard_advanced'),
    
    # Gestion des éléments
    path('privilege/elements/', views.privilege_element_management, name='privilege_element_management'),
    path('privilege/elements/<str:model_name>/', views.privilege_element_list, name='privilege_element_list'),
    
    
    # Actions en lot
    path('privilege/bulk-actions/', views.privilege_bulk_actions, name='privilege_bulk_actions'),
    
    # Gestion des profils
    path('privilege/profiles/', views.privilege_profile_management, name='privilege_profile_management'),
    
    # Journal d'audit
    path('privilege/audit/', views.privilege_dashboard_advanced, name='privilege_audit_log'),
] 