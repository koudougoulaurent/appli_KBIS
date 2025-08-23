from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les notifications
    """
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    recipient_email = serializers.CharField(source='recipient.email', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'priority', 'recipient', 
            'recipient_username', 'recipient_email', 'content_type', 'object_id',
            'content_type_name', 'is_read', 'is_sent_email', 'created_at', 
            'read_at', 'time_ago'
        ]
        read_only_fields = [
            'recipient', 'content_type', 'object_id', 'is_sent_email', 
            'created_at', 'read_at', 'time_ago'
        ]
    
    def get_time_ago(self, obj):
        """Calculer le temps écoulé depuis la création"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} jour(s) ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} heure(s) ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute(s) ago"
        else:
            return "À l'instant"
    
    def validate_priority(self, value):
        """Validation de la priorité"""
        if value not in ['low', 'medium', 'high', 'urgent']:
            raise serializers.ValidationError("Priorité invalide")
        return value
    
    def validate_type(self, value):
        """Validation du type de notification"""
        valid_types = [choice[0] for choice in Notification.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError("Type de notification invalide")
        return value


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de notifications
    """
    class Meta:
        model = Notification
        fields = ['type', 'title', 'message', 'priority', 'recipient', 'content_type', 'object_id']
    
    def validate(self, data):
        """Validation personnalisée"""
        # Vérifier que content_type et object_id sont cohérents
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        
        if content_type and object_id:
            try:
                content_type.get_object_for_this_type(id=object_id)
            except:
                raise serializers.ValidationError("L'objet référencé n'existe pas")
        
        return data
    
    def create(self, validated_data):
        """Créer la notification avec validation supplémentaire"""
        notification = Notification.objects.create(**validated_data)
        return notification


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les préférences de notification
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_username', 'user_email', 'email_notifications',
            'browser_notifications', 'payment_due_email', 'payment_received_email',
            'contract_expiring_email', 'maintenance_email', 'system_alerts_email',
            'daily_digest', 'weekly_digest', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validation personnalisée"""
        # Vérifier la cohérence des préférences
        email_notifications = data.get('email_notifications', True)
        
        if not email_notifications:
            # Si les notifications email sont désactivées, désactiver tous les types
            data['payment_due_email'] = False
            data['payment_received_email'] = False
            data['contract_expiring_email'] = False
            data['maintenance_email'] = False
            data['system_alerts_email'] = False
        
        return data


class NotificationSummarySerializer(serializers.Serializer):
    """
    Sérialiseur pour le résumé des notifications
    """
    total_count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    high_priority_count = serializers.IntegerField()
    recent_notifications = NotificationSerializer(many=True)
    
    def to_representation(self, instance):
        """Représentation personnalisée"""
        return {
            'total_count': instance.get('total_count', 0),
            'unread_count': instance.get('unread_count', 0),
            'high_priority_count': instance.get('high_priority_count', 0),
            'recent_notifications': NotificationSerializer(
                instance.get('recent_notifications', []), 
                many=True
            ).data
        }


class NotificationBulkActionSerializer(serializers.Serializer):
    """
    Sérialiseur pour les actions en lot sur les notifications
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=['mark_read', 'mark_unread', 'delete'])
    
    def validate_notification_ids(self, value):
        """Valider que les IDs de notification existent"""
        user = self.context['request'].user
        existing_ids = set(
            Notification.objects.filter(
                id__in=value, 
                recipient=user
            ).values_list('id', flat=True)
        )
        
        if len(existing_ids) != len(value):
            raise serializers.ValidationError("Certaines notifications n'existent pas ou ne vous appartiennent pas")
        
        return value 