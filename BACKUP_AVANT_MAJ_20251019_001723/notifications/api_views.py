from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourner seulement les notifications de l'utilisateur connecté avec filtres"""
        queryset = Notification.objects.filter(recipient=self.request.user)
        
        # Filtres manuels
        notification_type = self.request.query_params.get('type')
        priority = self.request.query_params.get('priority')
        is_read = self.request.query_params.get('is_read')
        
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        if priority:
            queryset = queryset.filter(priority=priority)
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_as_unread(self, request, pk=None):
        """Marquer une notification comme non lue"""
        notification = self.get_object()
        notification.mark_as_unread()
        return Response({'status': 'marked as unread'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Marquer toutes les notifications comme lues"""
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        return Response({'status': f'{count} notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtenir le nombre de notifications non lues"""
        count = Notification.get_unread_count(request.user)
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtenir les notifications récentes (limitées)"""
        limit = int(request.query_params.get('limit', 10))
        notifications = Notification.get_user_notifications(request.user, limit=limit)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Obtenir les notifications par type"""
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = self.get_queryset().filter(type=notification_type)
            serializer = self.get_serializer(notifications, many=True)
            return Response(serializer.data)
        return Response({'error': 'Type parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """Obtenir les notifications de haute priorité"""
        notifications = self.get_queryset().filter(
            Q(priority='high') | Q(priority='urgent')
        )
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des préférences de notification
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Retourner seulement les préférences de l'utilisateur connecté"""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associer automatiquement l'utilisateur connecté"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Obtenir les préférences de l'utilisateur connecté"""
        try:
            preferences = NotificationPreference.objects.get(user=request.user)
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
        except NotificationPreference.DoesNotExist:
            # Créer des préférences par défaut
            preferences = NotificationPreference.objects.create(user=request.user)
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Mettre à jour les préférences de notification"""
        try:
            preferences = NotificationPreference.objects.get(user=request.user)
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=request.user)
        
        serializer = self.get_serializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset_to_default(self, request):
        """Réinitialiser les préférences aux valeurs par défaut"""
        try:
            preferences = NotificationPreference.objects.get(user=request.user)
            preferences.delete()
        except NotificationPreference.DoesNotExist:
            pass
        
        preferences = NotificationPreference.objects.create(user=request.user)
        serializer = self.get_serializer(preferences)
        return Response(serializer.data) 