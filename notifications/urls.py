from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views, views_burkina
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
    path('<int:pk>/mark-unread/', views.mark_as_unread, name='mark_as_unread'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('notification-count/', views.notification_count, name='notification_count'),
    
    # URLs pour la gestion SMS
    path('sms/configuration/', views.sms_configuration, name='sms_configuration'),
    path('sms/historique/', views.sms_history, name='sms_history'),
    path('sms/test/', views.send_test_sms, name='send_test_sms'),
    path('sms/envoyer-retards/', views.send_overdue_notifications, name='send_overdue_notifications'),
    
    # URLs API pour les notifications dynamiques
    path('api/', include('notifications.urls_dynamiques')),
    
    # URLs pour les notifications simples
    path('', include('notifications.urls_simples')),
    
    # URLs pour le support Burkina Faso
    path('preferences-burkina/', views_burkina.preferences_burkina, name='preferences_burkina'),
    path('test-sms-burkina/', views_burkina.test_sms_burkina, name='test_sms_burkina'),
    path('validate-phone-burkina/', views_burkina.validate_phone_burkina, name='validate_phone_burkina'),
    path('format-phone-burkina/', views_burkina.format_phone_burkina, name='format_phone_burkina'),
    path('bulk-notification-burkina/', views_burkina.bulk_notification_burkina, name='bulk_notification_burkina'),
    path('phone-format-help/', views_burkina.phone_format_help, name='phone_format_help'),
] 