"""
URLs de test pour identifier le problème 'packages'
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
]

# URLs pour les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
