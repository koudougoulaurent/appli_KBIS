"""
Système de monitoring des requêtes SQL pour détecter les injections
"""
import logging
import time
import json
from django.db import connection
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from typing import Dict, List, Any
from .sql_security import SQLInjectionProtection

logger = logging.getLogger(__name__)


class SQLQueryMonitor:
    """Moniteur de requêtes SQL"""
    
    def __init__(self):
        self.queries_log = []
        self.suspicious_queries = []
        self.max_log_size = getattr(settings, 'SQL_MONITORING_MAX_LOG', 1000)
    
    def log_query(self, query: str, params: List[Any] = None, execution_time: float = None):
        """
        Enregistre une requête SQL
        
        Args:
            query: La requête SQL
            params: Les paramètres de la requête
            execution_time: Temps d'exécution en secondes
        """
        query_info = {
            'timestamp': time.time(),
            'query': query,
            'params': params or [],
            'execution_time': execution_time,
            'is_suspicious': False
        }
        
        # Vérifier si la requête est suspecte
        if self._is_suspicious_query(query, params):
            query_info['is_suspicious'] = True
            self.suspicious_queries.append(query_info)
            
            # Logger l'activité suspecte
            logger.warning(f"Requête SQL suspecte détectée: {query}")
            
            # Optionnel: lever une exception
            if getattr(settings, 'SQL_MONITORING_RAISE_ON_SUSPICIOUS', False):
                raise SuspiciousOperation("Requête SQL suspecte détectée")
        
        # Ajouter au log
        self.queries_log.append(query_info)
        
        # Limiter la taille du log
        if len(self.queries_log) > self.max_log_size:
            self.queries_log = self.queries_log[-self.max_log_size:]
    
    def _is_suspicious_query(self, query: str, params: List[Any] = None) -> bool:
        """
        Détermine si une requête est suspecte
        
        Args:
            query: La requête SQL
            params: Les paramètres de la requête
            
        Returns:
            bool: True si la requête est suspecte
        """
        # Vérifier l'injection SQL dans la requête
        if SQLInjectionProtection.detect_sql_injection(query):
            return True
        
        # Vérifier l'injection SQL dans les paramètres
        if params:
            for param in params:
                if isinstance(param, str) and SQLInjectionProtection.detect_sql_injection(param):
                    return True
        
        # Vérifier les patterns suspects
        suspicious_patterns = [
            r'\bUNION\b.*\bSELECT\b',
            r'\bOR\b.*\b1\s*=\s*1\b',
            r'\bAND\b.*\b1\s*=\s*1\b',
            r'\bOR\b.*\btrue\b',
            r'\bAND\b.*\btrue\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bUPDATE\b.*\bSET\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bEXEC\b|\bEXECUTE\b',
            r'\bSCRIPT\b',
            r'--.*$',
            r'/\*.*\*/',
            r'\bSLEEP\b\s*\(',
            r'\bBENCHMARK\b\s*\(',
            r'\bWAITFOR\b\s*\(',
        ]
        
        import re
        query_upper = query.upper()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE | re.MULTILINE):
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des requêtes
        
        Returns:
            Dict contenant les statistiques
        """
        total_queries = len(self.queries_log)
        suspicious_count = len(self.suspicious_queries)
        
        # Calculer le temps d'exécution moyen
        execution_times = [q['execution_time'] for q in self.queries_log if q['execution_time']]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Compter les types de requêtes
        query_types = {}
        for query_info in self.queries_log:
            query_type = self._get_query_type(query_info['query'])
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        return {
            'total_queries': total_queries,
            'suspicious_queries': suspicious_count,
            'suspicious_percentage': (suspicious_count / total_queries * 100) if total_queries > 0 else 0,
            'average_execution_time': avg_execution_time,
            'query_types': query_types,
            'recent_suspicious': self.suspicious_queries[-10:] if self.suspicious_queries else []
        }
    
    def _get_query_type(self, query: str) -> str:
        """Détermine le type de requête"""
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def clear_logs(self):
        """Efface les logs de requêtes"""
        self.queries_log.clear()
        self.suspicious_queries.clear()
    
    def export_logs(self, file_path: str):
        """
        Exporte les logs vers un fichier
        
        Args:
            file_path: Chemin du fichier d'export
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'queries': self.queries_log,
                    'suspicious_queries': self.suspicious_queries,
                    'statistics': self.get_statistics()
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Logs SQL exportés vers {file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de l'export des logs: {e}")


# Instance globale du moniteur
query_monitor = SQLQueryMonitor()


class SQLMonitoringCursor:
    """Curseur de base de données avec monitoring"""
    
    def __init__(self, original_cursor):
        self.original_cursor = original_cursor
        self._queries = []
    
    def execute(self, sql, params=None):
        """Exécute une requête SQL avec monitoring"""
        start_time = time.time()
        
        try:
            result = self.original_cursor.execute(sql, params)
            execution_time = time.time() - start_time
            
            # Logger la requête
            query_monitor.log_query(sql, params, execution_time)
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Logger la requête même en cas d'erreur
            query_monitor.log_query(sql, params, execution_time)
            
            raise e
    
    def executemany(self, sql, param_list):
        """Exécute plusieurs requêtes SQL avec monitoring"""
        start_time = time.time()
        
        try:
            result = self.original_cursor.executemany(sql, param_list)
            execution_time = time.time() - start_time
            
            # Logger chaque requête
            for params in param_list:
                query_monitor.log_query(sql, params, execution_time / len(param_list))
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Logger les requêtes même en cas d'erreur
            for params in param_list:
                query_monitor.log_query(sql, params, execution_time / len(param_list))
            
            raise e
    
    def __getattr__(self, name):
        """Délègue les autres attributs au curseur original"""
        return getattr(self.original_cursor, name)


class SQLMonitoringConnection:
    """Connexion de base de données avec monitoring"""
    
    def __init__(self, original_connection):
        self.original_connection = original_connection
    
    def cursor(self):
        """Retourne un curseur avec monitoring"""
        original_cursor = self.original_connection.cursor()
        return SQLMonitoringCursor(original_cursor)
    
    def __getattr__(self, name):
        """Délègue les autres attributs à la connexion originale"""
        return getattr(self.original_connection, name)


def patch_database_connection():
    """Applique le monitoring à la connexion de base de données"""
    from django.db import connection
    
    if not isinstance(connection, SQLMonitoringConnection):
        # Remplacer la connexion par notre version avec monitoring
        original_connection = connection
        connection = SQLMonitoringConnection(original_connection)
        
        # Mettre à jour la référence globale
        import django.db
        django.db.connection = connection


# Appliquer le monitoring automatiquement
if getattr(settings, 'SQL_MONITORING_ENABLED', True):
    patch_database_connection()


