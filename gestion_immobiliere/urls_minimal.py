"""
Configuration minimale des URLs pour test
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import render
from core.utils import KBISDocumentTemplate

def home_view(request):
    """Vue d'accueil simple."""
    return HttpResponse("""
    <html>
    <head><title>Test KBIS</title></head>
    <body>
        <h1>🏢 Système KBIS - Test Server</h1>
        <p>Le serveur fonctionne !</p>
        <ul>
            <li><a href="/admin/">Administration</a></li>
            <li><a href="/test-kbis/">Test système KBIS</a></li>
        </ul>
    </body>
    </html>
    """)

def test_kbis_view(request):
    """Vue de test du système KBIS."""
    
    contenu_test = """
    <h1 style="color: #2c5aa0; text-align: center;">
        🎉 TEST DU SYSTÈME KBIS !
    </h1>
    
    <div style="background: #e7f3ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h2 style="color: #2c5aa0; margin-top: 0;">Serveur Django opérationnel</h2>
        <ul>
            <li>✅ Serveur Django démarré avec succès</li>
            <li>✅ Système KBIS intégré et fonctionnel</li>
            <li>✅ Templates HTML générés</li>
            <li>✅ Styles CSS appliqués</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
        <p style="margin: 0; font-size: 18px; color: #2c5aa0;">
            <strong>Le système KBIS est opérationnel dans Django !</strong>
        </p>
    </div>
    """
    
    document_html = KBISDocumentTemplate.get_document_complet(
        "TEST KBIS - Serveur Django", 
        contenu_test
    )
    
    return HttpResponse(document_html)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('test-kbis/', test_kbis_view, name='test_kbis'),
]