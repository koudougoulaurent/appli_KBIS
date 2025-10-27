from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from core.admin_actions import suppression_definitive_conditionnelle
from .models import (
    Paiement, ChargeDeductible, ChargeBailleur,
    RetraitBailleur, RetraitQuittance, QuittancePaiement
)


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    """Interface d'administration pour les paiements."""
    
    list_display = (
        'id', 'contrat', 'montant', 'montant_charges_deduites', 'montant_net_paye', 
        'type_paiement', 'mode_paiement', 'date_paiement', 'statut_colore', 'valide_par'
    )
    list_filter = (
        'statut', 'type_paiement', 'mode_paiement', 'date_paiement', 
        'contrat__propriete__ville'
    )
    search_fields = (
        'contrat__numero_contrat', 'contrat__locataire__nom', 
        'contrat__locataire__prenom', 'numero_cheque', 'reference_virement'
    )
    ordering = ('-date_paiement',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('contrat', 'montant', 'type_paiement')
        }),
        (_('Charges déductibles'), {
            'fields': ('montant_charges_deduites', 'montant_net_paye'),
            'classes': ('collapse',)
        }),
        (_('Mode et statut'), {
            'fields': ('mode_paiement', 'statut')
        }),
        (_('Dates'), {
            'fields': ('date_paiement', 'date_encaissement')
        }),
        (_('Informations bancaires'), {
            'fields': ('numero_cheque', 'reference_virement'),
            'classes': ('collapse',)
        }),
        (_('Validation'), {
            'fields': ('valide_par',),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('notes', 'cree_par'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['valider_paiements', 'refuser_paiements', 'annuler_paiements', suppression_definitive_conditionnelle]
    
    def statut_colore(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'en_attente': 'orange',
            'valide': 'green',
            'refuse': 'red',
            'annule': 'gray',
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_colore.short_description = _("Statut")
    
    def valider_paiements(self, request, queryset):
        """Action pour valider les paiements sélectionnés."""
        updated = 0
        for paiement in queryset.filter(statut='en_attente'):
            paiement.valider_paiement(request.user)
            updated += 1
        self.message_user(request, f'{updated} paiement(s) validé(s) avec succès.')
    valider_paiements.short_description = _("Valider les paiements sélectionnés")
    
    def refuser_paiements(self, request, queryset):
        """Action pour refuser les paiements sélectionnés."""
        updated = 0
        for paiement in queryset.filter(statut='en_attente'):
            paiement.refuser_paiement(request.user)
            updated += 1
        self.message_user(request, f'{updated} paiement(s) refusé(s) avec succès.')
    refuser_paiements.short_description = _("Refuser les paiements sélectionnés")
    
    def annuler_paiements(self, request, queryset):
        """Action pour annuler les paiements sélectionnés."""
        updated = 0
        for paiement in queryset.exclude(statut='annule'):
            paiement.annuler_paiement(request.user)
            updated += 1
        self.message_user(request, f'{updated} paiement(s) annulé(s) avec succès.')
    annuler_paiements.short_description = _("Annuler les paiements sélectionnés")


@admin.register(ChargeDeductible)
class ChargeDeductibleAdmin(admin.ModelAdmin):
    """Interface d'administration pour les charges déductibles."""
    
    list_display = (
        'id', 'contrat', 'description', 'montant', 
        'date_charge', 'est_deductible_loyer'
    )
    list_filter = (
        'date_charge', 'contrat__est_actif', 'est_deductible_loyer'
    )
    search_fields = (
        'description', 'contrat__numero_contrat', 'contrat__propriete__titre',
        'contrat__locataire__nom', 'contrat__locataire__prenom'
    )
    ordering = ('-date_charge',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('contrat', 'description')
        }),
        (_('Montant'), {
            'fields': ('montant',)
        }),
        (_('Dates'), {
            'fields': ('date_charge',)
        }),
        (_('Statut'), {
            'fields': ('est_valide', 'est_deductible_loyer'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = [suppression_definitive_conditionnelle]


@admin.register(QuittancePaiement)
class QuittancePaiementAdmin(admin.ModelAdmin):
    """Interface d'administration pour les quittances de paiement."""
    
    list_display = (
        'numero_quittance', 'paiement', 'get_locataire', 'get_propriete', 
        'statut_colore', 'date_emission', 'date_impression', 'cree_par'
    )
    list_filter = (
        'statut', 'date_emission', 'date_impression', 
        'paiement__contrat__propriete__ville'
    )
    search_fields = (
        'numero_quittance', 'paiement__reference_paiement',
        'paiement__contrat__locataire__nom', 'paiement__contrat__locataire__prenom',
        'paiement__contrat__propriete__titre'
    )
    ordering = ('-date_emission',)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('numero_quittance', 'paiement')
        }),
        (_('Statut et dates'), {
            'fields': ('statut', 'date_emission', 'date_impression')
        }),
        (_('Métadonnées'), {
            'fields': ('cree_par', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('numero_quittance',)
    
    actions = ['marquer_imprimees', 'marquer_envoyees', 'marquer_archivees']
    
    def get_locataire(self, obj):
        """Affiche le nom du locataire."""
        return obj.get_locataire().get_nom_complet()
    get_locataire.short_description = _("Locataire")
    
    def get_propriete(self, obj):
        """Affiche l'adresse de la propriété."""
        return f"{obj.get_propriete().adresse}, {obj.get_propriete().ville}"
    get_propriete.short_description = _("Propriété")
    
    def statut_colore(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'generee': 'blue',
            'imprimee': 'green',
            'envoyee': 'purple',
            'archivee': 'gray',
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_colore.short_description = _("Statut")
    
    def marquer_imprimees(self, request, queryset):
        """Action pour marquer les quittances comme imprimées."""
        updated = 0
        for quittance in queryset.exclude(statut='imprimee'):
            quittance.marquer_imprimee()
            updated += 1
        self.message_user(request, f'{updated} quittance(s) marquée(s) comme imprimée(s).')
    marquer_imprimees.short_description = _("Marquer comme imprimées")
    
    def marquer_envoyees(self, request, queryset):
        """Action pour marquer les quittances comme envoyées."""
        updated = 0
        for quittance in queryset.exclude(statut='envoyee'):
            quittance.marquer_envoyee()
            updated += 1
        self.message_user(request, f'{updated} quittance(s) marquée(s) comme envoyée(s).')
    marquer_envoyees.short_description = _("Marquer comme envoyées")
    
    def marquer_archivees(self, request, queryset):
        """Action pour marquer les quittances comme archivées."""
        updated = 0
        for quittance in queryset.exclude(statut='archivée'):
            quittance.marquer_archivee()
            updated += 1
        self.message_user(request, f'{updated} quittance(s) marquée(s) comme archivée(s).')
    marquer_archivees.short_description = _("Marquer comme archivées")


@admin.register(RetraitBailleur)
class RetraitBailleurAdmin(admin.ModelAdmin):
    """Admin pour les retraits aux bailleurs."""
    
    list_display = [
        'bailleur', 'mois_retrait', 'montant_loyers_bruts', 
        'montant_charges_deductibles', 'montant_net_a_payer',
        'type_retrait', 'statut', 'mode_retrait', 'date_demande'
    ]
    
    list_filter = [
        'statut', 'type_retrait', 'mode_retrait', 'mois_retrait',
        'date_demande'
    ]
    
    search_fields = [
        'bailleur__nom', 'bailleur__prenom', 'bailleur__code_bailleur',
        'notes'
    ]
    
    readonly_fields = [
        'montant_net_a_payer', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('bailleur', 'mois_retrait', 'type_retrait', 'mode_retrait')
        }),
        ('Montants', {
            'fields': ('montant_loyers_bruts', 'montant_charges_deductibles', 'montant_net_a_payer')
        }),
        ('Dates', {
            'fields': ('date_demande', 'date_validation', 'date_paiement')
        }),
        ('Statut et validation', {
            'fields': ('statut', 'cree_par', 'valide_par')
        }),
        ('Métadonnées', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # filter_horizontal = ['paiements_concernes']  # Champ n'existe pas
    
    actions = ['valider_retraits', 'marquer_payes', 'annuler_retraits', suppression_definitive_conditionnelle]
    
    def valider_retraits(self, request, queryset):
        """Valider les retraits sélectionnés."""
        count = 0
        for retrait in queryset.filter(statut='en_attente'):
            retrait.valider_retrait(request.user)
            count += 1
        
        self.message_user(
            request, 
            f'{count} retrait(s) validé(s) avec succès.'
        )
    valider_retraits.short_description = "Valider les retraits sélectionnés"
    
    def marquer_payes(self, request, queryset):
        """Marquer les retraits sélectionnés comme payés."""
        count = 0
        for retrait in queryset.filter(statut='valide'):
            retrait.marquer_paye(request.user)
            count += 1
        
        self.message_user(
            request, 
            f'{count} retrait(s) marqué(s) comme payé(s).'
        )
    marquer_payes.short_description = "Marquer comme payés"
    
    def annuler_retraits(self, request, queryset):
        """Annuler les retraits sélectionnés."""
        count = 0
        for retrait in queryset.filter(statut__in=['en_attente', 'valide']):
            retrait.annuler_retrait(request.user, "Annulation en masse")
            count += 1
        
        self.message_user(
            request, 
            f'{count} retrait(s) annulé(s).'
        )
    annuler_retraits.short_description = "Annuler les retraits sélectionnés"
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'bailleur', 'cree_par', 'valide_par'
        )


# @admin.register(RetraitChargeDeductible)  # Modèle supprimé
class RetraitChargeDeductibleAdmin(admin.ModelAdmin):
    """Admin pour la liaison entre retraits et charges déductibles."""
    
    list_display = ['retrait_bailleur', 'charge_deductible', 'date_ajout']
    list_filter = ['date_ajout']
    search_fields = [
        'retrait_bailleur__bailleur__nom',
        'charge_deductible__description'
    ]
    readonly_fields = ['date_ajout']
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'retrait_bailleur__bailleur', 'charge_deductible'
        )


# @admin.register(RecuRetrait)  # Modèle supprimé
class RecuRetraitAdmin(admin.ModelAdmin):
    """Admin pour les reçus de retrait."""
    
    list_display = [
        'numero_recu', 'retrait_bailleur', 'date_emission', 
        'imprime', 'format_impression'
    ]
    
    list_filter = [
        'imprime', 'format_impression', 'date_emission', 'date_impression'
    ]
    
    search_fields = [
        'numero_recu', 'retrait_bailleur__bailleur__nom',
        'retrait_bailleur__bailleur__prenom'
    ]
    
    readonly_fields = [
        'numero_recu', 'date_emission', 'genere_automatiquement'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('retrait_bailleur', 'numero_recu', 'date_emission')
        }),
        ('Impression', {
            'fields': ('imprime', 'date_impression', 'imprime_par', 'format_impression')
        }),
        ('Génération', {
            'fields': ('genere_automatiquement', 'notes_internes'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_imprimes']
    
    def marquer_imprimes(self, request, queryset):
        """Marquer les reçus sélectionnés comme imprimés."""
        count = 0
        for recu in queryset.filter(imprime=False):
            recu.marquer_imprime(request.user)
            count += 1
        
        self.message_user(
            request, 
            f'{count} reçu(s) marqué(s) comme imprimé(s).'
        )
    marquer_imprimes.short_description = "Marquer comme imprimés"
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'retrait_bailleur__bailleur', 'imprime_par'
        )


# @admin.register(TableauBordFinancier)  # Modèle supprimé
class TableauBordFinancierAdmin(admin.ModelAdmin):
    """Interface d'administration professionnelle pour les tableaux de bord financiers."""
    
    list_display = (
        'nom', 'cree_par', 'periode', 'statut_colore', 'nombre_proprietes', 
        'nombre_bailleurs', 'date_creation', 'actif'
    )
    list_filter = (
        'actif', 'periode', 'afficher_revenus', 'afficher_charges', 
        'afficher_benefices', 'afficher_taux_occupation', 'date_creation',
        'cree_par__groups'
    )
    search_fields = (
        'nom', 'description', 'cree_par__username', 'cree_par__first_name', 
        'cree_par__last_name', 'proprietes__titre', 'bailleurs__nom'
    )
    ordering = ('-date_creation',)
    list_per_page = 25
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('nom', 'description', 'actif')
        }),
        (_('Sélection des données'), {
            'fields': ('proprietes', 'bailleurs'),
            'classes': ('collapse',)
        }),
        (_('Paramètres d\'affichage'), {
            'fields': (
                'afficher_revenus', 'afficher_charges', 'afficher_benefices', 
                'afficher_taux_occupation'
            ),
            'classes': ('collapse',)
        }),
        (_('Période d\'analyse'), {
            'fields': ('periode', 'date_debut_personnalisee', 'date_fin_personnalisee')
        }),
        (_('Configuration avancée'), {
            'fields': ('seuil_alerte', 'devise', 'couleur_theme'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('cree_par', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('proprietes', 'bailleurs')
    
    actions = [
        'activer_tableaux', 'desactiver_tableaux', 'dupliquer_tableaux',
        'exporter_configurations', 'recalculer_statistiques'
    ]
    
    def statut_colore(self, obj):
        """Affiche le statut avec une couleur appropriée."""
        if not obj.actif:
            color = '#6c757d'  # Gris pour inactif
            text = 'Inactif'
        elif obj.is_alerte_active():
            color = '#dc3545'  # Rouge pour alerte
            text = 'Alerte'
        else:
            color = '#28a745'  # Vert pour actif
            text = 'Actif'
        
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 4px 8px; '
            'border-radius: 12px; background-color: {}; color: white;">{}</span>',
            'white', color, text
        )
    statut_colore.short_description = _("Statut")
    statut_colore.admin_order_field = 'actif'
    
    def nombre_proprietes(self, obj):
        """Affiche le nombre de propriétés incluses."""
        return obj.get_nombre_proprietes()
    nombre_proprietes.short_description = _("Propriétés")
    nombre_proprietes.admin_order_field = 'proprietes__count'
    
    def nombre_bailleurs(self, obj):
        """Affiche le nombre de bailleurs inclus."""
        return obj.get_nombre_bailleurs()
    nombre_bailleurs.short_description = _("Bailleurs")
    nombre_bailleurs.admin_order_field = 'bailleurs__count'
    
    def activer_tableaux(self, request, queryset):
        """Action pour activer les tableaux de bord sélectionnés."""
        updated = queryset.update(actif=True)
        self.message_user(
            request, 
            f'{updated} tableau(x) de bord activé(s) avec succès.'
        )
    activer_tableaux.short_description = _("Activer les tableaux de bord sélectionnés")
    
    def desactiver_tableaux(self, request, queryset):
        """Action pour désactiver les tableaux de bord sélectionnés."""
        updated = queryset.update(actif=False)
        self.message_user(
            request, 
            f'{updated} tableau(x) de bord désactivé(s) avec succès.'
        )
    desactiver_tableaux.short_description = _("Désactiver les tableaux de bord sélectionnés")
    
    def dupliquer_tableaux(self, request, queryset):
        """Action pour dupliquer les tableaux de bord sélectionnés."""
        duplicated = 0
        for tableau in queryset:
            # Créer une copie
            nouveau_tableau = TableauBordFinancier.objects.create(
                nom=f"{tableau.nom} (Copie)",
                description=f"Copie de {tableau.nom} - {timezone.now().strftime('%d/%m/%Y')}",
                periode=tableau.periode,
                date_debut_personnalisee=tableau.date_debut_personnalisee,
                date_fin_personnalisee=tableau.date_fin_personnalisee,
                seuil_alerte=tableau.seuil_alerte,
                devise=tableau.devise,
                couleur_theme=tableau.couleur_theme,
                afficher_revenus=tableau.afficher_revenus,
                afficher_charges=tableau.afficher_charges,
                afficher_benefices=tableau.afficher_benefices,
                afficher_taux_occupation=tableau.afficher_taux_occupation,
                actif=False,  # Désactivé par défaut
                cree_par=request.user
            )
            # Copier les relations many-to-many
            nouveau_tableau.proprietes.set(tableau.proprietes.all())
            nouveau_tableau.bailleurs.set(tableau.bailleurs.all())
            duplicated += 1
        
        self.message_user(
            request, 
            f'{duplicated} tableau(x) de bord dupliqué(s) avec succès.'
        )
    dupliquer_tableaux.short_description = _("Dupliquer les tableaux de bord sélectionnés")
    
    def exporter_configurations(self, request, queryset):
        """Action pour exporter les configurations des tableaux de bord."""
        # TODO: Implémenter l'export des configurations
        self.message_user(
            request, 
            f'Export des configurations pour {queryset.count()} tableau(x) de bord en cours de développement.'
        )
    exporter_configurations.short_description = _("Exporter les configurations")
    
    def recalculer_statistiques(self, request, queryset):
        """Action pour recalculer les statistiques des tableaux de bord."""
        # TODO: Implémenter le recalcul des statistiques
        self.message_user(
            request, 
            f'Recalcul des statistiques pour {queryset.count()} tableau(x) de bord en cours de développement.'
        )
    recalculer_statistiques.short_description = _("Recalculer les statistiques")
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related et prefetch_related."""
        return super().get_queryset(request).select_related('cree_par').prefetch_related(
            'proprietes', 'bailleurs'
        )
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle avec l'utilisateur créateur."""
        if not change:  # Nouvelle création
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        """Ajoute des styles CSS personnalisés pour l'admin."""
        css = {
            'all': ('admin/css/tableau_bord_admin.css',)
        }
        js = ('admin/js/tableau_bord_admin.js',)


# @admin.register(RecapMensuel)  # Modèle supprimé
class RecapMensuelAdmin(admin.ModelAdmin):
    """Interface d'administration pour les récapitulatifs mensuels."""
    
    list_display = (
        'id', 'bailleur', 'mois_recap', 'total_loyers_bruts', 
        'total_charges_deductibles', 'total_net_a_payer', 'statut_colore',
        'nombre_proprietes', 'nombre_contrats_actifs', 'date_creation'
    )
    list_filter = (
        'statut', 'mois_recap', 'date_creation', 'bailleur'
    )
    search_fields = (
        'bailleur__nom', 'bailleur__prenom', 'bailleur__code_bailleur'
    )
    ordering = ('-mois_recap', '-date_creation')
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('bailleur', 'mois_recap', 'statut')
        }),
        (_('Montants'), {
            'fields': ('total_loyers_bruts', 'total_charges_deductibles', 'total_net_a_payer')
        }),
        (_('Compteurs'), {
            'fields': ('nombre_proprietes', 'nombre_contrats_actifs', 'nombre_paiements_recus')
        }),
        (_('Relations'), {
            'fields': ('retraits_associes', 'paiements_concernes', 'charges_deductibles'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_validation', 'date_envoi', 'date_paiement')
        }),
        (_('Utilisateurs'), {
            'fields': ('cree_par', 'valide_par'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'total_net_a_payer')
    
    actions = ['valider_recaps', 'marquer_envoyes', 'marquer_payes', 'recalculer_totaux']
    
    def statut_colore(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'brouillon': '#6c757d',
            'valide': '#28a745',
            'envoye': '#17a2b8',
            'paye': '#007bff'
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_colore.short_description = _("Statut")
    
    def valider_recaps(self, request, queryset):
        """Action pour valider les récapitulatifs sélectionnés."""
        updated = 0
        for recap in queryset.filter(statut='brouillon'):
            recap.valider_recap(request.user)
            updated += 1
        self.message_user(request, f'{updated} récapitulatif(s) validé(s) avec succès.')
    valider_recaps.short_description = _("Valider les récapitulatifs sélectionnés")
    
    def marquer_envoyes(self, request, queryset):
        """Action pour marquer les récapitulatifs comme envoyés."""
        updated = 0
        for recap in queryset.filter(statut='valide'):
            recap.marquer_envoye(request.user)
            updated += 1
        self.message_user(request, f'{updated} récapitulatif(s) marqué(s) comme envoyé(s).')
    marquer_envoyes.short_description = _("Marquer comme envoyés")
    
    def marquer_payes(self, request, queryset):
        """Action pour marquer les récapitulatifs comme payés."""
        updated = 0
        for recap in queryset.filter(statut='envoye'):
            recap.marquer_paye(request.user)
            updated += 1
        self.message_user(request, f'{updated} récapitulatif(s) marqué(s) comme payé(s).')
    marquer_payes.short_description = _("Marquer comme payés")
    
    def recalculer_totaux(self, request, queryset):
        """Action pour recalculer les totaux des récapitulatifs."""
        updated = 0
        for recap in queryset:
            recap.calculer_totaux_bailleur()
            updated += 1
        self.message_user(request, f'{updated} récapitulatif(s) recalculé(s) avec succès.')
    recalculer_totaux.short_description = _("Recalculer les totaux")
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related et prefetch_related."""
        return super().get_queryset(request).select_related(
            'bailleur', 'cree_par', 'valide_par'
        ).prefetch_related(
            'retraits_associes', 'paiements_concernes', 'charges_deductibles'
        )
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle avec l'utilisateur créateur."""
        if not change:  # Nouvelle création
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChargeBailleur)
class ChargeBailleurAdmin(admin.ModelAdmin):
    """Interface d'administration pour les charges bailleur."""
    
    list_display = (
        'id', 'numero_charge', 'bailleur', 'description', 'montant', 'date_charge', 
        'mois_charge', 'statut_colore', 'retrait_utilise', 'cree_par'
    )
    list_filter = (
        'statut', 'date_charge', 'mois_charge', 'bailleur', 'cree_par'
    )
    search_fields = (
        'numero_charge', 'bailleur__nom', 'bailleur__prenom', 'description', 'notes'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date_charge'
    ordering = ['-date_charge', '-created_at']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('numero_charge', 'bailleur', 'description', 'montant', 'date_charge', 'mois_charge')
        }),
        (_('Statut et utilisation'), {
            'fields': ('statut', 'retrait_utilise')
        }),
        (_('Métadonnées'), {
            'fields': ('cree_par', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def statut_colore(self, obj):
        """Affiche le statut avec une couleur."""
        couleurs = {
            'en_attente': 'orange',
            'valide': 'green',
            'utilise': 'blue',
            'annule': 'red'
        }
        couleur = couleurs.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            couleur,
            obj.get_statut_display()
        )
    statut_colore.short_description = _("Statut")
    statut_colore.admin_order_field = 'statut'
    
    def get_queryset(self, request):
        """Optimise les requêtes."""
        return super().get_queryset(request).select_related(
            'bailleur', 'cree_par', 'retrait_utilise'
        )
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle avec l'utilisateur créateur."""
        if not change:  # Nouvelle création
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
