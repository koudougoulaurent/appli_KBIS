from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Bailleur, Locataire, TypeBien, Propriete, Document


@admin.register(TypeBien)
class TypeBienAdmin(admin.ModelAdmin):
    """Interface d'administration pour les types de biens."""
    
    list_display = ('nom', 'description', 'proprietes_count')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    
    def proprietes_count(self, obj):
        """Affiche le nombre de propriétés pour ce type."""
        return obj.propriete_set.count()
    proprietes_count.short_description = _("Nombre de propriétés")


@admin.register(Bailleur)
class BailleurAdmin(admin.ModelAdmin):
    """Interface d'administration pour les bailleurs."""
    
    list_display = ('nom', 'prenom', 'email', 'telephone', 'proprietes_count', 'actif')
    list_filter = ('actif', 'date_creation')
    search_fields = ('nom', 'prenom', 'email', 'telephone')
    ordering = ('nom', 'prenom')
    
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'adresse')
        }),
        (_('Informations professionnelles'), {
            'fields': ('civilite', 'date_naissance'),
            'classes': ('collapse',)
        }),
        (_('Informations bancaires'), {
            'fields': ('iban', 'bic', 'banque'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('actif', 'cree_par'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    
    def proprietes_count(self, obj):
        """Affiche le nombre de propriétés du bailleur."""
        return obj.get_proprietes_count()
    proprietes_count.short_description = _("Propriétés")


@admin.register(Locataire)
class LocataireAdmin(admin.ModelAdmin):
    """Interface d'administration pour les locataires."""
    
    list_display = ('nom', 'prenom', 'email', 'telephone', 'profession', 'contrats_actifs_count', 'statut')
    list_filter = ('statut', 'date_creation', 'profession')
    search_fields = ('nom', 'prenom', 'email', 'telephone', 'employeur')
    ordering = ('nom', 'prenom')
    
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'adresse', 'code_postal', 'ville', 'pays')
        }),
        (_('Informations professionnelles'), {
            'fields': ('profession', 'employeur', 'revenus_mensuels'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('statut', 'cree_par'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    
    def contrats_actifs_count(self, obj):
        """Affiche le nombre de contrats actifs du locataire."""
        return obj.get_contrats_actifs_count()
    contrats_actifs_count.short_description = _("Contrats actifs")


@admin.register(Propriete)
class ProprieteAdmin(admin.ModelAdmin):
    """Interface d'administration pour les propriétés."""
    
    list_display = (
        'titre', 'ville', 'type_bien', 'surface', 'nombre_pieces', 
        'loyer_actuel', 'disponible', 'etat', 'bailleur'
    )
    list_filter = (
        'type_bien', 'disponible', 'etat', 'ville', 'ascenseur', 
        'parking', 'balcon', 'jardin'
    )
    search_fields = ('titre', 'adresse', 'ville', 'bailleur__nom', 'bailleur__prenom')
    ordering = ('ville', 'adresse')
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('titre', 'adresse', 'code_postal', 'ville', 'pays')
        }),
        (_('Caractéristiques'), {
            'fields': (
                'type_bien', 'surface', 'nombre_pieces', 'nombre_chambres', 
                'nombre_salles_bain'
            )
        }),
        (_('Équipements'), {
            'fields': ('ascenseur', 'parking', 'balcon', 'jardin'),
            'classes': ('collapse',)
        }),
        (_('Informations financières'), {
            'fields': ('prix_achat', 'loyer_actuel', 'charges'),
            'classes': ('collapse',)
        }),
        (_('État et disponibilité'), {
            'fields': ('etat', 'disponible')
        }),
        (_('Relations'), {
            'fields': ('bailleur', 'cree_par'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    
    actions = ['marquer_disponible', 'marquer_indisponible', 'activer_proprietes', 'desactiver_proprietes']
    
    def marquer_disponible(self, request, queryset):
        """Action pour marquer les propriétés comme disponibles."""
        updated = queryset.update(disponible=True)
        self.message_user(request, f'{updated} propriété(s) marquée(s) comme disponible(s).')
    marquer_disponible.short_description = _("Marquer comme disponible")
    
    def marquer_indisponible(self, request, queryset):
        """Action pour marquer les propriétés comme indisponibles."""
        updated = queryset.update(disponible=False)
        self.message_user(request, f'{updated} propriété(s) marquée(s) comme indisponible(s).')
    marquer_indisponible.short_description = _("Marquer comme indisponible")
    
    def activer_proprietes(self, request, queryset):
        """Action pour activer les propriétés."""
        updated = queryset.update(est_actif=True)
        self.message_user(request, f'{updated} propriété(s) activée(s).')
    activer_proprietes.short_description = _("Activer les propriétés")
    
    def desactiver_proprietes(self, request, queryset):
        """Action pour désactiver les propriétés."""
        updated = queryset.update(est_actif=False)
        self.message_user(request, f'{updated} propriété(s) désactivée(s).')
    desactiver_proprietes.short_description = _("Désactiver les propriétés")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Administration des documents."""
    list_display = [
        'nom', 'type_document', 'statut', 'propriete', 'bailleur', 
        'locataire', 'date_creation', 'date_expiration', 'confidentiel'
    ]
    list_filter = [
        'type_document', 'statut', 'confidentiel', 'date_creation',
        'propriete', 'bailleur', 'locataire'
    ]
    search_fields = ['nom', 'description', 'tags']
    readonly_fields = ['date_creation', 'date_modification', 'taille_fichier']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'type_document', 'description', 'fichier')
        }),
        ('Relations', {
            'fields': ('propriete', 'bailleur', 'locataire'),
            'classes': ('collapse',)
        }),
        ('Statut et dates', {
            'fields': ('statut', 'date_expiration')
        }),
        ('Métadonnées', {
            'fields': ('tags', 'confidentiel', 'cree_par'),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('date_creation', 'date_modification', 'taille_fichier'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
