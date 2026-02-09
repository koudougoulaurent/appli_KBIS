from django.apps import AppConfig


class PaiementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paiements'
    label = 'paiements'
    
    def ready(self):
        """Configuration lors du démarrage de l'application"""
        # Importer les modèles pour qu'ils soient reconnus par Django
        from . import models
        # Importer les signaux quand l'application est prête
        try:
            from . import signals_retrait
        except ImportError:
            pass
        try:
            from . import signals_quittance
        except ImportError:
            pass
        try:
            from . import signals_financiers
        except ImportError:
            pass
        try:
            # Signal de correction automatique des avances au démarrage
            from . import signals_correction_avances
        except ImportError:
            pass
        try:
            # Signal de complétion automatique des paiements partiels
            from . import signals_paiement_partiel
        except ImportError:
            pass
        try:
            # Signal de synchronisation automatique après ajout de paiements historiques
            from . import signals_paiement_historique
        except ImportError:
            pass
