"""
API Views pour les Notifications Dynamiques Ultra-Fonctionnelles
Endpoints REST complets avec gestion en temps réel
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Notification, NotificationPreference
from .services_notifications_dynamiques import ServiceNotificationsDynamiques
from .serializers_dynamiques import NotificationSerializer, NotificationDetailSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications_recentes(request):
    """
    API pour récupérer les notifications récentes avec pagination
    """
    try:
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        priority = request.GET.get('priority')
        type_notification = request.GET.get('type')
        
        # Récupérer les notifications
        notifications = ServiceNotificationsDynamiques.get_notifications_utilisateur(
            user=request.user,
            limit=limit * 2,  # Récupérer plus pour la pagination
            unread_only=unread_only
        )
        
        # Filtres supplémentaires
        if priority:
            notifications = notifications.filter(priority=priority)
        if type_notification:
            notifications = notifications.filter(type=type_notification)
        
        # Pagination
        paginator = Paginator(notifications, limit)
        page_obj = paginator.get_page(page)
        
        # Sérialisation
        serializer = NotificationSerializer(page_obj.object_list, many=True)
        
        return Response({
            'success': True,
            'notifications': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'statistiques': ServiceNotificationsDynamiques.get_statistiques_notifications(request.user)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_detail(request, notification_id):
    """
    API pour récupérer le détail d'une notification
    """
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        serializer = NotificationDetailSerializer(notification)
        
        return Response({
            'success': True,
            'notification': serializer.data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    API pour marquer une notification comme lue
    """
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.mark_as_read()
        
        return Response({
            'success': True,
            'message': 'Notification marquée comme lue'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_unread(request, notification_id):
    """
    API pour marquer une notification comme non lue
    """
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.mark_as_unread()
        
        return Response({
            'success': True,
            'message': 'Notification marquée comme non lue'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """
    API pour marquer toutes les notifications comme lues
    """
    try:
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({
            'success': True,
            'message': f'{count} notification(s) marquée(s) comme lue(s)',
            'count': count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """
    API pour récupérer le nombre de notifications non lues
    """
    try:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({
            'success': True,
            'unread_count': unread_count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_statistics(request):
    """
    API pour récupérer les statistiques des notifications
    """
    try:
        stats = ServiceNotificationsDynamiques.get_statistiques_notifications(request.user)
        
        return Response({
            'success': True,
            'statistiques': stats
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_preferences(request):
    """
    API pour récupérer les préférences de notification
    """
    try:
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        return Response({
            'success': True,
            'preferences': {
                'email_notifications': preferences.email_notifications,
                'browser_notifications': preferences.browser_notifications,
                'sms_notifications': preferences.sms_notifications,
                'phone_number': preferences.phone_number,
                'email_preferences': preferences.get_email_preferences(),
                'sms_preferences': preferences.get_sms_preferences(),
                'daily_digest': preferences.daily_digest,
                'weekly_digest': preferences.weekly_digest,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_notification_preferences(request):
    """
    API pour mettre à jour les préférences de notification
    """
    try:
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        data = request.data
        
        # Mise à jour des préférences générales
        preferences.email_notifications = data.get('email_notifications', preferences.email_notifications)
        preferences.browser_notifications = data.get('browser_notifications', preferences.browser_notifications)
        preferences.sms_notifications = data.get('sms_notifications', preferences.sms_notifications)
        preferences.phone_number = data.get('phone_number', preferences.phone_number)
        preferences.daily_digest = data.get('daily_digest', preferences.daily_digest)
        preferences.weekly_digest = data.get('weekly_digest', preferences.weekly_digest)
        
        # Mise à jour des préférences par type
        email_prefs = data.get('email_preferences', {})
        for key, value in email_prefs.items():
            if hasattr(preferences, f'{key}_email'):
                setattr(preferences, f'{key}_email', value)
        
        sms_prefs = data.get('sms_preferences', {})
        for key, value in sms_prefs.items():
            if hasattr(preferences, f'{key}_sms'):
                setattr(preferences, f'{key}_sms', value)
        
        preferences.save()
        
        return Response({
            'success': True,
            'message': 'Préférences mises à jour avec succès'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """
    API pour supprimer une notification
    """
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.delete()
        
        return Response({
            'success': True,
            'message': 'Notification supprimée avec succès'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_all_read_notifications(request):
    """
    API pour supprimer toutes les notifications lues
    """
    try:
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=True
        ).delete()[0]
        
        return Response({
            'success': True,
            'message': f'{count} notification(s) supprimée(s)',
            'count': count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_types(request):
    """
    API pour récupérer les types de notifications disponibles
    """
    try:
        types = ServiceNotificationsDynamiques.NOTIFICATION_TYPES
        
        return Response({
            'success': True,
            'types': types
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """
    API pour tester l'envoi de notification
    """
    try:
        type_notification = request.data.get('type', 'info')
        message = request.data.get('message', 'Test de notification')
        
        notification = ServiceNotificationsDynamiques.creer_notification_intelligente(
            recipient=request.user,
            type_notification=type_notification,
            message=message,
            force_send=True
        )
        
        if notification:
            return Response({
                'success': True,
                'message': 'Notification de test envoyée avec succès',
                'notification_id': notification.id
            })
        else:
            return Response({
                'success': False,
                'error': 'Impossible d\'envoyer la notification de test'
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_dashboard_data(request):
    """
    API pour récupérer les données du dashboard des notifications
    """
    try:
        # Statistiques générales
        stats = ServiceNotificationsDynamiques.get_statistiques_notifications(request.user)
        
        # Notifications récentes (5 dernières)
        recent_notifications = ServiceNotificationsDynamiques.get_notifications_utilisateur(
            user=request.user,
            limit=5
        )
        
        # Notifications par priorité
        priority_stats = {}
        for priority in ['urgent', 'high', 'medium', 'low']:
            priority_stats[priority] = Notification.objects.filter(
                recipient=request.user,
                priority=priority,
                is_read=False
            ).count()
        
        # Notifications par type
        type_stats = {}
        for type_notif in ServiceNotificationsDynamiques.NOTIFICATION_TYPES.keys():
            type_stats[type_notif] = Notification.objects.filter(
                recipient=request.user,
                type=type_notif,
                is_read=False
            ).count()
        
        return Response({
            'success': True,
            'dashboard_data': {
                'statistiques': stats,
                'notifications_recentes': NotificationSerializer(recent_notifications, many=True).data,
                'par_priorite': priority_stats,
                'par_type': type_stats,
                'derniere_activite': Notification.objects.filter(
                    recipient=request.user
                ).order_by('-created_at').first().created_at if Notification.objects.filter(recipient=request.user).exists() else None
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
