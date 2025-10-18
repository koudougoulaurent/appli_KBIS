from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Bailleur, Locataire, TypeBien, Propriete, Document, UniteLocative, 
    ReservationUnite, Piece, PieceContrat, ChargeCommune, RepartitionChargeCommune, 
    AccesEspacePartage
)


@admin.register(TypeBien)
class TypeBienAdmin(admin.ModelAdmin):
    """Interface d'administration pour les types de biens."""
    
    list_display = ('nom', 'description', 'proprietes_count')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    
    def proprietes_count(self, obj):
        """Affiche le nombre de propriétés pour ce type."""
        return obj.proprietes.count()
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


@admin.register(UniteLocative)
class UniteLocativeAdmin(admin.ModelAdmin):
    """Interface d'administration pour les unités locatives."""
    
    list_display = (
        'numero_unite', 'nom', 'propriete', 'type_unite', 'statut', 
        'etage', 'surface', 'loyer_mensuel', 'est_disponible'
    )
    list_filter = ('statut', 'type_unite', 'propriete', 'etage', 'meuble')
    search_fields = ('numero_unite', 'nom', 'propriete__titre', 'description')
    ordering = ('propriete', 'etage', 'numero_unite')
    
    fieldsets = (
        (_('Identification'), {
            'fields': ('propriete', 'numero_unite', 'nom', 'type_unite')
        }),
        (_('Localisation'), {
            'fields': ('etage', 'surface')
        }),
        (_('Caractéristiques'), {
            'fields': ('nombre_pieces', 'nombre_chambres', 'nombre_salles_bain')
        }),
        (_('Équipements'), {
            'fields': ('meuble', 'balcon', 'parking_inclus', 'climatisation', 'internet_inclus')
        }),
        (_('Informations Financières'), {
            'fields': ('loyer_mensuel', 'charges_mensuelles', 'caution_demandee')
        }),
        (_('État et Disponibilité'), {
            'fields': ('statut', 'date_disponibilite')
        }),
        (_('Descriptions'), {
            'fields': ('description', 'notes_privees'),
            'classes': ('collapse',)
        }),
    )
    
    def est_disponible(self, obj):
        """Affiche si l'unité est disponible."""
        return obj.est_disponible()
    est_disponible.boolean = True
    est_disponible.short_description = _("Disponible")


