from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'type', 'priority', 'is_read', 'created_at']
    list_filter = ['type', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'message', 'type', 'priority')
        }),
        ('Destinataire', {
            'fields': ('recipient',)
        }),
        ('Référence', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('État', {
            'fields': ('is_read', 'is_sent_email', 'read_at')
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_sent']
    
    def mark_as_read(self, request, queryset):
        """Marquer les notifications sélectionnées comme lues"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_unread(self, request, queryset):
        """Marquer les notifications sélectionnées comme non lues"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme non lue(s).')
    mark_as_unread.short_description = "Marquer comme non lues"
    
    def mark_as_sent(self, request, queryset):
        """Marquer les notifications sélectionnées comme envoyées par email"""
        updated = queryset.update(is_sent_email=True)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme envoyée(s).')
    mark_as_sent.short_description = "Marquer comme envoyées par email"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_notifications', 'browser_notifications', 'daily_digest', 'weekly_digest']
    list_filter = ['email_notifications', 'browser_notifications', 'daily_digest', 'weekly_digest']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Notifications générales', {
            'fields': ('email_notifications', 'browser_notifications')
        }),
        ('Préférences par type', {
            'fields': (
                'payment_due_email', 'payment_received_email', 
                'contract_expiring_email', 'maintenance_email', 'system_alerts_email'
            )
        }),
        ('Digest', {
            'fields': ('daily_digest', 'weekly_digest')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 