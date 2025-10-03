from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import AuditLog, ConfigurationEntreprise
from .utils import valider_logo_entreprise
from .admin_actions import (
    regenerate_all_pdfs, 
    clear_pdf_cache, 
    show_cache_stats, 
    force_regenerate_now
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
    """Formulaire personnalisé pour la configuration de l'entreprise avec validation du logo et de l'en-tête"""
    
    class Meta:
        model = ConfigurationEntreprise
        fields = '__all__'
        widgets = {
            'entete_upload': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',
                'title': 'En-tête complet de votre entreprise (remplace le logo et le texte)'
            }),
            'logo_upload': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',
                'title': 'Logo de votre entreprise'
            }),
        }
    
    def clean_entete_upload(self):
        """Valide l'en-tête uploadé"""
        entete_file = self.files.get('entete_upload')
        if entete_file:
            # Validation spécifique pour l'en-tête (plus permissive)
            if entete_file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError("L'en-tête ne doit pas dépasser 10MB")
            
            # Vérifier le type de fichier
            allowed_extensions = ['.png', '.jpg', '.jpeg']
            import os
            file_extension = os.path.splitext(entete_file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise ValidationError(f"Format non supporté. Formats autorisés: {', '.join(allowed_extensions)}")
        return entete_file
    
    def clean_logo_upload(self):
        """Valide le logo uploadé"""
        logo_file = self.files.get('logo_upload')
        if logo_file:
            validation = valider_logo_entreprise(logo_file)
            if not validation['valid']:
                raise ValidationError(validation['message'])
        return logo_file
    
    def clean_logo_url(self):
        """Valide l'URL du logo externe"""
        logo_url = self.cleaned_data.get('logo_url')
        if logo_url and not logo_url.startswith(('http://', 'https://')):
            raise ValidationError("L'URL doit commencer par http:// ou https://")
        return logo_url


@admin.register(ConfigurationEntreprise)
class ConfigurationEntrepriseAdmin(admin.ModelAdmin):
    """
    Administration de la configuration de l'entreprise
    """
    form = ConfigurationEntrepriseAdminForm
    
    list_display = ['nom_entreprise', 'ville', 'afficher_logo']
    actions = [regenerate_all_pdfs, clear_pdf_cache, show_cache_stats, force_regenerate_now]
    
    # Forcer la mise à jour des champs
    def get_form(self, request, obj=None, **kwargs):
        """Force la mise à jour du formulaire"""
        form = super().get_form(request, obj, **kwargs)
        return form
    list_filter = ['ville', 'pays']
    search_fields = ['nom_entreprise', 'adresse', 'ville', 'email']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom_entreprise', 'slogan')
        }),
        ('Adresse', {
            'fields': ('adresse', 'code_postal', 'ville', 'pays')
        }),
        ('Contact', {
            'fields': ('telephone', 'email', 'site_web')
        }),
        ('Identité visuelle', {
            'fields': ('entete_upload', 'logo_upload', 'logo_url', 'couleur_principale', 'couleur_secondaire'),
            'description': 'Configurez l\'identité visuelle de votre entreprise. L\'en-tête uploadé a la priorité absolue, puis le logo uploadé, puis l\'URL externe.'
        }),
        ('Informations légales', {
            'fields': ('siret', 'numero_licence', 'capital_social'),
            'description': 'Ces informations apparaîtront sur vos documents'
        }),
        ('Informations bancaires', {
            'fields': ('iban', 'bic', 'banque'),
            'description': 'Informations pour les paiements'
        }),
        ('Textes personnalisés', {
            'fields': ('texte_contrat', 'texte_resiliation'),
            'description': 'Textes personnalisés pour vos documents'
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['date_creation', 'date_modification', 'afficher_logo']
    
    def afficher_logo(self, obj):
        """Affiche un aperçu du logo et de l'en-tête dans l'admin"""
        # Vérifier d'abord l'en-tête personnalisé
        if obj.entete_upload:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 200px; max-height: 80px; border: 2px solid #dc3545;" alt="En-tête personnalisé" />'
                '<br><small style="color: #dc3545;"><strong>En-tête personnalisé (PRIORITÉ ABSOLUE)</strong></small>'
                '<br><small style="color: #6c757d;">Remplace complètement le logo et le texte</small>'
                '</div>',
                obj.entete_upload.url
            )
        
        # Sinon, afficher le logo
        if obj.logo_upload:
            # Logo uploadé (prioritaire)
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 100px; max-height: 60px; border: 2px solid #28a745;" alt="Logo uploadé" />'
                '<br><small style="color: #28a745;">Logo uploadé (prioritaire)</small>'
                '</div>',
                obj.logo_upload.url
            )
        elif obj.logo_url:
            # Logo externe
            if obj.logo_url.startswith('http'):
                return format_html(
                    '<div style="text-align: center;">'
                    '<img src="{}" style="max-width: 100px; max-height: 60px; border: 2px solid #007cba;" alt="Logo externe" />'
                    '<br><small style="color: #007cba;">Logo externe</small>'
                    '</div>',
                    obj.logo_url
                )
            else:
                return format_html(
                    '<div style="text-align: center;">'
                    '<img src="/media/{}" style="max-width: 100px; max-height: 60px; border: 2px solid #007cba;" alt="Logo local" />'
                    '<br><small style="color: #007cba;">Logo local</small>'
                    '</div>',
                    obj.logo_url
                )
        return format_html(
            '<div style="text-align: center; color: #6c757d; font-style: italic;">'
            'Aucun logo ni en-tête configuré'
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
