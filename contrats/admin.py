from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .models import Contrat, Quittance, EtatLieux, ResiliationContrat, DepenseResiliation


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    """Interface d'administration pour les contrats."""
    
    list_display = (
        'numero_contrat', 'propriete', 'locataire', 'date_debut', 
        'date_fin', 'loyer_mensuel', 'statut', 'est_actif'
    )
    list_filter = (
        'est_actif', 'est_resilie', 'mode_paiement', 'date_debut', 
        'date_fin', 'propriete__ville'
    )
    search_fields = (
        'numero_contrat', 'propriete__titre', 'locataire__nom', 
        'locataire__prenom', 'propriete__adresse'
    )
    ordering = ('-date_debut',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('numero_contrat', 'propriete', 'locataire')
        }),
        (_('Dates'), {
            'fields': ('date_debut', 'date_fin', 'date_signature')
        }),
        (_('Informations financières'), {
            'fields': ('loyer_mensuel', 'charges_mensuelles', 'depot_garantie')
        }),
        (_('Conditions de paiement'), {
            'fields': ('jour_paiement', 'mode_paiement'),
            'classes': ('collapse',)
        }),
        (_('État du contrat'), {
            'fields': ('est_actif', 'est_resilie', 'date_resiliation', 'motif_resiliation')
        }),
        (_('Métadonnées'), {
            'fields': ('notes', 'cree_par'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('numero_contrat', 'date_creation', 'date_modification')
    
    actions = ['activer_contrats', 'desactiver_contrats', 'resilier_contrats']
    
    def statut(self, obj):
        """Affiche le statut du contrat avec une couleur."""
        statut = obj.get_statut()
        if statut == "Actif":
            color = "green"
        elif statut == "Expiré":
            color = "orange"
        elif statut == "Résilié":
            color = "red"
        else:
            color = "gray"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, statut
        )
    statut.short_description = _("Statut")
    
    def activer_contrats(self, request, queryset):
        """Action pour activer les contrats sélectionnés."""
        updated = queryset.update(est_actif=True)
        self.message_user(request, f'{updated} contrat(s) activé(s) avec succès.')
    activer_contrats.short_description = _("Activer les contrats sélectionnés")
    
    def desactiver_contrats(self, request, queryset):
        """Action pour désactiver les contrats sélectionnés."""
        updated = queryset.update(est_actif=False)
        self.message_user(request, f'{updated} contrat(s) désactivé(s) avec succès.')
    desactiver_contrats.short_description = _("Désactiver les contrats sélectionnés")
    
    def resilier_contrats(self, request, queryset):
        """Action pour résilier les contrats sélectionnés."""
        updated = queryset.update(
            est_resilie=True,
            est_actif=False,
            date_resiliation=timezone.now().date()
        )
        self.message_user(request, f'{updated} contrat(s) résilié(s) avec succès.')
    resilier_contrats.short_description = _("Résilier les contrats sélectionnés")


@admin.register(Quittance)
class QuittanceAdmin(admin.ModelAdmin):
    """Interface d'administration pour les quittances."""
    
    list_display = (
        'numero_quittance', 'contrat', 'mois', 'montant_loyer', 
        'montant_charges', 'montant_total', 'date_emission'
    )
    list_filter = ('mois', 'date_emission', 'contrat__propriete__ville')
    search_fields = (
        'numero_quittance', 'contrat__numero_contrat', 
        'contrat__locataire__nom', 'contrat__locataire__prenom'
    )
    ordering = ('-mois',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('numero_quittance', 'contrat', 'mois')
        }),
        (_('Montants'), {
            'fields': ('montant_loyer', 'montant_charges', 'montant_total')
        }),
        (_('Métadonnées'), {
            'fields': ('date_emission',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('numero_quittance', 'montant_total', 'date_creation', 'date_emission')
    
    actions = ['generer_quittances_mensuelles']
    
    def generer_quittances_mensuelles(self, request, queryset):
        """Action pour générer des quittances mensuelles."""
        # Cette action pourrait être implémentée pour générer automatiquement
        # les quittances pour tous les contrats actifs
        self.message_user(request, "Fonctionnalité de génération automatique à implémenter.")
    generer_quittances_mensuelles.short_description = _("Générer quittances mensuelles")


@admin.register(EtatLieux)
class EtatLieuxAdmin(admin.ModelAdmin):
    """Interface d'administration pour les états des lieux."""
    
    list_display = (
        'contrat', 'type_etat', 'date_etat', 'etat_murs', 
        'etat_sol', 'etat_plomberie', 'etat_electricite'
    )
    list_filter = (
        'type_etat', 'date_etat', 'etat_murs', 'etat_sol', 
        'etat_plomberie', 'etat_electricite', 'contrat__propriete__ville'
    )
    search_fields = (
        'contrat__numero_contrat', 'contrat__locataire__nom', 
        'contrat__locataire__prenom', 'contrat__propriete__titre'
    )
    ordering = ('-date_etat',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('contrat', 'type_etat', 'date_etat')
        }),
        (_('Observations'), {
            'fields': ('observations_generales',)
        }),
        (_('État des éléments'), {
            'fields': ('etat_murs', 'etat_sol', 'etat_plomberie', 'etat_electricite')
        }),
        (_('Métadonnées'), {
            'fields': ('notes', 'cree_par'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation',)
    
    actions = ['dupliquer_etat_lieux']
    
    def dupliquer_etat_lieux(self, request, queryset):
        """Action pour dupliquer un état des lieux."""
        if queryset.count() != 1:
            self.message_user(request, "Veuillez sélectionner exactement un état des lieux à dupliquer.")
            return
        
        etat_original = queryset.first()
        # Créer une copie avec le type opposé
        nouveau_type = 'sortie' if etat_original.type_etat == 'entree' else 'entree'
        
        EtatLieux.objects.create(
            contrat=etat_original.contrat,
            type_etat=nouveau_type,
            date_etat=timezone.now().date(),
            observations_generales=etat_original.observations_generales,
            etat_murs=etat_original.etat_murs,
            etat_sol=etat_original.etat_sol,
            etat_plomberie=etat_original.etat_plomberie,
            etat_electricite=etat_original.etat_electricite,
            notes=etat_original.notes,
            cree_par=request.user
        )
        
        self.message_user(request, f"État des lieux dupliqué avec succès (type: {nouveau_type}).")
    dupliquer_etat_lieux.short_description = _("Dupliquer l'état des lieux")


@admin.register(ResiliationContrat)
class ResiliationContratAdmin(admin.ModelAdmin):
    """Interface d'administration pour les résiliations de contrat."""
    
    list_display = (
        'contrat', 'date_resiliation', 'type_resiliation', 
        'statut', 'total_depenses', 'solde_restant', 'cree_par'
    )
    list_filter = (
        'statut', 'type_resiliation', 'caution_remboursee', 
        'date_resiliation', 'cree_par'
    )
    search_fields = (
        'contrat__numero_contrat', 'contrat__propriete__titre',
        'contrat__locataire__nom', 'contrat__locataire__prenom'
    )
    ordering = ('-date_resiliation',)
    
    fieldsets = (
        (_('Informations de résiliation'), {
            'fields': ('contrat', 'date_resiliation', 'motif_resiliation', 'type_resiliation', 'statut')
        }),
        (_('État des lieux'), {
            'fields': ('etat_lieux_sortie',)
        }),
        (_('Remboursement'), {
            'fields': ('caution_remboursee', 'montant_remboursement', 'date_remboursement')
        }),
        (_('Calculs financiers'), {
            'fields': ('total_depenses', 'caution_versee', 'solde_restant'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('notes', 'cree_par', 'validee_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('total_depenses', 'caution_versee', 'solde_restant', 'date_creation', 'date_modification')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contrat', 'contrat__propriete', 'contrat__locataire', 'cree_par')


@admin.register(DepenseResiliation)
class DepenseResiliationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les dépenses de résiliation."""
    
    list_display = ('resiliation', 'description', 'montant', 'ordre', 'date_creation')
    list_filter = ('date_creation', 'resiliation__type_resiliation')
    search_fields = ('description', 'resiliation__contrat__numero_contrat')
    ordering = ('resiliation', 'ordre', 'date_creation')
    
    fieldsets = (
        (_('Informations de la dépense'), {
            'fields': ('resiliation', 'description', 'montant', 'ordre')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resiliation', 'resiliation__contrat')
