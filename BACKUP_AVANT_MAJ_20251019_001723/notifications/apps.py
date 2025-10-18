from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    
    def ready(self):
        """
        Importer les signaux quand l'application est prête
        """
        import notifications.signals