@admin.register(ReservationUnite)
class ReservationUniteAdmin(admin.ModelAdmin):
    """Interface d'administration pour les réservations d'unités."""
    
    list_display = (
        'unite_locative', 'locataire_potentiel', 'statut', 
        'date_debut_souhaitee', 'date_expiration', 'est_active'
    )
    list_filter = ('statut', 'date_reservation', 'date_expiration')
    search_fields = (
        'unite_locative__numero_unite', 
        'locataire_potentiel__nom', 
        'locataire_potentiel__prenom'
    )
    ordering = ('-date_reservation',)
    
    fieldsets = (
        (_('Réservation'), {
            'fields': ('unite_locative', 'locataire_potentiel', 'statut')
        }),
        (_('Dates'), {
            'fields': ('date_debut_souhaitee', 'date_fin_prevue', 'date_expiration')
        }),
        (_('Financier'), {
            'fields': ('montant_reservation',)
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def est_active(self, obj):
        """Affiche si la réservation est active."""
        return obj.est_active()
    est_active.boolean = True
    est_active.short_description = _("Active")
    
    def save_model(self, request, obj, form, change):
        if not change:  # Création
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(Piece)
class PieceAdmin(admin.ModelAdmin):
    """Interface d'administration pour les pièces."""
    
    list_display = (
        'nom', 'propriete', 'type_piece', 'surface', 'statut', 
        'est_espace_partage', 'cout_acces_mensuel', 'contrats_actifs_count'
    )
    list_filter = ('type_piece', 'statut', 'est_espace_partage', 'propriete')
    search_fields = ('nom', 'propriete__titre', 'description')
    ordering = ('propriete', 'type_piece', 'nom')
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('propriete', 'unite_locative', 'nom', 'type_piece', 'numero_piece')
        }),
        (_('Caractéristiques'), {
            'fields': ('surface', 'description')
        }),
        (_('État et disponibilité'), {
            'fields': ('statut',)
        }),
        (_('Espace partagé'), {
            'fields': ('est_espace_partage', 'cout_acces_mensuel'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    
    def contrats_actifs_count(self, obj):
        """Affiche le nombre de contrats actifs pour cette pièce."""
        return obj.contrats.filter(est_actif=True, est_resilie=False).count()
    contrats_actifs_count.short_description = _("Contrats actifs")


@admin.register(ChargeCommune)
class ChargeCommuneAdmin(admin.ModelAdmin):
    """Interface d'administration pour les charges communes."""
    
    list_display = (
        'nom', 'propriete', 'type_charge', 'montant_mensuel', 
        'type_repartition', 'active', 'date_debut', 'date_fin'
    )
    list_filter = ('type_charge', 'type_repartition', 'active', 'propriete')
    search_fields = ('nom', 'propriete__titre', 'description')
    ordering = ('propriete', 'nom')
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('propriete', 'nom', 'type_charge', 'description')
        }),
        (_('Montant et répartition'), {
            'fields': ('montant_mensuel', 'type_repartition')
        }),
        (_('Période d\'application'), {
            'fields': ('date_debut', 'date_fin')
        }),
        (_('Statut'), {
            'fields': ('active',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('propriete')


@admin.register(RepartitionChargeCommune)
class RepartitionChargeCommuneAdmin(admin.ModelAdmin):
    """Interface d'administration pour les répartitions de charges communes."""
    
    list_display = (
        'charge_commune', 'piece_contrat', 'mois', 'annee', 
        'montant_calcule', 'montant_ajuste', 'applique'
    )
    list_filter = ('mois', 'annee', 'applique', 'charge_commune__propriete')
    search_fields = (
        'charge_commune__nom', 'piece_contrat__piece__nom',
        'piece_contrat__contrat__locataire__nom'
    )
    ordering = ('-annee', '-mois', 'charge_commune')
    
    fieldsets = (
        (_('Charge et contrat'), {
            'fields': ('charge_commune', 'piece_contrat')
        }),
        (_('Période'), {
            'fields': ('mois', 'annee')
        }),
        (_('Montants'), {
            'fields': ('montant_calcule', 'montant_ajuste', 'base_calcul')
        }),
        (_('Statut'), {
            'fields': ('applique', 'date_application')
        }),
    )
    
    readonly_fields = ('date_calcul', 'date_application')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'charge_commune', 'piece_contrat', 'piece_contrat__piece',
            'piece_contrat__contrat', 'piece_contrat__contrat__locataire'
        )


@admin.register(AccesEspacePartage)
class AccesEspacePartageAdmin(admin.ModelAdmin):
    """Interface d'administration pour les accès aux espaces partagés."""
    
    list_display = (
        'piece_privee', 'espace_partage', 'acces_inclus', 
        'cout_supplementaire', 'actif', 'date_debut_acces', 'date_fin_acces'
    )
    list_filter = ('acces_inclus', 'actif', 'espace_partage__propriete')
    search_fields = (
        'piece_privee__nom', 'espace_partage__nom',
        'piece_privee__propriete__titre'
    )
    ordering = ('piece_privee', 'espace_partage')
    
    fieldsets = (
        (_('Pièces'), {
            'fields': ('piece_privee', 'espace_partage')
        }),
        (_('Conditions d\'accès'), {
            'fields': ('acces_inclus', 'cout_supplementaire')
        }),
        (_('Restrictions d\'usage'), {
            'fields': ('heures_acces_debut', 'heures_acces_fin', 'jours_acces'),
            'classes': ('collapse',)
        }),
        (_('Période d\'activation'), {
            'fields': ('date_debut_acces', 'date_fin_acces')
        }),
        (_('Statut'), {
            'fields': ('actif',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'piece_privee', 'espace_partage', 'piece_privee__propriete'
        )


class AccesEspacePartageInline(admin.TabularInline):
    """Inline pour les accès aux espaces partagés."""
    model = AccesEspacePartage
    fk_name = 'piece_privee'
    extra = 0
    fields = ('espace_partage', 'acces_inclus', 'cout_supplementaire', 'actif')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('espace_partage')


class PieceContratInline(admin.TabularInline):
    """Inline pour les contrats de pièces."""
    model = PieceContrat
    extra = 0
    fields = ('contrat', 'loyer_piece', 'charges_piece', 'date_debut_occupation', 'actif')
    readonly_fields = ('date_creation',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contrat', 'contrat__locataire')
