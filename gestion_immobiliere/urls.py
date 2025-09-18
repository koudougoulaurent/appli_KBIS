"""
URL configuration for gestion_immobiliere project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView
from . import views
import core.security_views

def redirect_to_groupes(request):
    """Redirige vers la page de connexion des groupes"""
    return redirect('utilisateurs:connexion_groupes')

urlpatterns = [
    # Redirection de la racine vers la page de connexion des groupes
    path('', include('core.urls')),
    
    # Admin Django
    path('admin/', admin.site.urls),
    
    # Authentification
    path('logout/', LogoutView.as_view(next_page='utilisateurs:connexion_groupes'), name='logout'),
    
    # Applications
    path('utilisateurs/', include('utilisateurs.urls')),
    path('proprietes/', include('proprietes.urls')),
    path('contrats/', include('contrats.urls')),
    path('paiements/', include('paiements.urls')),
    path('notifications/', include('notifications.urls')),
    path('select2/', include('django_select2.urls')),
    
    # URLs de sécurité
    path('security/', include([
        path('dashboard/', core.security_views.security_dashboard, name='security_dashboard'),
        path('alerts/', core.security_views.security_alerts_api, name='security_alerts_api'),
        path('report/', core.security_views.security_report, name='security_report'),
        path('user-status/', core.security_views.user_security_status, name='user_security_status'),
        path('health-check/', core.security_views.security_health_check, name='security_health_check'),
    ])),
]

# Gestion des erreurs en production
if not settings.DEBUG:
    handler404 = views.custom_404
    handler500 = views.custom_500
    handler403 = views.custom_403

# URLs pour les fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
