from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """S'exécute au démarrage de l'application"""
        import core.signals  # Import des signals pour l'initialisation automatique