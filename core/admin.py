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
