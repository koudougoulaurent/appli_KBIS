from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .utils import get_context_with_entreprise_config

@login_required
def demo_kbis_design(request):
    """
    Vue de démonstration du design KBIS professionnel
    """
    context = get_context_with_entreprise_config({
        'page_title': 'Démonstration Design KBIS',
        'page_description': 'Prévisualisation du design professionnel KBIS pour les en-têtes et pieds de page',
    })
    
    return render(request, 'demo_kbis_design.html', context)
