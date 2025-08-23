from django.apps import AppConfig


class PaiementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paiements'
    
    def ready(self):
        """Configuration lors du démarrage de l'application"""
        pass
