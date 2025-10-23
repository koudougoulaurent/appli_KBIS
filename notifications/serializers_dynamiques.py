"""
Sérialiseurs pour les Notifications Dynamiques Ultra-Fonctionnelles
Sérialisation complète avec métadonnées avancées
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Notification, NotificationPreference, SMSNotification
from .services_notifications_dynamiques import ServiceNotificationsDynamiques


class NotificationSerializer(serializers.ModelSerializer):
    """Sérialiseur de base pour les notifications"""
    
    # Champs calculés
    time_ago = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    priority_color = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    sound = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    data_extra = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'priority', 'is_read', 
            'is_sent_email', 'is_sent_sms', 'created_at', 'read_at',
            'time_ago', 'type_display', 'priority_display', 'priority_color',
            'icon', 'sound', 'duration', 'data_extra'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def get_time_ago(self, obj):
        """Calcule le temps écoulé depuis la création"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"
    
    def get_type_display(self, obj):
        """Retourne l'affichage du type de notification"""
        return dict(Notification.TYPE_CHOICES).get(obj.type, obj.type)
    
    def get_priority_display(self, obj):
        """Retourne l'affichage de la priorité"""
        return dict(Notification.PRIORITY_CHOICES).get(obj.priority, obj.priority)
    
    def get_priority_color(self, obj):
        """Retourne la couleur de la priorité"""
        colors = {
            'urgent': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary'
        }
        return colors.get(obj.priority, 'secondary')
    
    def get_icon(self, obj):
        """Retourne l'icône du type de notification"""
        config = ServiceNotificationsDynamiques.NOTIFICATION_TYPES.get(obj.type, {})
        return config.get('icon', 'bi-bell')
    
    def get_sound(self, obj):
        """Retourne le son du type de notification"""
        config = ServiceNotificationsDynamiques.NOTIFICATION_TYPES.get(obj.type, {})
        return config.get('sound', 'default')
    
    def get_duration(self, obj):
        """Retourne la durée d'affichage"""
        config = ServiceNotificationsDynamiques.NOTIFICATION_TYPES.get(obj.type, {})
        return config.get('duration', 5000)
    
    def get_data_extra(self, obj):
        """Retourne les données extra si disponibles"""
        if hasattr(obj, 'data_extra') and obj.data_extra:
            try:
                return json.loads(obj.data_extra)
            except (json.JSONDecodeError, TypeError):
                return None
        return None


class NotificationDetailSerializer(NotificationSerializer):
    """Sérialiseur détaillé pour les notifications"""
    
    # Informations supplémentaires
    content_object_info = serializers.SerializerMethodField()
    recipient_info = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_mark_read = serializers.SerializerMethodField()
    
    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + [
            'content_object_info', 'recipient_info', 'can_delete', 'can_mark_read'
        ]
    
    def get_content_object_info(self, obj):
        """Retourne les informations sur l'objet lié"""
        if obj.content_object:
            try:
                if hasattr(obj.content_object, 'get_nom_complet'):
                    return {
                        'type': obj.content_type.model,
                        'name': obj.content_object.get_nom_complet(),
                        'id': obj.content_object.id
                    }
                elif hasattr(obj.content_object, 'numero_contrat'):
                    return {
                        'type': obj.content_type.model,
                        'name': obj.content_object.numero_contrat,
                        'id': obj.content_object.id
                    }
                else:
                    return {
                        'type': obj.content_type.model,
                        'name': str(obj.content_object),
                        'id': obj.content_object.id
                    }
            except Exception:
                return None
        return None
    
    def get_recipient_info(self, obj):
        """Retourne les informations sur le destinataire"""
        return {
            'id': obj.recipient.id,
            'username': obj.recipient.username,
            'email': obj.recipient.email,
            'groupe': obj.recipient.groupe_travail.nom if obj.recipient.groupe_travail else None
        }
    
    def get_can_delete(self, obj):
        """Détermine si la notification peut être supprimée"""
        # Les notifications peuvent être supprimées si elles sont lues ou anciennes
        return obj.is_read or (timezone.now() - obj.created_at).days > 7
    
    def get_can_mark_read(self, obj):
        """Détermine si la notification peut être marquée comme lue"""
        return not obj.is_read


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les préférences de notification"""
    
    email_preferences = serializers.SerializerMethodField()
    sms_preferences = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'email_notifications', 'browser_notifications', 'sms_notifications',
            'phone_number', 'daily_digest', 'weekly_digest', 'email_preferences',
            'sms_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_email_preferences(self, obj):
        """Retourne les préférences email"""
        return obj.get_email_preferences()
    
    def get_sms_preferences(self, obj):
        """Retourne les préférences SMS"""
        return obj.get_sms_preferences()


class SMSNotificationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les notifications SMS"""
    
    status_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = SMSNotification
        fields = [
            'id', 'phone_number', 'message', 'status', 'provider',
            'provider_message_id', 'attempts', 'max_attempts',
            'created_at', 'sent_at', 'delivered_at',
            'status_display', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'delivered_at']
    
    def get_status_display(self, obj):
        """Retourne l'affichage du statut"""
        return dict(SMSNotification.STATUS_CHOICES).get(obj.status, obj.status)
    
    def get_time_ago(self, obj):
        """Calcule le temps écoulé depuis la création"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"


class NotificationStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des notifications"""
    
    total = serializers.IntegerField()
    non_lues = serializers.IntegerField()
    aujourd_hui = serializers.IntegerField()
    cette_semaine = serializers.IntegerField()
    par_priorite = serializers.DictField()
    
    def to_representation(self, instance):
        """Formate les statistiques pour l'affichage"""
        data = super().to_representation(instance)
        
        # Ajouter des informations calculées
        data['pourcentage_lues'] = round(
            (data['total'] - data['non_lues']) / data['total'] * 100, 2
        ) if data['total'] > 0 else 0
        
        data['tendance'] = self._calculer_tendance(instance)
        
        return data
    
    def _calculer_tendance(self, stats):
        """Calcule la tendance des notifications"""
        # Logique simple pour déterminer la tendance
        if stats['aujourd_hui'] > stats['cette_semaine'] / 7:
            return 'increasing'
        elif stats['aujourd_hui'] < stats['cette_semaine'] / 7:
            return 'decreasing'
        else:
            return 'stable'


class NotificationDashboardSerializer(serializers.Serializer):
    """Sérialiseur pour le dashboard des notifications"""
    
    statistiques = NotificationStatsSerializer()
    notifications_recentes = NotificationSerializer(many=True)
    par_priorite = serializers.DictField()
    par_type = serializers.DictField()
    derniere_activite = serializers.DateTimeField()
    
    def to_representation(self, instance):
        """Formate les données du dashboard"""
        data = super().to_representation(instance)
        
        # Ajouter des métadonnées calculées
        data['alertes_urgentes'] = instance['par_priorite'].get('urgent', 0)
        data['alertes_importantes'] = instance['par_priorite'].get('high', 0)
        data['total_alertes'] = data['alertes_urgentes'] + data['alertes_importantes']
        
        # Calculer le niveau d'alerte global
        if data['alertes_urgentes'] > 0:
            data['niveau_alerte'] = 'critical'
        elif data['alertes_importantes'] > 3:
            data['niveau_alerte'] = 'high'
        elif data['alertes_importantes'] > 0:
            data['niveau_alerte'] = 'medium'
        else:
            data['niveau_alerte'] = 'low'
        
        return data


