
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Contrat, Quittance, EtatLieux, ResiliationContrat,
    DepenseResiliation, RecuCaution, DocumentContrat
)


class PaiementInline(admin.TabularInline):
    """Affiche l'historique des paiements du contrat."""
    from paiements.models import Paiement
    model = Paiement
    extra = 0
    can_delete = False
    fields = ('date_paiement', 'mois_paye', 'montant', 'type_paiement', 'mode_paiement', 'statut', 'est_saisie_manuelle_historique')
    readonly_fields = ('date_paiement', 'mois_paye', 'montant', 'type_paiement', 'mode_paiement', 'statut', 'est_saisie_manuelle_historique', 'bouton_migration')
    ordering = ('-date_paiement',)
    verbose_name = "Paiement"
    verbose_name_plural = "Historique des paiements"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def bouton_migration(self, obj):
        """Affiche un bouton pour ajouter un paiement historique."""
        if obj and obj.pk:
            return ''  # Si le paiement existe déjà, ne rien afficher
        # Ce champ ne sera visible que dans le formulaire d'ajout (jamais appelé en pratique)
        return ''
    bouton_migration.short_description = ""
    
    def get_queryset(self, request):
        """Retourne les paiements du contrat."""
        qs = super().get_queryset(request)
        return qs
    
    def get_formset(self, request, obj=None, **kwargs):
        """Personnalise l'affichage si aucun paiement n'existe."""
        formset = super().get_formset(request, obj, **kwargs)
        
        # Si le contrat n'a aucun paiement, ajouter un message d'aide
        if obj and not obj.paiements.exists():
            from django.utils.safestring import mark_safe
            url = reverse('admin:paiements_paiement_add') + f'?contrat={obj.pk}&historique=1'
            message = mark_safe(
                f'<div style="padding:15px;background:#fff3cd;border:1px solid #ffc107;border-radius:4px;margin:10px 0;">'
                f'<strong>📋 Aucun paiement enregistré pour ce contrat</strong><br><br>'
                f'<a href="{url}" style="background:#ff9800;color:white;padding:8px 16px;border-radius:4px;'
                f'font-weight:bold;text-decoration:none;display:inline-block;">➕ Ajouter un paiement historique (migration)</a>'
                f'<p style="margin-top:10px;color:#666;font-size:13px;">Utilisez ce bouton pour importer des paiements de l\'ancienne plateforme.</p>'
                f'</div>'
            )
            formset.help_text = message
        
        return formset


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    autocomplete_fields = ['propriete', 'locataire']
    """Interface d'administration pour les contrats."""
    
    inlines = [PaiementInline]
    
    list_display = (
        'numero_contrat', 'propriete', 'locataire', 'date_debut', 
        'date_fin', 'loyer_mensuel', 'statut', 'est_actif', 'bouton_paiement_historique'
    )

    def bouton_paiement_historique(self, obj):
        # Affiche le bouton uniquement si le contrat n'a aucun paiement ou est marqué pour migration
        from paiements.models import Paiement
        nb_paiements = Paiement.objects.filter(contrat=obj).count()
        if nb_paiements == 0 or getattr(obj, 'migration_necessaire', False):
            url = reverse('admin:paiements_paiement_add') + f'?contrat={obj.pk}&historique=1'
            return mark_safe(f'<a href="{url}" style="background:#ff9800;color:white;padding:6px 12px;border-radius:4px;font-weight:bold;text-decoration:none;">Ajouter paiement historique (migration)</a>')
        return ''
    bouton_paiement_historique.short_description = "Migration : Paiement historique"

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
            'fields': ('numero_contrat', 'propriete', 'locataire'),
            'description': _('Le numéro de contrat peut être modifié. Si laissé vide lors de la création, un numéro sera généré automatiquement.')
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

    readonly_fields = ('date_creation', 'date_modification')

    def render_change_form(self, request, context, *args, **kwargs):
        # Ajoute le bouton sur la fiche contrat (détail)
        obj = context.get('original')
        if obj:
            from paiements.models import Paiement
            nb_paiements = Paiement.objects.filter(contrat=obj).count()
            if nb_paiements == 0 or getattr(obj, 'migration_necessaire', False):
                url = reverse('admin:paiements_paiement_add') + f'?contrat={obj.pk}&historique=1'
                bouton = mark_safe(f'<a href="{url}" style="background:#ff9800;color:white;padding:8px 16px;border-radius:4px;font-weight:bold;text-decoration:none;display:inline-block;margin-bottom:12px;">Ajouter paiement historique (migration)</a>')
                context['adminform'].form.fields['numero_contrat'].help_text = (context['adminform'].form.fields['numero_contrat'].help_text or '') + '<br>' + bouton
        return super().render_change_form(request, context, *args, **kwargs)
    
    actions = ['activer_contrats', 'desactiver_contrats', 'resilier_contrats', 'retablir_contrats_resilies']
    
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
        updated = 0
        for contrat in queryset:
            contrat.est_resilie = True
            contrat.est_actif = False
            contrat.date_resiliation = timezone.now().date()
            contrat.save()
            # Forcer la mise à jour de la disponibilité de la propriété et de l'unité locative
            contrat._update_disponibilite_propriete()
            contrat._update_disponibilite_unite_locative()
            updated += 1
        self.message_user(request, f'{updated} contrat(s) résilié(s) avec succès.')
    resilier_contrats.short_description = _("Résilier les contrats sélectionnés")
    
    def retablir_contrats_resilies(self, request, queryset):
        """Action pour rétablir des contrats résiliés par inadvertance."""
        # Filtrer uniquement les contrats qui sont effectivement résiliés
        contrats_resilies = queryset.filter(est_resilie=True)
        
        if not contrats_resilies.exists():
            self.message_user(
                request, 
                "Aucun contrat résilié trouvé dans la sélection.", 
                level='warning'
            )
            return
        
        updated = 0
        for contrat in contrats_resilies:
            # Restaurer le contrat
            contrat.est_resilie = False
            contrat.date_resiliation = None
            contrat.motif_resiliation = ''
            contrat.est_actif = True  # Réactiver automatiquement
            contrat.save()
            
            # Mettre à jour la disponibilité de la propriété et de l'unité locative
            contrat._update_disponibilite_propriete()
            contrat._update_disponibilite_unite_locative()
            updated += 1
        
        self.message_user(
            request, 
            f'{updated} contrat(s) rétabli(s) avec succès. '
            f'Les propriétés/unités associées ont été marquées comme occupées.',
            level='success'
        )
    retablir_contrats_resilies.short_description = _("Rétablir les contrats résiliés (annuler la résiliation)")


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


