from django.contrib import admin
from .models import RetraitBailleur, RetraitQuittance

# Enregistrement des modèles de retraits
admin.site.register(RetraitBailleur)

@admin.register(RetraitQuittance)
class RetraitQuittanceAdmin(admin.ModelAdmin):
    """Admin pour les quittances de retrait."""
    
    list_display = ['numero_quittance', 'retrait', 'date_emission', 'cree_par']
    list_filter = ['date_emission', 'cree_par']
    search_fields = ['numero_quittance', 'retrait__bailleur__nom', 'retrait__bailleur__prenom']
    readonly_fields = ['numero_quittance', 'date_emission', 'created_at']
