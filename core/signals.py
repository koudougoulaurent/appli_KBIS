"""
Signaux Django pour la gestion automatique des PDF
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import ConfigurationEntreprise
from .pdf_cache import PDFCacheManager, PDFRegenerationService
import threading
import time

@receiver(post_save, sender=ConfigurationEntreprise)
def configuration_updated(sender, instance, created, **kwargs):
    """
    Signal déclenché quand la configuration de l'entreprise est modifiée
    """
    if not created:  # Seulement pour les modifications, pas la création
        print(f"🔄 Configuration de l'entreprise modifiée: {instance.nom_entreprise}")
        
        # Invalider tous les caches PDF
        PDFCacheManager.invalidate_all_pdf_cache()
        
        # Démarrer la régénération en arrière-plan
        def regenerate_documents():
            try:
                print("🚀 Démarrage de la régénération automatique des PDF...")
                result = PDFRegenerationService.regenerate_all_documents()
                
                if result['success']:
                    print(f"✅ Régénération automatique terminée: {result['total_regenerated']} documents mis à jour")
                else:
                    print(f"❌ Erreur lors de la régénération: {result.get('error', 'Erreur inconnue')}")
                    
            except Exception as e:
                print(f"❌ Erreur critique lors de la régénération: {e}")
        
        # Lancer la régénération en arrière-plan
        thread = threading.Thread(target=regenerate_documents)
        thread.daemon = True
        thread.start()

@receiver(post_delete, sender=ConfigurationEntreprise)
def configuration_deleted(sender, instance, **kwargs):
    """
    Signal déclenché quand une configuration de l'entreprise est supprimée
    """
    print(f"🗑️ Configuration de l'entreprise supprimée: {instance.nom_entreprise}")
    
    # Invalider tous les caches PDF
    PDFCacheManager.invalidate_all_pdf_cache()

def force_regenerate_all_documents():
    """
    Fonction utilitaire pour forcer la régénération de tous les documents
    """
    print("🔄 Forçage de la régénération de tous les documents PDF...")
    result = PDFRegenerationService.regenerate_all_documents()
    return result