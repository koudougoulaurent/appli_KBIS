"""
Utilitaires de cache pour optimiser la génération des PDFs
"""
import base64
import os
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class ImageCache:
    """Cache pour les images encodées en base64."""
    
    CACHE_KEY_ENTETE = 'pdf_entete_image_base64'
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 heures
    
    @classmethod
    def get_entete_base64(cls):
        """
        Récupère l'image d'en-tête encodée en base64 depuis le cache.
        Si elle n'est pas en cache, la charge et la met en cache.
        
        Returns:
            str: Image encodée en base64
        """
        # Essayer de récupérer depuis le cache
        entete_base64 = cache.get(cls.CACHE_KEY_ENTETE)
        
        if entete_base64 is not None:
            logger.debug("Image d'en-tête récupérée depuis le cache")
            return entete_base64
        
        # Si pas en cache, charger l'image
        logger.debug("Chargement et mise en cache de l'image d'en-tête")
        image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'enteteEnImage.png')
        
        try:
            with open(image_path, "rb") as image_file:
                entete_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Mettre en cache pour 24 heures
            cache.set(cls.CACHE_KEY_ENTETE, entete_base64, cls.CACHE_TIMEOUT)
            return entete_base64
            
        except Exception as e:
            logger.warning(f"Impossible de charger l'image d'en-tête: {e}")
            return ""
    
    @classmethod
    def invalidate_entete(cls):
        """Invalide le cache de l'image d'en-tête."""
        cache.delete(cls.CACHE_KEY_ENTETE)
        logger.info("Cache de l'image d'en-tête invalidé")

