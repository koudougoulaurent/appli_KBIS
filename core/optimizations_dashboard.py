"""
Optimisations spécifiques pour le dashboard
"""
from django.core.cache import cache
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardOptimizer:
    """Optimiseur pour le dashboard"""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_PREFIX = "dashboard_"
    
    @classmethod
    def get_cached_stats(cls, user_id=None):
        """Récupère les statistiques du dashboard depuis le cache"""
        cache_key = f"{cls.CACHE_PREFIX}stats_{user_id or 'anonymous'}"
        return cache.get(cache_key)
    
    @classmethod
    def set_cached_stats(cls, stats, user_id=None):
        """Met en cache les statistiques du dashboard"""
        cache_key = f"{cls.CACHE_PREFIX}stats_{user_id or 'anonymous'}"
        cache.set(cache_key, stats, cls.CACHE_TIMEOUT)
    
    @classmethod
    def get_optimized_stats(cls, user_id=None):
        """Calcule les statistiques optimisées du dashboard"""
        # Vérifier le cache d'abord
        cached_stats = cls.get_cached_stats(user_id)
        if cached_stats:
            return cached_stats
        
        try:
            from proprietes.models import Propriete, Locataire, Bailleur, UniteLocative
            from contrats.models import Contrat
            from paiements.models import Paiement
            from utilisateurs.models import Utilisateur
            
            # Statistiques optimisées avec requêtes efficaces
            stats = {}
            
            # 1. Statistiques des propriétés (optimisé)
            proprietes_stats = cls._get_proprietes_stats()
            stats.update(proprietes_stats)
            
            # 2. Statistiques des paiements (optimisé)
            paiements_stats = cls._get_paiements_stats()
            stats.update(paiements_stats)
            
            # 3. Statistiques des utilisateurs (optimisé)
            utilisateurs_stats = cls._get_utilisateurs_stats()
            stats.update(utilisateurs_stats)
            
            # 4. Statistiques des contrats (optimisé)
            contrats_stats = cls._get_contrats_stats()
            stats.update(contrats_stats)
            
            # Mettre en cache
            cls.set_cached_stats(stats, user_id)
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return cls._get_fallback_stats()
    
    @classmethod
    def _get_proprietes_stats(cls):
        """Statistiques optimisées des propriétés"""
        try:
            from proprietes.models import Propriete, UniteLocative
            from contrats.models import Contrat
            
            # Requête optimisée pour les propriétés
            total_proprietes = Propriete.objects.count()
            
            # Compter les unités louées et disponibles en une seule requête
            unites_stats = UniteLocative.objects.aggregate(
                total=Count('id'),
                louees=Count('id', filter=Q(contrats__est_actif=True)),
                disponibles=Count('id', filter=Q(contrats__est_actif=False))
            )
            
            return {
                'proprietes_total': total_proprietes,
                'proprietes_louees': unites_stats['louees'] or 0,
                'proprietes_disponibles': unites_stats['disponibles'] or 0,
                'unites_total': unites_stats['total'] or 0,
                'unites_louees': unites_stats['louees'] or 0,
                'unites_disponibles': unites_stats['disponibles'] or 0,
            }
        except Exception as e:
            logger.error(f"Erreur statistiques propriétés: {e}")
            return {
                'proprietes_total': 0,
                'proprietes_louees': 0,
                'proprietes_disponibles': 0,
                'unites_total': 0,
                'unites_louees': 0,
                'unites_disponibles': 0,
            }
    
    @classmethod
    def _get_paiements_stats(cls):
        """Statistiques optimisées des paiements"""
        try:
            from paiements.models import Paiement
            
            # Statistiques des paiements en une seule requête
            paiements_stats = Paiement.objects.aggregate(
                total=Count('id'),
                en_attente=Count('id', filter=Q(statut='en_attente')),
                valides=Count('id', filter=Q(statut='valide')),
                refuses=Count('id', filter=Q(statut='refuse'))
            )
            
            return {
                'paiements_total': paiements_stats['total'] or 0,
                'paiements_en_attente': paiements_stats['en_attente'] or 0,
                'paiements_valides': paiements_stats['valides'] or 0,
                'paiements_refuses': paiements_stats['refuses'] or 0,
            }
        except Exception as e:
            logger.error(f"Erreur statistiques paiements: {e}")
            return {
                'paiements_total': 0,
                'paiements_en_attente': 0,
                'paiements_valides': 0,
                'paiements_refuses': 0,
            }
    
    @classmethod
    def _get_utilisateurs_stats(cls):
        """Statistiques optimisées des utilisateurs"""
        try:
            from utilisateurs.models import Utilisateur, GroupeTravail
            from proprietes.models import Bailleur, Locataire
            
            # Statistiques des utilisateurs
            utilisateurs_total = Utilisateur.objects.count()
            groupes_total = GroupeTravail.objects.count()
            
            # Statistiques des bailleurs et locataires
            bailleurs_total = Bailleur.objects.count()
            locataires_total = Locataire.objects.count()
            
            return {
                'utilisateurs_total': utilisateurs_total,
                'groupes_total': groupes_total,
                'bailleurs_total': bailleurs_total,
                'locataires_total': locataires_total,
            }
        except Exception as e:
            logger.error(f"Erreur statistiques utilisateurs: {e}")
            return {
                'utilisateurs_total': 0,
                'groupes_total': 0,
                'bailleurs_total': 0,
                'locataires_total': 0,
            }
    
    @classmethod
    def _get_contrats_stats(cls):
        """Statistiques optimisées des contrats"""
        try:
            from contrats.models import Contrat
            
            # Statistiques des contrats en une seule requête
            contrats_stats = Contrat.objects.aggregate(
                total=Count('id'),
                actifs=Count('id', filter=Q(est_actif=True)),
                inactifs=Count('id', filter=Q(est_actif=False))
            )
            
            return {
                'contrats_total': contrats_stats['total'] or 0,
                'contrats_actifs': contrats_stats['actifs'] or 0,
                'contrats_inactifs': contrats_stats['inactifs'] or 0,
            }
        except Exception as e:
            logger.error(f"Erreur statistiques contrats: {e}")
            return {
                'contrats_total': 0,
                'contrats_actifs': 0,
                'contrats_inactifs': 0,
            }
    
    @classmethod
    def _get_fallback_stats(cls):
        """Statistiques de fallback en cas d'erreur"""
        return {
            'proprietes_total': 0,
            'proprietes_louees': 0,
            'proprietes_disponibles': 0,
            'unites_total': 0,
            'unites_louees': 0,
            'unites_disponibles': 0,
            'paiements_total': 0,
            'paiements_en_attente': 0,
            'paiements_valides': 0,
            'paiements_refuses': 0,
            'utilisateurs_total': 0,
            'groupes_total': 0,
            'bailleurs_total': 0,
            'locataires_total': 0,
            'contrats_total': 0,
            'contrats_actifs': 0,
            'contrats_inactifs': 0,
        }
    
    @classmethod
    def clear_cache(cls, user_id=None):
        """Vide le cache du dashboard"""
        cache_key = f"{cls.CACHE_PREFIX}stats_{user_id or 'anonymous'}"
        cache.delete(cache_key)
        logger.info(f"Cache dashboard vidé pour l'utilisateur {user_id}")

