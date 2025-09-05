"""
Outils de diagnostic pour le système de documents
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Document
import os
import traceback

@login_required
def document_debug_info(request, pk):
    """Vue de diagnostic pour un document"""
    try:
        document = get_object_or_404(Document, pk=pk)
        
        debug_info = {
            'document_id': document.pk,
            'document_nom': document.nom,
            'document_type': document.get_type_document_display(),
            'confidentiel': document.confidentiel,
            'has_file': bool(document.fichier),
        }
        
        if document.fichier:
            debug_info.update({
                'file_name': document.fichier.name,
                'file_path': document.fichier.path,
                'file_url': document.fichier.url,
                'file_exists': os.path.exists(document.fichier.path),
                'file_size': document.fichier.size if hasattr(document.fichier, 'size') else 'Unknown',
            })
            
            # Vérifier les permissions du fichier
            if os.path.exists(document.fichier.path):
                stat = os.stat(document.fichier.path)
                debug_info.update({
                    'file_readable': os.access(document.fichier.path, os.R_OK),
                    'file_size_on_disk': stat.st_size,
                })
        
        # Informations utilisateur
        debug_info.update({
            'user': request.user.username,
            'is_authenticated': request.user.is_authenticated,
            'user_groups': [g.name for g in request.user.groups.all()] if hasattr(request.user, 'groups') else [],
        })
        
        if hasattr(request.user, 'groupe_travail') and request.user.groupe_travail:
            debug_info['groupe_travail'] = request.user.groupe_travail.nom
        
        return JsonResponse(debug_info, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@login_required 
def document_test_download(request, pk):
    """Vue de test pour le téléchargement"""
    try:
        document = get_object_or_404(Document, pk=pk)
        
        if not document.fichier:
            return HttpResponse("❌ Pas de fichier associé", content_type='text/plain')
        
        if not os.path.exists(document.fichier.path):
            return HttpResponse(f"❌ Fichier introuvable: {document.fichier.path}", content_type='text/plain')
        
        # Test de lecture du fichier
        try:
            with open(document.fichier.path, 'rb') as f:
                first_bytes = f.read(100)  # Lire les 100 premiers bytes
            
            info = f"""✅ Test de téléchargement réussi !

Document: {document.nom}
Fichier: {document.fichier.name}
Chemin: {document.fichier.path}
Taille: {document.fichier.size} bytes
Premiers bytes: {len(first_bytes)} bytes lus

Le fichier est accessible et lisible.
"""
            return HttpResponse(info, content_type='text/plain')
            
        except Exception as read_error:
            return HttpResponse(f"❌ Erreur de lecture: {read_error}", content_type='text/plain')
        
    except Exception as e:
        return HttpResponse(f"❌ Erreur générale: {e}", content_type='text/plain')
