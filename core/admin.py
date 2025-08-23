from django.contrib import admin
from .models import AuditLog

# Register your models here.

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Administration des logs d'audit
    """
    list_display = ['user', 'action', 'content_type', 'object_repr', 'timestamp', 'ip_address']
    list_filter = ['action', 'content_type', 'timestamp', 'user']
    search_fields = ['user__username', 'user__email', 'object_repr', 'details']
    readonly_fields = ['user', 'action', 'content_type', 'object_id', 'object_repr', 'details', 'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """Les logs d'audit ne peuvent pas être créés manuellement"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Les logs d'audit ne peuvent pas être modifiés"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Seuls les superusers peuvent supprimer les logs d'audit"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """Optimisation des requêtes avec select_related"""
        return super().get_queryset(request).select_related('user', 'content_type')