class DashboardAPIOptimizer:
    """Optimiseur pour les API du dashboard"""
    
    @classmethod
    def get_dashboard_stats_api(cls, request):
        """API optimisée pour les statistiques du dashboard"""
        try:
            user_id = request.user.id if request.user.is_authenticated else None
            stats = DashboardOptimizer.get_optimized_stats(user_id)
            
            return {
                'success': True,
                'data': stats,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur API dashboard: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': DashboardOptimizer._get_fallback_stats()
            }
    
    @classmethod
    def get_quick_actions_data(cls, request):
        """Données optimisées pour les actions rapides"""
        try:
            # Actions rapides basées sur les permissions de l'utilisateur
            from core.utils import check_group_permissions
            
            actions = []
            
            # Vérifier les permissions pour chaque action
            if check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'add')['allowed']:
                actions.extend([
                    {'name': 'Ajouter Propriété', 'url': '/proprietes/ajouter/', 'icon': 'plus'},
                    {'name': 'Ajouter Bailleur', 'url': '/proprietes/bailleurs/ajouter/', 'icon': 'user-plus'},
                ])
            
            if check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'add')['allowed']:
                actions.append({'name': 'Nouveau Paiement', 'url': '/paiements/ajouter/', 'icon': 'credit-card'})
            
            return {
                'success': True,
                'actions': actions
            }
        except Exception as e:
            logger.error(f"Erreur actions rapides: {e}")
            return {
                'success': False,
                'actions': []
            }
