"""
URLs pour les Notifications Simples
Endpoints simples et efficaces
"""
from django.urls import path
from . import api_views_simples

app_name = 'notifications_simples'

urlpatterns = [
    # URLs API pour les notifications simples
    path('api/simples/', api_views_simples.get_notifications_simples, name='api_simples'),
    path('api/simples/mark-read/<int:notification_id>/', api_views_simples.mark_notification_read_simple, name='api_mark_read_simple'),
    path('api/simples/mark-all-read/', api_views_simples.mark_all_as_read_simple, name='api_mark_all_read_simple'),
    path('api/simples/unread-count/', api_views_simples.get_unread_count_simple, name='api_unread_count_simple'),
    path('api/simples/statistics/', api_views_simples.get_notification_statistics_simple, name='api_statistics_simple'),
    path('api/simples/delete/<int:notification_id>/', api_views_simples.delete_notification_simple, name='api_delete_simple'),
    path('api/simples/test/', api_views_simples.test_notification_simple, name='api_test_simple'),
    path('api/simples/types/', api_views_simples.get_notification_types_simple, name='api_types_simple'),
]

