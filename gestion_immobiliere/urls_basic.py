"""
URL configuration basique pour tester
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    """Page d'accueil simple"""
    return HttpResponse("""
    <html>
    <head><title>Application Immobilière</title></head>
    <body>
        <h1>Application Immobilière</h1>
        <p>Serveur Django fonctionne correctement !</p>
        <p><a href="/admin/">Administration</a></p>
    </body>
    </html>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
]
