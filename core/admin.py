from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import (
    AuditLog, ConfigurationEntreprise, NiveauAcces, PermissionTableauBord,
    LogAccesDonnees, ConfigurationTableauBord, TemplateRecu, Devise,
    TemplateDocument, HistoriqueGeneration, SecurityEvent, AutoNumberSequence
)
from .utils import valider_logo_entreprise
from .admin_actions import (
    regenerate_all_pdfs, 
    clear_pdf_cache, 
    show_cache_stats, 
    force_regenerate_now,
    suppression_definitive_conditionnelle
)

# Register your models here.

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Administration des logs d'audit
    """
    list_display = ['user', 'action', 'content_type', 'object_id', 'timestamp', 'ip_address']
    list_filter = ['action', 'content_type', 'timestamp', 'user']
    search_fields = ['user__username', 'user__email', 'description', 'action']
    readonly_fields = ['user', 'action', 'content_type', 'object_id', 'ip_address', 'user_agent', 'timestamp', 'description']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """Les logs d'audit ne peuvent pas être créés manuellement"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les logs d'audit ne peuvent pas être modifiés"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Seuls les superusers peuvent supprimer les logs d'audit"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """Optimisation des requêtes avec select_related"""
        return super().get_queryset(request).select_related('user', 'content_type')


