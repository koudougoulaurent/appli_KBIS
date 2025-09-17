"""
Système de monitoring avancé des performances
pour l'application de gestion immobilière
"""

import time
import logging
import psutil
import threading
from functools import wraps
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Moniteur de performance en temps réel"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.active_requests = {}
        self.system_metrics = {}
        self.lock = threading.Lock()
        
    def start_request(self, request_id, path, method):
        """Démarrer le monitoring d'une requête"""
        with self.lock:
            self.active_requests[request_id] = {
                'path': path,
                'method': method,
                'start_time': time.time(),
                'queries': [],
                'memory_start': psutil.Process().memory_info().rss,
            }
    
    def end_request(self, request_id, status_code):
        """Terminer le monitoring d'une requête"""
        with self.lock:
            if request_id in self.active_requests:
                request_data = self.active_requests[request_id]
                duration = time.time() - request_data['start_time']
                memory_used = psutil.Process().memory_info().rss - request_data['memory_start']
                
                # Enregistrer les métriques
                self.metrics['response_time'].append({
                    'timestamp': timezone.now().isoformat(),
                    'path': request_data['path'],
                    'method': request_data['method'],
                    'duration': duration,
                    'status_code': status_code,
                    'queries_count': len(request_data['queries']),
                    'memory_used': memory_used,
                })
                
                # Nettoyer les anciennes données
                self._cleanup_old_metrics()
                
                del self.active_requests[request_id]
    
    def add_query(self, request_id, query, duration):
        """Ajouter une requête SQL au monitoring"""
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id]['queries'].append({
                    'query': query,
                    'duration': duration,
                })
    
    def get_system_metrics(self):
        """Obtenir les métriques système"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'active_connections': len(self.active_requests),
            'timestamp': timezone.now().isoformat(),
        }
    
    def get_performance_summary(self):
        """Obtenir un résumé des performances"""
        with self.lock:
            if not self.metrics['response_time']:
                return {}
            
            recent_metrics = self.metrics['response_time'][-100:]  # 100 dernières requêtes
            
            return {
                'total_requests': len(recent_metrics),
                'average_response_time': sum(m['duration'] for m in recent_metrics) / len(recent_metrics),
                'slowest_request': max(recent_metrics, key=lambda x: x['duration']),
                'fastest_request': min(recent_metrics, key=lambda x: x['duration']),
                'queries_per_request': sum(len(m.get('queries', [])) for m in recent_metrics) / len(recent_metrics),
                'error_rate': len([m for m in recent_metrics if m['status_code'] >= 400]) / len(recent_metrics),
                'system_metrics': self.get_system_metrics(),
            }
    
    def _cleanup_old_metrics(self):
        """Nettoyer les anciennes métriques"""
        cutoff_time = time.time() - 3600  # 1 heure
        
        for metric_type in self.metrics:
            self.metrics[metric_type] = [
                m for m in self.metrics[metric_type]
                if time.mktime(timezone.datetime.fromisoformat(m['timestamp']).timetuple()) > cutoff_time
            ]

# Instance globale du moniteur
performance_monitor = PerformanceMonitor()

def monitor_performance(func):
    """Décorateur pour monitorer les performances d'une fonction"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        request_id = f"{request.META.get('REMOTE_ADDR')}_{int(time.time() * 1000)}"
        path = request.path
        method = request.method
        
        # Démarrer le monitoring
        performance_monitor.start_request(request_id, path, method)
        
        try:
            response = func(request, *args, **kwargs)
            performance_monitor.end_request(request_id, response.status_code)
            return response
        except Exception as e:
            performance_monitor.end_request(request_id, 500)
            raise
    
    return wrapper

def monitor_queries(func):
    """Décorateur pour monitorer les requêtes SQL"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        duration = time.time() - start_time
        new_queries = connection.queries[initial_queries:]
        
        # Enregistrer les requêtes lentes
        for query in new_queries:
            if float(query['time']) > 0.1:  # Requêtes > 100ms
                logger.warning(f"Slow query detected: {query['sql'][:100]}... ({query['time']}s)")
        
        return result
    
    return wrapper

class PerformanceMiddleware:
    """Middleware pour le monitoring automatique des performances"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request_id = f"{request.META.get('REMOTE_ADDR')}_{int(time.time() * 1000)}"
        path = request.path
        method = request.method
        
        # Démarrer le monitoring
        performance_monitor.start_request(request_id, path, method)
        
        # Compter les requêtes initiales
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Compter les nouvelles requêtes
        new_queries = connection.queries[initial_queries:]
        for query in new_queries:
            performance_monitor.add_query(request_id, query['sql'], float(query['time']))
        
        # Terminer le monitoring
        performance_monitor.end_request(request_id, response.status_code)
        
        # Ajouter des headers de performance
        response['X-Process-Time'] = str(time.time() - time.mktime(timezone.datetime.fromisoformat(
            performance_monitor.active_requests.get(request_id, {}).get('start_time', time.time())
        ).timetuple()))
        response['X-Query-Count'] = str(len(new_queries))
        
        return response

def get_performance_dashboard_data():
    """Obtenir les données pour le dashboard de performance"""
    summary = performance_monitor.get_performance_summary()
    
    # Ajouter des métriques de cache
    cache_stats = cache.get('cache_stats', {})
    
    return {
        'performance': summary,
        'cache': cache_stats,
        'recommendations': _get_performance_recommendations(summary),
    }

def _get_performance_recommendations(summary):
    """Obtenir des recommandations d'optimisation"""
    recommendations = []
    
    if summary.get('average_response_time', 0) > 1.0:
        recommendations.append({
            'type': 'warning',
            'message': 'Temps de réponse moyen élevé. Considérez l\'optimisation des requêtes.',
            'action': 'Optimiser les requêtes de base de données'
        })
    
    if summary.get('queries_per_request', 0) > 10:
        recommendations.append({
            'type': 'warning',
            'message': 'Trop de requêtes par requête. Utilisez select_related et prefetch_related.',
            'action': 'Optimiser les requêtes ORM'
        })
    
    if summary.get('error_rate', 0) > 0.05:
        recommendations.append({
            'type': 'error',
            'message': 'Taux d\'erreur élevé. Vérifiez les logs d\'erreur.',
            'action': 'Corriger les erreurs'
        })
    
    system_metrics = summary.get('system_metrics', {})
    if system_metrics.get('memory_percent', 0) > 80:
        recommendations.append({
            'type': 'warning',
            'message': 'Utilisation mémoire élevée. Considérez l\'optimisation du cache.',
            'action': 'Optimiser la gestion mémoire'
        })
    
    if system_metrics.get('cpu_percent', 0) > 80:
        recommendations.append({
            'type': 'warning',
            'message': 'Utilisation CPU élevée. Considérez l\'optimisation des calculs.',
            'action': 'Optimiser les calculs'
        })
    
    return recommendations

def clear_performance_cache():
    """Nettoyer le cache de performance"""
    cache.delete('performance_summary')
    cache.delete('system_metrics')
    cache.delete('cache_stats')
    logger.info("Cache de performance nettoyé")

def export_performance_data():
    """Exporter les données de performance"""
    data = {
        'timestamp': timezone.now().isoformat(),
        'performance_summary': performance_monitor.get_performance_summary(),
        'system_metrics': performance_monitor.get_system_metrics(),
    }
    
    filename = f"performance_data_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Données de performance exportées vers {filename}")
    return filename
