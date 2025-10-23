"""
URLs pour les Notifications Dynamiques Ultra-Fonctionnelles
Endpoints complets pour l'API et l'interface
"""
from django.urls import path, include
from . import api_views_dynamiques, views

app_name = 'notifications'

urlpatterns = [
    # URLs existantes (compatibilité)
    path('', views.notification_list, name='notification_list'),
    path('preferences/', views.preferences, name='preferences'),
    path('sms-configuration/', views.sms_configuration, name='sms_configuration'),
    path('sms-history/', views.sms_history, name='sms_history'),
    path('mark-read/<int:pk>/', views.mark_as_read, name='mark_as_read'),
    path('mark-unread/<int:pk>/', views.mark_as_unread, name='mark_as_unread'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('notification-count/', views.notification_count, name='notification_count'),
    path('send-test-sms/', views.send_test_sms, name='send_test_sms'),
    path('send-overdue-notifications/', views.send_overdue_notifications, name='send_overdue_notifications'),
    
    # URLs API pour les notifications dynamiques
    path('api/recentes/', api_views_dynamiques.get_notifications_recentes, name='api_recentes'),
    path('api/detail/<int:notification_id>/', api_views_dynamiques.get_notification_detail, name='api_detail'),
    path('api/mark-read/<int:notification_id>/', api_views_dynamiques.mark_notification_read, name='api_mark_read'),
    path('api/mark-unread/<int:notification_id>/', api_views_dynamiques.mark_notification_unread, name='api_mark_unread'),
    path('api/mark-all-read/', api_views_dynamiques.mark_all_as_read, name='api_mark_all_read'),
    path('api/unread-count/', api_views_dynamiques.get_unread_count, name='api_unread_count'),
    path('api/statistics/', api_views_dynamiques.get_notification_statistics, name='api_statistics'),
    path('api/preferences/', api_views_dynamiques.get_notification_preferences, name='api_preferences'),
    path('api/update-preferences/', api_views_dynamiques.update_notification_preferences, name='api_update_preferences'),
    path('api/delete/<int:notification_id>/', api_views_dynamiques.delete_notification, name='api_delete'),
    path('api/delete-all-read/', api_views_dynamiques.delete_all_read_notifications, name='api_delete_all_read'),
    path('api/types/', api_views_dynamiques.get_notification_types, name='api_types'),
    path('api/test/', api_views_dynamiques.test_notification, name='api_test'),
    path('api/dashboard/', api_views_dynamiques.get_notification_dashboard_data, name='api_dashboard'),
]