class ConfigurationEntrepriseAdminForm(forms.ModelForm):
    """Formulaire personnalisé pour la configuration de l'entreprise avec validation du logo"""
    
    class Meta:
        model = ConfigurationEntreprise
        fields = '__all__'
        widgets = {
            'logo': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',
                'title': 'Logo de votre entreprise'
            }),
        }
    
    def clean_logo(self):
        """Valide le logo uploadé"""
        logo_file = self.files.get('logo')
        if logo_file:
            # Validation simple pour le logo
            if logo_file.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError("Le logo ne doit pas dépasser 5MB")
            
            # Vérifier le type de fichier
            allowed_extensions = ['.png', '.jpg', '.jpeg']
            import os
            file_extension = os.path.splitext(logo_file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise ValidationError(f"Format non supporté. Formats autorisés: {', '.join(allowed_extensions)}")
        return logo_file


@admin.register(ConfigurationEntreprise)
class ConfigurationEntrepriseAdmin(admin.ModelAdmin):
    """
    Administration de la configuration de l'entreprise
    """
    form = ConfigurationEntrepriseAdminForm
    
    list_display = ['nom_entreprise', 'ville', 'afficher_logo']
    actions = [regenerate_all_pdfs, clear_pdf_cache, show_cache_stats, force_regenerate_now, suppression_definitive_conditionnelle]
    
    # Forcer la mise à jour des champs
    def get_form(self, request, obj=None, **kwargs):
        """Force la mise à jour du formulaire"""
        form = super().get_form(request, obj, **kwargs)
        return form
    list_filter = ['ville', 'pays']
    search_fields = ['nom_entreprise', 'adresse_ligne1', 'ville', 'email']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom_entreprise', 'slogan')
        }),
        ('Adresse', {
            'fields': ('adresse_ligne1', 'adresse_ligne2', 'code_postal', 'ville', 'pays')
        }),
        ('Contact', {
            'fields': ('telephone', 'telephone_2', 'email', 'site_web')
        }),
        ('Identité visuelle', {
            'fields': ('logo', 'couleur_principale', 'couleur_secondaire'),
            'description': 'Configurez l\'identité visuelle de votre entreprise.'
        }),
        ('Informations légales', {
            'fields': ('rccm', 'ifu', 'numero_compte_contribuable'),
            'description': 'Ces informations apparaîtront sur vos documents'
        }),
        ('Métadonnées', {
            'fields': ('active', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['date_creation', 'date_modification', 'afficher_logo']
    
    def afficher_logo(self, obj):
        """Affiche un aperçu du logo dans l'admin"""
        # Vérifier le logo uploadé
        if obj.logo:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 100px; max-height: 60px; border: 2px solid #28a745;" alt="Logo" />'
                '<br><small style="color: #28a745;">Logo configuré</small>'
                '</div>',
                obj.logo.url
            )
        else:
            # Aucun logo configuré
            return format_html(
                '<div style="text-align: center; padding: 20px; border: 2px dashed #6c757d; background-color: #f8f9fa;">'
                '<span style="color: #6c757d; font-size: 24px;">📷</span>'
                '<br><small style="color: #6c757d;">Aucun logo configuré</small>'
                '<br><small style="color: #6c757d;">Utilisez le champ "Logo" ci-dessous</small>'
                '</div>'
            )
    
    afficher_logo.short_description = "Aperçu du logo"
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde personnalisée avec validation du logo"""
        if form.cleaned_data.get('logo_url'):
            # Le logo a été validé par le formulaire
            pass
        
        super().save_model(request, obj, form, change)
    
    class Media:
        """Ajoute des styles CSS personnalisés pour l'admin"""
        css = {
            'all': ('admin/css/configuration_entreprise.css',)
        }


@admin.register(NiveauAcces)
class NiveauAccesAdmin(admin.ModelAdmin):
    """Interface d'administration pour les niveaux d'accès."""
    
    list_display = ('nom', 'niveau', 'priorite', 'active', 'date_creation')
    list_filter = ('niveau', 'active', 'date_creation')
    search_fields = ('nom', 'description')
    ordering = ('-priorite', 'nom')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'niveau', 'description', 'priorite')
        }),
        ('Groupes autorisés', {
            'fields': ('groupes_autorises',)
        }),
        ('Statut', {
            'fields': ('active',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')
    filter_horizontal = ('groupes_autorises',)


@admin.register(PermissionTableauBord)
class PermissionTableauBordAdmin(admin.ModelAdmin):
    """Interface d'administration pour les permissions de tableaux de bord."""
    
    list_display = (
        'nom', 'type_donnees', 'niveau_acces_requis', 'peut_voir_montants',
        'peut_exporter', 'active'
    )
    list_filter = ('type_donnees', 'active', 'niveau_acces_requis')
    search_fields = ('nom', 'description')
    ordering = ('type_donnees', 'nom')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'type_donnees', 'description', 'niveau_acces_requis')
        }),
        ('Permissions spécifiques', {
            'fields': (
                'peut_voir_montants', 'peut_voir_details_personnels',
                'peut_voir_historique', 'peut_exporter', 'peut_modifier'
            )
        }),
        ('Statut', {
            'fields': ('active',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(LogAccesDonnees)
class LogAccesDonneesAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'accès aux données."""
    
    list_display = (
        'utilisateur', 'type_donnees', 'type_action', 'niveau_acces_utilise',
        'succes', 'timestamp', 'adresse_ip'
    )
    list_filter = (
        'type_donnees', 'type_action', 'succes', 'timestamp', 'niveau_acces_utilise'
    )
    search_fields = (
        'utilisateur__username', 'utilisateur__email', 'identifiant_objet', 'adresse_ip'
    )
    readonly_fields = (
        'utilisateur', 'type_donnees', 'type_action', 'niveau_acces_utilise',
        'succes', 'timestamp', 'adresse_ip', 'user_agent', 'identifiant_objet', 'message_erreur'
    )
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """Les logs ne peuvent pas être créés manuellement"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les logs ne peuvent pas être modifiés"""
        return False
    
    def get_queryset(self, request):
        """Optimisation des requêtes"""
        return super().get_queryset(request).select_related('utilisateur', 'niveau_acces_utilise')


@admin.register(ConfigurationTableauBord)
class ConfigurationTableauBordAdmin(admin.ModelAdmin):
    """Interface d'administration pour les configurations de tableaux de bord."""
    
    list_display = (
        'nom_tableau', 'utilisateur', 'par_defaut', 'date_creation'
    )
    list_filter = ('par_defaut', 'date_creation', 'utilisateur')
    search_fields = ('nom_tableau', 'utilisateur__username', 'utilisateur__email')
    ordering = ('utilisateur', '-par_defaut', 'nom_tableau')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('utilisateur', 'nom_tableau', 'par_defaut')
        }),
        ('Configuration', {
            'fields': ('widgets_actifs', 'ordre_widgets', 'configuration_widgets')
        }),
        ('Paramètres de sécurité', {
            'fields': ('masquer_montants_sensibles', 'affichage_anonymise', 'limite_donnees_recentes'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(TemplateRecu)
class TemplateRecuAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates de reçus."""
    
    list_display = (
        'nom', 'active', 'date_creation', 'date_modification'
    )
    list_filter = ('active', 'date_creation')
    search_fields = ('nom', 'description', 'contenu_html')
    ordering = ('nom',)
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'description', 'active')
        }),
        ('Template', {
            'fields': ('contenu_html', 'variables_disponibles')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(Devise)
class DeviseAdmin(admin.ModelAdmin):
    """Interface d'administration pour les devises."""
    
    list_display = (
        'code', 'nom', 'symbole', 'taux_change', 'par_defaut', 'active'
    )
    list_filter = ('par_defaut', 'active', 'date_creation')
    search_fields = ('code', 'nom', 'symbole')
    ordering = ('nom',)
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('code', 'nom', 'symbole', 'taux_change')
        }),
        ('Configuration', {
            'fields': ('par_defaut', 'active')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(TemplateDocument)
class TemplateDocumentAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates de documents."""
    
    list_display = (
        'nom', 'type_document', 'par_defaut', 'actif', 'date_creation'
    )
    list_filter = ('type_document', 'actif', 'par_defaut', 'date_creation')
    search_fields = ('nom', 'description', 'template_html')
    ordering = ('type_document', 'nom')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'type_document', 'description', 'par_defaut', 'actif')
        }),
        ('Configuration de page', {
            'fields': ('format_page', 'marge_haut', 'marge_bas', 'marge_gauche', 'marge_droite')
        }),
        ('En-tête et pied de page', {
            'fields': ('inclure_entete', 'inclure_pied_page', 'hauteur_entete', 'hauteur_pied_page'),
            'classes': ('collapse',)
        }),
        ('Template', {
            'fields': ('template_html', 'css_personnalise')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(HistoriqueGeneration)
class HistoriqueGenerationAdmin(admin.ModelAdmin):
    """Interface d'administration pour l'historique de génération de documents."""
    
    list_display = (
        'type_document', 'nom_fichier', 'type_objet', 'reference_objet', 'succes', 'date_generation'
    )
    list_filter = ('type_document', 'succes', 'date_generation')
    search_fields = (
        'nom_fichier', 'reference_objet', 'type_objet'
    )
    readonly_fields = (
        'template', 'type_document', 'nom_fichier', 'taille_fichier',
        'reference_objet', 'type_objet', 'date_generation', 'succes', 'message_erreur'
    )
    date_hierarchy = 'date_generation'
    ordering = ['-date_generation']
    
    def has_add_permission(self, request):
        """L'historique ne peut pas être créé manuellement"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """L'historique ne peut pas être modifié"""
        return False
    
    def get_queryset(self, request):
        """Optimisation des requêtes"""
        return super().get_queryset(request).select_related('template')


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Interface d'administration pour les événements de sécurité."""
    
    list_display = (
        'event_type', 'user', 'ip_address', 'severity', 'resolved', 'timestamp'
    )
    list_filter = ('event_type', 'severity', 'resolved', 'timestamp')
    search_fields = (
        'user__username', 'user__email', 'ip_address', 'description'
    )
    readonly_fields = (
        'event_type', 'severity', 'user', 'ip_address', 'user_agent',
        'timestamp', 'description', 'details', 'resolved'
    )
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """Les événements de sécurité ne peuvent pas être créés manuellement"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les événements de sécurité ne peuvent pas être modifiés"""
        return False
    
    def get_queryset(self, request):
        """Optimisation des requêtes"""
        return super().get_queryset(request).select_related('user')


@admin.register(AutoNumberSequence)
class AutoNumberSequenceAdmin(admin.ModelAdmin):
    """Interface d'administration pour les séquences de numérotation automatique."""
    
    list_display = (
        'scope', 'year', 'current'
    )
    list_filter = ('scope', 'year')
    search_fields = ('scope',)
    ordering = ('scope', 'year')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('scope', 'year', 'current')
        }),
    )
    
    readonly_fields = ()
