"""
Vue de téléchargement simplifiée et robuste
"""

from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from .models import Document
import os
import mimetypes

@login_required
def simple_document_download(request, pk):
    """Vue de téléchargement simplifiée et robuste"""
    try:
        # Récupérer le document
        document = get_object_or_404(Document, pk=pk)
        
        # Vérifier que le document a un fichier
        if not document.fichier:
            return HttpResponse("❌ Ce document n'a pas de fichier associé.", status=404)
        
        # Vérifier que le fichier existe sur le disque
        file_path = document.fichier.path
        if not os.path.exists(file_path):
            return HttpResponse(f"❌ Fichier introuvable: {document.fichier.name}", status=404)
        
        # Vérifier les permissions pour les documents confidentiels
        if document.confidentiel:
            is_privilege = (hasattr(request.user, 'groupe_travail') and 
                          request.user.groupe_travail and 
                          request.user.groupe_travail.nom == 'PRIVILEGE')
            
            if not is_privilege:
                return HttpResponse("❌ Accès refusé: Document confidentiel", status=403)
        
        # Déterminer le type MIME
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Créer la réponse de téléchargement
        try:
            # Ouvrir le fichier en mode binaire
            file_handle = open(file_path, 'rb')
            
            response = FileResponse(
                file_handle,
                as_attachment=True,
                filename=os.path.basename(document.fichier.name),
                content_type=mime_type
            )
            
            # Headers de sécurité
            response['X-Content-Type-Options'] = 'nosniff'
            response['Content-Length'] = os.path.getsize(file_path)
            
            return response
            
        except Exception as file_error:
            return HttpResponse(f"❌ Erreur de lecture du fichier: {file_error}", status=500)
    
    except Exception as e:
        return HttpResponse(f"❌ Erreur générale: {e}", status=500)

@login_required
def simple_document_view(request, pk):
    """Vue de visualisation simplifiée pour images"""
    try:
        # Récupérer le document
        document = get_object_or_404(Document, pk=pk)
        
        # Vérifier que le document a un fichier
        if not document.fichier:
            return HttpResponse("❌ Ce document n'a pas de fichier associé.", status=404)
        
        # Vérifier que le fichier existe
        file_path = document.fichier.path
        if not os.path.exists(file_path):
            return HttpResponse(f"❌ Fichier introuvable: {document.fichier.name}", status=404)
        
        # Vérifier les permissions
        if document.confidentiel:
            is_privilege = (hasattr(request.user, 'groupe_travail') and 
                          request.user.groupe_travail and 
                          request.user.groupe_travail.nom == 'PRIVILEGE')
            
            if not is_privilege:
                return HttpResponse("❌ Accès refusé: Document confidentiel", status=403)
        
        # Déterminer le type MIME
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Pour les images, afficher directement
        if mime_type.startswith('image/'):
            try:
                file_handle = open(file_path, 'rb')
                response = FileResponse(
                    file_handle,
                    content_type=mime_type
                )
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(document.fichier.name)}"'
                return response
            except Exception as e:
                return HttpResponse(f"❌ Erreur de lecture de l'image: {e}", status=500)
        
        # Pour les autres types, proposer le téléchargement
        return simple_document_download(request, pk)
    
    except Exception as e:
        return HttpResponse(f"❌ Erreur générale: {e}", status=500)
