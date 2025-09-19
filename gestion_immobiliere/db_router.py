"""
Routeur de base de données pour la migration SQLite → PostgreSQL
"""
from django.conf import settings


class DatabaseRouter:
    """
    Routeur pour gérer les opérations de base de données
    entre SQLite (source) et PostgreSQL (destination)
    """
    
    def db_for_read(self, model, **hints):
        """Déterminer quelle base de données utiliser pour la lecture"""
        if model._meta.app_label in ['utilisateurs', 'proprietes', 'contrats', 'paiements', 'core', 'notifications']:
            return 'default'  # PostgreSQL
        return None
    
    def db_for_write(self, model, **hints):
        """Déterminer quelle base de données utiliser pour l'écriture"""
        if model._meta.app_label in ['utilisateurs', 'proprietes', 'contrats', 'paiements', 'core', 'notifications']:
            return 'default'  # PostgreSQL
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Autoriser les relations entre objets"""
        db_set = {'default', 'sqlite'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Autoriser les migrations"""
        if db == 'default':
            return app_label in ['utilisateurs', 'proprietes', 'contrats', 'paiements', 'core', 'notifications']
        elif db == 'sqlite':
            return app_label in ['utilisateurs', 'proprietes', 'contrats', 'paiements', 'core', 'notifications']
        return None
