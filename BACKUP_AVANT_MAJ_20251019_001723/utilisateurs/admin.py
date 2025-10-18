from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, GroupeTravail

@admin.register(GroupeTravail)
class GroupeTravailAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description', 'actif', 'date_creation']
    list_filter = ['actif', 'date_creation']
    search_fields = ['nom', 'description']
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'actif')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'description': 'Permissions au format JSON'
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'groupe_travail', 'actif', 'date_creation']
    list_filter = ['groupe_travail', 'actif', 'is_staff', 'is_superuser', 'date_creation']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    readonly_fields = ['date_creation', 'date_modification', 'derniere_connexion']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'telephone', 'adresse', 'date_naissance', 'photo')
        }),
        ('Informations professionnelles', {
            'fields': ('groupe_travail', 'poste', 'departement', 'date_embauche')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Statut', {
            'fields': ('actif', 'derniere_connexion')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'groupe_travail', 'actif'),
        }),
    )
    
    ordering = ['username']
