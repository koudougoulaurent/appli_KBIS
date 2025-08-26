from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import json

from ..models import ConfigurationEntreprise
from ..forms import ConfigurationEntrepriseForm
from ..utils import valider_logo_entreprise


@login_required
def configuration_entreprise_admin(request):
    """
    Vue admin personnalisée pour la configuration de l'entreprise
    """
    # Récupérer ou créer la configuration
    config, created = ConfigurationEntreprise.objects.get_or_create(
        actif=True,
        defaults={
            'nom_entreprise': 'GESTIMMOB',
            'adresse': '123 Rue de la Paix',
            'code_postal': '75001',
            'ville': 'Paris',
            'pays': 'France',
            'telephone': '01 23 45 67 89',
            'email': 'contact@gestimmob.fr',
            'siret': '123 456 789 00012',
            'numero_licence': '123456789',
            'forme_juridique': 'SARL',
            'couleur_principale': '#2c3e50',
            'couleur_secondaire': '#3498db',
        }
    )
    
    if request.method == 'POST':
        form = ConfigurationEntrepriseForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            # Gérer l'upload des fichiers
            if 'entete_upload' in request.FILES:
                entete_file = request.FILES['entete_upload']
                # Supprimer l'ancien fichier s'il existe
                if config.entete_upload:
                    old_path = config.entete_upload.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Sauvegarder le nouveau fichier
                file_path = default_storage.save(
                    f'entetes_entreprise/{entete_file.name}',
                    ContentFile(entete_file.read())
                )
                config.entete_upload = file_path
                messages.success(request, 'En-tête personnalisé uploadé avec succès !')
            
            if 'logo_upload' in request.FILES:
                logo_file = request.FILES['logo_upload']
                # Supprimer l'ancien fichier s'il existe
                if config.logo_upload:
                    old_path = config.logo_upload.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Sauvegarder le nouveau fichier
                file_path = default_storage.save(
                    f'logos_entreprise/{logo_file.name}',
                    ContentFile(logo_file.read())
                )
                config.logo_upload = file_path
                messages.success(request, 'Logo uploadé avec succès !')
            
            # Sauvegarder le formulaire
            form.save()
            messages.success(request, 'Configuration mise à jour avec succès !')
            return redirect('core:configuration_entreprise_admin')
        else:
            messages.error(request, 'Erreur dans le formulaire. Veuillez corriger les erreurs.')
    else:
        form = ConfigurationEntrepriseForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
        'has_entete': bool(config.entete_upload),
        'has_logo': bool(config.logo_upload),
    }
    
    return render(request, 'core/configuration_entreprise_admin.html', context)


@login_required
def supprimer_entete(request):
    """
    Supprime l'en-tête personnalisé
    """
    if request.method == 'POST':
        config = ConfigurationEntreprise.get_configuration_active()
        if config.entete_upload:
            # Supprimer le fichier
            old_path = config.entete_upload.path
            if os.path.exists(old_path):
                os.remove(old_path)
            
            # Supprimer la référence
            config.entete_upload.delete(save=False)
            config.save()
            messages.success(request, 'En-tête personnalisé supprimé !')
        else:
            messages.warning(request, 'Aucun en-tête personnalisé à supprimer.')
    
    return redirect('core:configuration_entreprise_admin')


@login_required
def supprimer_logo(request):
    """
    Supprime le logo uploadé
    """
    if request.method == 'POST':
        config = ConfigurationEntreprise.get_configuration_active()
        if config.logo_upload:
            # Supprimer le fichier
            old_path = config.logo_upload.path
            if os.path.exists(old_path):
                os.remove(old_path)
            
            # Supprimer la référence
            config.logo_upload.delete(save=False)
            config.save()
            messages.success(request, 'Logo supprimé !')
        else:
            messages.warning(request, 'Aucun logo à supprimer.')
    
    return redirect('core:configuration_entreprise_admin')


@csrf_exempt
@require_http_methods(["POST"])
def valider_fichier_upload(request):
    """
    Valide un fichier uploadé via AJAX
    """
    if 'file' not in request.FILES:
        return JsonResponse({'valid': False, 'message': 'Aucun fichier reçu'})
    
    file = request.FILES['file']
    file_type = request.POST.get('type', 'logo')
    
    if file_type == 'entete':
        # Validation spécifique pour l'en-tête
        if file.size > 10 * 1024 * 1024:  # 10MB
            return JsonResponse({'valid': False, 'message': 'Fichier trop volumineux (max 10MB)'})
        
        allowed_extensions = ['.png', '.jpg', '.jpeg']
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({'valid': False, 'message': f'Format non supporté. Formats autorisés: {", ".join(allowed_extensions)}'})
        
        return JsonResponse({'valid': True, 'message': 'En-tête valide'})
    
    else:
        # Validation pour le logo
        validation = valider_logo_entreprise(file)
        return JsonResponse(validation)
