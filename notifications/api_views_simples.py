"""
API Views pour les Notifications Simples
Endpoints REST simples et efficaces
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Notification, NotificationPreference
from .services_notifications_simples import ServiceNotificationsSimples
from .serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications_simples(request):
    """
    API simple pour récupérer les notifications
    """
    try:
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        priority = request.GET.get('priority')
        type_notification = request.GET.get('type')
        
        # Récupérer les notifications
        notifications = ServiceNotificationsSimples.get_notifications_utilisateur_simple(
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
            'statistiques': ServiceNotificationsSimples.get_statistiques_notifications_simple(request.user)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read_simple(request, notification_id):
    """
    API simple pour marquer une notification comme lue
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
def mark_all_as_read_simple(request):
    """
    API simple pour marquer toutes les notifications comme lues
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
def get_unread_count_simple(request):
    """
    API simple pour récupérer le nombre de notifications non lues
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
def get_notification_statistics_simple(request):
    """
    API simple pour récupérer les statistiques des notifications
    """
    try:
        stats = ServiceNotificationsSimples.get_statistiques_notifications_simple(request.user)
        
        return Response({
            'success': True,
            'statistiques': stats
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_notification_simple(request, notification_id):
    """
    API simple pour supprimer une notification
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
def test_notification_simple(request):
    """
    API simple pour tester l'envoi de notification
    """
    try:
        type_notification = request.data.get('type', 'info')
        message = request.data.get('message', 'Test de notification simple')
        
        notification = ServiceNotificationsSimples.creer_notification_simple(
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
def get_notification_types_simple(request):
    """
    API simple pour récupérer les types de notifications disponibles
    """
    try:
        types = ServiceNotificationsSimples.NOTIFICATION_TYPES
        
        return Response({
            'success': True,
            'types': types
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

