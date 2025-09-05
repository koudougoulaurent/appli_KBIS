"""
Visualiseur universel de documents pour tous les formats
Supporte la visualisation sécurisée en développement et production
"""

import os
import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_control
from django.views.decorators.http import etag
from django.core.cache import cache
from .models import Document
from .document_settings import get_viewer_config, is_format_viewable, get_external_viewer_url, should_use_external_viewer
import logging

logger = logging.getLogger(__name__)

class UniversalDocumentViewer:
    """
    Classe pour gérer la visualisation universelle de documents
    """
    
    # Formats supportés avec leurs méthodes de visualisation
    SUPPORTED_FORMATS = {
        # Images
        '.jpg': 'image',
        '.jpeg': 'image', 
        '.png': 'image',
        '.gif': 'image',
        '.webp': 'image',
        '.svg': 'image',
        '.bmp': 'image',
        '.tiff': 'image',
        
        # Documents PDF
        '.pdf': 'pdf',
        
        # Documents Office
        '.doc': 'office',
        '.docx': 'office',
        '.xls': 'office',
        '.xlsx': 'office',
        '.ppt': 'office',
        '.pptx': 'office',
        
        # Texte
        '.txt': 'text',
        '.rtf': 'text',
        '.csv': 'text',
        '.log': 'text',
        
        # Web
        '.html': 'web',
        '.htm': 'web',
        '.xml': 'web',
        
        # Archives (aperçu de contenu)
        '.zip': 'archive',
        '.rar': 'archive',
        '.7z': 'archive',
        
        # Autres
        '.json': 'code',
        '.js': 'code',
        '.css': 'code',
        '.py': 'code',
    }
    
    @staticmethod
    def get_file_info(file_path):
        """Récupère les informations détaillées d'un fichier"""
        if not os.path.exists(file_path):
            return None
            
        stat = os.stat(file_path)
        _, ext = os.path.splitext(file_path.lower())
        
        return {
            'extension': ext,
            'size': stat.st_size,
            'mime_type': mimetypes.guess_type(file_path)[0],
            'viewer_type': UniversalDocumentViewer.SUPPORTED_FORMATS.get(ext, 'download'),
            'is_viewable': ext in UniversalDocumentViewer.SUPPORTED_FORMATS,
            'filename': os.path.basename(file_path)
        }
    
    @staticmethod
    def can_user_view_document(user, document):
        """Vérifie si l'utilisateur peut voir le document"""
        # Vérifier si le document est confidentiel
        if document.confidentiel:
            # Seuls les utilisateurs PRIVILEGE peuvent voir les documents confidentiels
            if not (hasattr(user, 'groupe_travail') and 
                    user.groupe_travail and 
                    user.groupe_travail.nom == 'PRIVILEGE'):
                return False
        
        return True
    
    @staticmethod
    def get_viewer_context(document, user):
        """Prépare le contexte pour le visualiseur"""
        if not document.fichier:
            return None
            
        file_path = document.fichier.path
        file_info = UniversalDocumentViewer.get_file_info(file_path)
        
        if not file_info:
            return None
            
        context = {
            'document': document,
            'file_info': file_info,
            'can_download': True,
            'can_print': user.has_perm('proprietes.change_document'),
            'is_privilege_user': (hasattr(user, 'groupe_travail') and 
                                user.groupe_travail and 
                                user.groupe_travail.nom == 'PRIVILEGE'),
            'viewer_url': document.fichier.url,
            'download_url': f'/proprietes/documents/{document.pk}/download/',
        }
        
        # Ajouter des informations spécifiques selon le type
        viewer_type = file_info['viewer_type']
        
        if viewer_type == 'pdf':
            context.update({
                'embed_pdf': True,
                'pdf_viewer_url': f'/proprietes/documents/{document.pk}/viewer/pdf/',
            })
        elif viewer_type == 'office':
            context.update({
                'office_viewer_url': f'https://view.officeapps.live.com/op/embed.aspx?src={document.fichier.url}',
                'google_viewer_url': f'https://docs.google.com/gview?url={document.fichier.url}&embedded=true',
            })
        elif viewer_type == 'image':
            context.update({
                'direct_image': True,
            })
        elif viewer_type == 'text':
            context.update({
                'can_show_content': file_info['size'] < 1024 * 1024,  # Limite à 1MB
            })
            
        return context


