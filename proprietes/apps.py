from django.apps import AppConfig


class ProprietesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proprietes'
    verbose_name = 'Propriétés'
    
    def ready(self):
        # Import des signaux si le fichier existe
        try:
            import proprietes.signals
        except ImportError:
            # Le fichier signals n'existe pas, ce n'est pas grave
            pass
