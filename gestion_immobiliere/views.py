from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound
from django.urls import reverse

def custom_404(request, exception=None):
    """Vue personnalisée pour les erreurs 404."""
    # Rediriger vers la page de connexion si l'URL n'existe pas
    return redirect('utilisateurs:connexion_groupes')

def custom_500(request):
    """Vue personnalisée pour les erreurs 500."""
    from django.http import HttpResponse
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Erreur 500 - Service Indisponible</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
            .message { color: #7f8c8d; font-size: 16px; margin-bottom: 30px; }
            .btn { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="error">⚠️ Erreur 500</div>
        <div class="message">Le service est temporairement indisponible. Veuillez réessayer plus tard.</div>
        <a href="/" class="btn">Retour à l'accueil</a>
    </body>
    </html>
    """, status=500)

def custom_403(request, exception=None):
    """Vue personnalisée pour les erreurs 403."""
    from django.http import HttpResponse
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Erreur 403 - Accès Refusé</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
            .message { color: #7f8c8d; font-size: 16px; margin-bottom: 30px; }
            .btn { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="error">🚫 Erreur 403</div>
        <div class="message">Accès refusé. Vous n'avez pas les permissions nécessaires.</div>
        <a href="/" class="btn">Retour à l'accueil</a>
    </body>
    </html>
    """, status=403)
