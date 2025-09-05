"""
Configuration pour le visualiseur de documents
Optimisé pour la production avec sécurité et performance
"""

from django.conf import settings
import os

# Configuration du visualiseur de documents
DOCUMENT_VIEWER_CONFIG = {
    # Taille maximale des fichiers pour visualisation en ligne (en bytes)
    'MAX_INLINE_SIZE': 50 * 1024 * 1024,  # 50MB
    
    # Taille maximale pour le contenu textuel (en bytes)
    'MAX_TEXT_SIZE': 1 * 1024 * 1024,  # 1MB
    
    # Formats supportés pour la visualisation
    'VIEWABLE_FORMATS': {
        # Images (visualisation directe)
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff'],
        
        # PDFs (visualisation native du navigateur)
        'pdf': ['.pdf'],
        
        # Documents Office (visualiseurs en ligne)
        'office': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp'],
        
        # Texte (affichage direct)
        'text': ['.txt', '.rtf', '.csv', '.log', '.md', '.json', '.xml', '.html', '.htm'],
        
        # Code (affichage avec coloration syntaxique)
        'code': ['.py', '.js', '.css', '.php', '.java', '.c', '.cpp', '.h', '.sql'],
        
        # Archives (liste du contenu)
        'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    },
    
    # Visualiseurs externes pour la production
    'EXTERNAL_VIEWERS': {
        'office_microsoft': 'https://view.officeapps.live.com/op/embed.aspx?src=',
        'office_google': 'https://docs.google.com/gview?url=',
        'pdf_mozilla': 'https://mozilla.github.io/pdf.js/web/viewer.html?file=',
    },
    
    # Configuration de sécurité
    'SECURITY': {
        'ALLOWED_DOMAINS': ['localhost', '127.0.0.1', 'testserver'],
        'REQUIRE_AUTHENTICATION': True,
        'CHECK_PERMISSIONS': True,
        'LOG_ACCESS': True,
        'ENABLE_CACHE': True,
        'CACHE_TIMEOUT': 3600,  # 1 heure
    },
    
    # Configuration de performance
    'PERFORMANCE': {
        'ENABLE_COMPRESSION': True,
        'ENABLE_ETAG': True,
        'BROWSER_CACHE_MAX_AGE': 3600,  # 1 heure
        'CDN_FALLBACK': True,
    },
    
    # Messages d'erreur personnalisés
    'ERROR_MESSAGES': {
        'file_not_found': "Le document demandé n'a pas été trouvé.",
        'access_denied': "Vous n'avez pas l'autorisation d'accéder à ce document.",
        'file_too_large': "Le fichier est trop volumineux pour être visualisé en ligne.",
        'format_not_supported': "Ce format de fichier n'est pas supporté pour la visualisation.",
        'external_viewer_error': "Erreur lors du chargement du visualiseur externe.",
    }
}

def get_viewer_config():
    """Retourne la configuration du visualiseur"""
    return DOCUMENT_VIEWER_CONFIG

def is_format_viewable(file_extension):
    """Vérifie si un format de fichier est visualisable"""
    ext = file_extension.lower()
    for format_type, extensions in DOCUMENT_VIEWER_CONFIG['VIEWABLE_FORMATS'].items():
        if ext in extensions:
            return True, format_type
    return False, None

def get_external_viewer_url(file_url, viewer_type='office_microsoft'):
    """Génère l'URL pour un visualiseur externe"""
    base_url = DOCUMENT_VIEWER_CONFIG['EXTERNAL_VIEWERS'].get(viewer_type)
    if not base_url:
        return None
    
    # Encoder l'URL du fichier pour les visualiseurs externes
    import urllib.parse
    encoded_url = urllib.parse.quote(file_url, safe=':/?#[]@!$&\'()*+,;=')
    
    return base_url + encoded_url

def should_use_external_viewer():
    """Détermine s'il faut utiliser un visualiseur externe en production"""
    return not settings.DEBUG and settings.ALLOWED_HOSTS != ['*']

def get_cache_key(document_id, user_id, viewer_type):
    """Génère une clé de cache pour la visualisation"""
    return f"doc_viewer:{document_id}:{user_id}:{viewer_type}"

# Configuration spécifique à la production
PRODUCTION_CONFIG = {
    'USE_CDN': True,
    'CDN_DOMAINS': [
        'view.officeapps.live.com',
        'docs.google.com',
        'mozilla.github.io'
    ],
    'FALLBACK_DOWNLOAD': True,
    'SECURITY_HEADERS': {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'Content-Security-Policy': "default-src 'self'; frame-src 'self' https://view.officeapps.live.com https://docs.google.com https://mozilla.github.io;",
    }
}

def get_production_config():
    """Configuration optimisée pour la production"""
    return PRODUCTION_CONFIG
