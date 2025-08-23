from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views
from .views import notification_list

# Router pour l'API
router = DefaultRouter()
router.register(r'notifications', api_views.NotificationViewSet, basename='notification')
router.register(r'preferences', api_views.NotificationPreferenceViewSet, basename='notification-preference')

app_name = 'notifications'

urlpatterns = [
    # URLs pour l'API
    path('api/', include(router.urls)),
    
    # URLs pour les vues web
    path('', notification_list, name='notification_list'),
    path('<int:pk>/', views.notification_detail, name='notification_detail'),
    path('preferences/', views.preferences, name='preferences'),
    
    # URLs pour les actions AJAX
    path('<int:pk>/mark-read/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('notification-count/', views.notification_count, name='notification_count'),
    
    # URLs pour la gestion SMS
    path('sms/configuration/', views.sms_configuration, name='sms_configuration'),
    path('sms/historique/', views.sms_history, name='sms_history'),
    path('sms/test/', views.send_test_sms, name='send_test_sms'),
    path('sms/envoyer-retards/', views.send_overdue_notifications, name='send_overdue_notifications'),
] 