"""
Vue de débogage pour la création de contrat
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms_debug import ContratFormDebug
from proprietes.models import Locataire
from .utils import get_proprietes_disponibles


@login_required
def ajouter_contrat_debug(request):
    """
    Vue de débogage pour ajouter un contrat
    """
    print("=== DEBUG: Vue ajouter_contrat_debug appelée ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"User groups: {list(request.user.groups.all())}")
    
    if request.method == 'POST':
        print("=== DEBUG: Formulaire POST reçu ===")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        form = ContratFormDebug(request.POST, request.FILES)
        print(f"=== DEBUG: Formulaire créé ===")
        print(f"Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print("=== DEBUG: Erreurs du formulaire ===")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
        
        if form.is_valid():
            print("=== DEBUG: Formulaire valide, sauvegarde... ===")
            try:
                contrat = form.save(commit=False)
                contrat.cree_par = request.user
                
                # Générer un numéro de contrat simple
                if not contrat.numero_contrat:
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    contrat.numero_contrat = f"CT-{timestamp}"
                
                contrat.save()
                print(f"=== DEBUG: Contrat sauvegardé avec ID: {contrat.id} ===")
                
                messages.success(
                    request,
                    f'Contrat "{contrat.numero_contrat}" ajouté avec succès!'
                )
                
                return redirect('contrats:detail', pk=contrat.pk)
                
            except Exception as e:
                print(f"=== DEBUG: Erreur lors de la sauvegarde: {e} ===")
                messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
        else:
            print("=== DEBUG: Formulaire invalide ===")
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        print("=== DEBUG: Affichage du formulaire ===")
        form = ContratFormDebug()
    
    # Récupérer les données pour le formulaire
    proprietes_disponibles = get_proprietes_disponibles()
    locataires = Locataire.objects.filter(is_deleted=False)
    
    print(f"=== DEBUG: Données du contexte ===")
    print(f"Propriétés disponibles: {proprietes_disponibles.count()}")
    print(f"Locataires disponibles: {locataires.count()}")
    
    context = {
        'form': form,
        'title': 'Ajouter un contrat (Debug)',
        'proprietes': proprietes_disponibles,
        'locataires': locataires,
        'proprietes_data': form.proprietes_data if hasattr(form, 'proprietes_data') else [],
    }
    
    return render(request, 'contrats/contrat_form_debug.html', context)