@method_decorator([login_required, cache_control(max_age=3600)], name='dispatch')
class DocumentViewerView(View):
    """Vue pour la visualisation universelle des documents avec optimisations production"""
    
    def get(self, request, pk, viewer_type=None):
        """Affiche le visualiseur de document"""
        document = get_object_or_404(Document, pk=pk)
        
        # Vérifier les permissions
        if not UniversalDocumentViewer.can_user_view_document(request.user, document):
            raise PermissionDenied("Vous n'avez pas l'autorisation de consulter ce document confidentiel.")
        
        # Vérifier la taille du fichier pour la production
        config = get_viewer_config()
        if document.fichier:
            file_size = document.fichier.size
            if file_size > config['MAX_INLINE_SIZE']:
                # Rediriger vers le téléchargement pour les gros fichiers
                from django.shortcuts import redirect
                return redirect('proprietes:document_download', pk=pk)
        
        # Utiliser le cache en production
        cache_key = f"doc_viewer_context:{pk}:{request.user.id}:{viewer_type or 'default'}"
        context = cache.get(cache_key)
        
        if not context:
            # Préparer le contexte
            context = UniversalDocumentViewer.get_viewer_context(document, request.user)
            
            if not context:
                raise Http404("Document ou fichier non trouvé")
            
            # Ajouter des informations pour la production
            if should_use_external_viewer() and document.fichier:
                file_url = request.build_absolute_uri(document.fichier.url)
                context.update({
                    'external_office_url': get_external_viewer_url(file_url, 'office_microsoft'),
                    'external_google_url': get_external_viewer_url(file_url, 'office_google'),
                    'external_pdf_url': get_external_viewer_url(file_url, 'pdf_mozilla'),
                    'use_external_viewers': True,
                })
            
            # Mettre en cache pour 1 heure
            if config['SECURITY']['ENABLE_CACHE']:
                cache.set(cache_key, context, config['SECURITY']['CACHE_TIMEOUT'])
        
        # Ajouter le type de visualiseur demandé
        if viewer_type:
            context['forced_viewer_type'] = viewer_type
            
        # Log de l'accès au document
        if config['SECURITY']['LOG_ACCESS']:
            logger.info(f"Document {document.pk} ({document.nom}) consulté par {request.user.username}")
        
        return TemplateResponse(
            request,
            'proprietes/documents/document_viewer_universal.html',
            context
        )


@login_required
def document_content_view(request, pk):
    """Vue pour afficher le contenu textuel d'un document"""
    document = get_object_or_404(Document, pk=pk)
    
    # Vérifier les permissions
    if not UniversalDocumentViewer.can_user_view_document(request.user, document):
        raise PermissionDenied("Accès refusé")
    
    if not document.fichier:
        raise Http404("Fichier non trouvé")
    
    file_path = document.fichier.path
    file_info = UniversalDocumentViewer.get_file_info(file_path)
    
    if not file_info or file_info['viewer_type'] != 'text':
        raise Http404("Type de fichier non supporté pour l'affichage textuel")
    
    # Limite de taille pour éviter les problèmes de mémoire
    if file_info['size'] > 1024 * 1024:  # 1MB
        return HttpResponse("Fichier trop volumineux pour l'affichage", status=413)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return HttpResponse(content, content_type='text/plain; charset=utf-8')
    
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        return HttpResponse("Erreur lors de la lecture du fichier", status=500)


@login_required
def document_pdf_viewer(request, pk):
    """Vue spécialisée pour les PDFs avec visionneuse intégrée"""
    document = get_object_or_404(Document, pk=pk)
    
    # Vérifier les permissions
    if not UniversalDocumentViewer.can_user_view_document(request.user, document):
        raise PermissionDenied("Accès refusé")
    
    if not document.fichier:
        raise Http404("Fichier non trouvé")
    
    file_info = UniversalDocumentViewer.get_file_info(document.fichier.path)
    
    if not file_info or file_info['extension'] != '.pdf':
        raise Http404("Ce n'est pas un fichier PDF")
    
    # Retourner le fichier PDF directement pour l'affichage dans le navigateur
    response = FileResponse(
        open(document.fichier.path, 'rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'inline; filename="{file_info["filename"]}"'
    
    return response


@login_required
def document_secure_proxy(request, pk):
    """Proxy sécurisé pour servir les fichiers avec contrôle d'accès"""
    document = get_object_or_404(Document, pk=pk)
    
    # Vérifier les permissions
    if not UniversalDocumentViewer.can_user_view_document(request.user, document):
        raise PermissionDenied("Accès refusé")
    
    if not document.fichier:
        raise Http404("Fichier non trouvé")
    
    file_path = document.fichier.path
    file_info = UniversalDocumentViewer.get_file_info(file_path)
    
    if not file_info:
        raise Http404("Fichier non trouvé")
    
    # Servir le fichier avec le bon type MIME
    response = FileResponse(
        open(file_path, 'rb'),
        content_type=file_info['mime_type'] or 'application/octet-stream'
    )
    
    # Headers de sécurité
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Log de l'accès
    logger.info(f"Fichier {document.fichier.name} servi à {request.user.username}")
    
    return response