@admin.register(RecuCaution)
class RecuCautionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les reçus de caution."""
    
    list_display = (
        'numero_recu', 'contrat', 'type_recu', 'imprime', 
        'date_emission', 'format_impression', 'imprime_par'
    )
    list_filter = (
        'type_recu', 'imprime', 'format_impression', 'date_emission'
    )
    search_fields = (
        'numero_recu', 'contrat__numero_contrat',
        'contrat__locataire__nom', 'contrat__locataire__prenom'
    )
    ordering = ('-date_emission',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('contrat', 'numero_recu', 'type_recu', 'date_emission')
        }),
        (_('Impression'), {
            'fields': ('imprime', 'date_impression', 'imprime_par', 'format_impression')
        }),
        (_('Métadonnées'), {
            'fields': ('notes_internes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('numero_recu', 'date_emission')
    
    actions = ['marquer_imprimes']
    
    def marquer_imprimes(self, request, queryset):
        """Action pour marquer les reçus comme imprimés."""
        from django.utils import timezone
        updated = 0
        for recu in queryset.filter(imprime=False):
            recu.marquer_imprime(request.user)
            updated += 1
        self.message_user(request, f'{updated} reçu(s) marqué(s) comme imprimé(s).')
    marquer_imprimes.short_description = _("Marquer comme imprimés")
    
    def get_queryset(self, request):
        """Optimiser les requêtes."""
        return super().get_queryset(request).select_related(
            'contrat', 'contrat__locataire', 'contrat__propriete', 'imprime_par'
        )


@admin.register(DocumentContrat)
class DocumentContratAdmin(admin.ModelAdmin):
    """Interface d'administration pour les documents de contrat."""
    
    list_display = (
        'numero_document', 'contrat', 'type_document', 'imprime',
        'date_creation', 'date_impression', 'imprime_par'
    )
    list_filter = (
        'type_document', 'imprime', 'date_creation', 'format_impression'
    )
    search_fields = (
        'numero_document', 'contrat__numero_contrat',
        'contrat__locataire__nom', 'contrat__locataire__prenom'
    )
    ordering = ('-date_creation',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('contrat', 'numero_document', 'type_document')
        }),
        (_('Impression'), {
            'fields': ('imprime', 'date_impression', 'imprime_par', 'format_impression')
        }),
        (_('Métadonnées'), {
            'fields': ('version_template', 'notes_internes', 'date_creation'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('numero_document', 'date_creation')
    
    actions = ['marquer_imprimes']
    
    def marquer_imprimes(self, request, queryset):
        """Action pour marquer les documents comme imprimés."""
        from django.utils import timezone
        updated = 0
        for doc in queryset.filter(imprime=False):
            doc.marquer_imprime(request.user)
            updated += 1
        self.message_user(request, f'{updated} document(s) marqué(s) comme imprimé(s).')
    marquer_imprimes.short_description = _("Marquer comme imprimés")
    
    def get_queryset(self, request):
        """Optimiser les requêtes."""
        return super().get_queryset(request).select_related(
            'contrat', 'contrat__locataire', 'contrat__propriete', 'imprime_par'
        )
