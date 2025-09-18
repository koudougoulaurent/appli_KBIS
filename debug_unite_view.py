from django.shortcuts import render
from django.contrib import messages

def debug_unite_form(request):
    """Vue de debug pour tester le formulaire d'unités locatives"""
    
    if request.method == 'POST':
        # Simuler la validation
        propriete = request.POST.get('propriete')
        numero_unite = request.POST.get('numero_unite')
        nom = request.POST.get('nom')
        type_unite = request.POST.get('type_unite')
        loyer_mensuel = request.POST.get('loyer_mensuel')
        
        errors = []
        
        if not propriete:
            errors.append('propriete: Ce champ est obligatoire')
        if not numero_unite:
            errors.append('numero_unite: Ce champ est obligatoire')
        if not nom:
            errors.append('nom: Ce champ est obligatoire')
        if not type_unite:
            errors.append('type_unite: Ce champ est obligatoire')
        if not loyer_mensuel:
            errors.append('loyer_mensuel: Ce champ est obligatoire')
        elif float(loyer_mensuel) <= 0:
            errors.append('loyer_mensuel: Le loyer doit être supérieur à 0')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            messages.success(request, 'Formulaire validé avec succès ! (Simulation)')
    
    return render(request, 'debug_unite_form.html')
