"""
Actions d'administration pour la gestion des PDF et suppression conditionnelle
"""

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.core.exceptions import PermissionDenied
from django.db import transaction
import threading

def regenerate_all_pdfs(modeladmin, request, queryset):
    """
    Action pour régénérer tous les PDF
    """
    def regenerate_in_background():
        try:
            from .pdf_cache import PDFRegenerationService
            result = PDFRegenerationService.regenerate_all_documents()
            if result['success']:
                print(f"✅ Régénération automatique terminée: {result['total_regenerated']} documents mis à jour")
            else:
                print(f"❌ Erreur lors de la régénération: {result.get('error', 'Erreur inconnue')}")
        except Exception as e:
            print(f"❌ Erreur critique lors de la régénération: {e}")
    
    # Lancer la régénération en arrière-plan
    thread = threading.Thread(target=regenerate_in_background)
    thread.daemon = True
    thread.start()
    
    messages.success(
        request,
        "🔄 Régénération des PDF lancée en arrière-plan. Les documents seront mis à jour automatiquement."
    )

regenerate_all_pdfs.short_description = "🔄 Régénérer tous les PDF"

def clear_pdf_cache(modeladmin, request, queryset):
    """
    Action pour vider le cache des PDF
    """
    from .pdf_cache import PDFCacheManager
    PDFCacheManager.invalidate_all_pdf_cache()
    messages.success(request, "🗑️ Cache des PDF vidé avec succès.")

clear_pdf_cache.short_description = "🗑️ Vider le cache PDF"

def show_cache_stats(modeladmin, request, queryset):
    """
    Action pour afficher les statistiques du cache
    """
    from .pdf_cache import PDFCacheManager
    stats = PDFCacheManager.get_cache_stats()
    messages.info(
        request,
        f"📊 Statistiques du cache: Hash de configuration = {stats['current_config_hash'][:8]}..."
    )

show_cache_stats.short_description = "📊 Afficher les statistiques du cache"

def force_regenerate_now(modeladmin, request, queryset):
    """
    Action pour forcer la régénération immédiate
    """
    try:
        from .signals import force_regenerate_all_documents
        result = force_regenerate_all_documents()
        if result['success']:
            messages.success(
                request,
                f"✅ Régénération immédiate terminée: {result['total_regenerated']} documents mis à jour"
            )
        else:
            messages.error(
                request,
                f"❌ Erreur lors de la régénération: {result.get('error', 'Erreur inconnue')}"
            )
    except Exception as e:
        messages.error(request, f"❌ Erreur critique: {e}")

force_regenerate_now.short_description = "⚡ Forcer la régénération immédiate"


def suppression_definitive_conditionnelle(modeladmin, request, queryset):
    """
    Action pour suppression définitive avec conditions de sécurité
    """
    # Vérifier les permissions
    if not request.user.is_superuser:
        raise PermissionDenied("Seuls les superutilisateurs peuvent effectuer des suppressions définitives")
    
    # Compter les éléments sélectionnés
    count = queryset.count()
    
    if count == 0:
        messages.warning(request, "⚠️ Aucun élément sélectionné pour la suppression")
        return
    
    # Afficher un résumé des éléments à supprimer
    model_name = queryset.model._meta.verbose_name_plural
    messages.info(request, f"📋 {count} {model_name} sélectionné(s) pour suppression définitive")
    
    # Conditions de sécurité
    conditions_ok = True
    erreurs = []
    
    # Vérifier si des éléments ont des relations importantes
    for obj in queryset:
        # Vérifier les relations ForeignKey
        for field in obj._meta.get_fields():
            if field.many_to_one and hasattr(obj, field.name):
                related_obj = getattr(obj, field.name, None)
                if related_obj:
                    erreurs.append(f"❌ {obj} a une relation avec {related_obj}")
                    conditions_ok = False
        
        # Vérifier les relations ManyToMany
        for field in obj._meta.get_fields():
            if field.many_to_many and hasattr(obj, field.name):
                related_objects = getattr(obj, field.name, None)
                if related_objects and related_objects.exists():
                    count_related = related_objects.count()
                    erreurs.append(f"❌ {obj} a {count_related} relation(s) ManyToMany")
                    conditions_ok = False
    
    if not conditions_ok:
        messages.error(request, "🚫 Suppression annulée - Relations détectées:")
        for erreur in erreurs[:5]:  # Limiter à 5 erreurs
            messages.error(request, erreur)
        if len(erreurs) > 5:
            messages.error(request, f"... et {len(erreurs) - 5} autres relations")
        return
    
    # Demander confirmation finale
    if request.POST.get('confirm_suppression') != 'oui':
        # Afficher la page de confirmation
        context = {
            'title': f'Confirmation de suppression définitive',
            'objects': queryset,
            'count': count,
            'model_name': model_name,
            'action': 'suppression_definitive_conditionnelle',
        }
        return admin.site.admin_view(
            lambda request: admin.site.each_context(request)
        )(request)
    
    # Effectuer la suppression avec transaction
    try:
        with transaction.atomic():
            deleted_count = 0
            for obj in queryset:
                obj.delete()
                deleted_count += 1
            
            messages.success(
                request,
                f"✅ Suppression définitive réussie: {deleted_count} {model_name} supprimé(s)"
            )
            
    except Exception as e:
        messages.error(
            request,
            f"❌ Erreur lors de la suppression: {str(e)}"
        )

suppression_definitive_conditionnelle.short_description = "🗑️ Suppression définitive (avec conditions)"
