from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound
from django.urls import reverse

def custom_404(request, exception=None):
    """Vue personnalisée pour les erreurs 404."""
    # Rediriger vers la page de connexion si l'URL n'existe pas
    return redirect('utilisateurs:connexion_groupes')

def custom_500(request):
    """Vue personnalisée pour les erreurs 500."""
    return render(request, 'errors/500.html', status=500)

def custom_403(request, exception=None):
    """Vue personnalisée pour les erreurs 403."""
    return redirect('utilisateurs:connexion_groupes')
