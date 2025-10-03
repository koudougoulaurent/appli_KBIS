"""
Actions d'administration pour la gestion des PDF
"""

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from .pdf_cache import PDFRegenerationService, PDFCacheManager
from .signals import force_regenerate_all_documents
import threading

def regenerate_all_pdfs(modeladmin, request, queryset):
    """
    Action pour régénérer tous les PDF
    """
    def regenerate_in_background():
        try:
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
    PDFCacheManager.invalidate_all_pdf_cache()
    messages.success(request, "🗑️ Cache des PDF vidé avec succès.")

clear_pdf_cache.short_description = "🗑️ Vider le cache PDF"

def show_cache_stats(modeladmin, request, queryset):
    """
    Action pour afficher les statistiques du cache
    """
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
