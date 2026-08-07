"""
Service d'optimisation des requêtes pour le système des avances.
Améliore significativement les performances en évitant les requêtes N+1 et en optimisant les requêtes.
"""
from django.db.models import Q, Prefetch, Count, Sum
from django.core.cache import cache
from decimal import Decimal
from datetime import date
from typing import Dict, Optional


class ServiceOptimisationAvances:
    """
    Service pour optimiser les requêtes sur les avances de loyer.
    """
    
    # Clé de cache pour éviter les appels répétés à consommer_avances_automatiquement
    CACHE_KEY_CONSOMMATION = 'avances_consommation_en_cours'
    CACHE_TIMEOUT_CONSOMMATION = 60  # 1 minute
    
    @staticmethod
    def get_avances_optimisees(filters: Optional[Dict] = None, prefetch_consommations: bool = True):
        """
        Récupère les avances avec toutes les optimisations nécessaires.
        
        Args:
            filters: Dictionnaire de filtres à appliquer (contrat_id, statut, mois_debut, mois_fin)
            prefetch_consommations: Si True, précharge les consommations pour éviter N+1
        
        Returns:
            QuerySet optimisé des avances
        """
        from .models_avance import AvanceLoyer, ConsommationAvance
        
        # Base queryset avec select_related pour éviter N+1
        queryset = AvanceLoyer.objects.select_related(
            'contrat',
            'contrat__locataire',
            'contrat__propriete',
            'contrat__propriete__bailleur',
            'paiement'
        )
        
        # Précharger les consommations si demandé
        if prefetch_consommations:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'consommations',
                    queryset=ConsommationAvance.objects.select_related('paiement').order_by('-mois_consomme'),
                    to_attr='consommations_prefetched'
                )
            )
        
        # Appliquer les filtres en base de données (beaucoup plus rapide que Python)
        if filters:
            if filters.get('contrat_id'):
                queryset = queryset.filter(contrat_id=filters['contrat_id'])
            
            if filters.get('statut'):
                queryset = queryset.filter(statut=filters['statut'])
            
            if filters.get('mois_debut'):
                queryset = queryset.filter(date_avance__gte=filters['mois_debut'])
            
            if filters.get('mois_fin'):
                queryset = queryset.filter(date_avance__lte=filters['mois_fin'])
        
        return queryset.order_by('-date_avance')
    
    @staticmethod
    def get_avance_detail_optimisee(avance_id: int):
        """
        Récupère une avance avec toutes ses relations préchargées pour la vue détail.
        
        Args:
            avance_id: ID de l'avance
        
        Returns:
            Instance d'AvanceLoyer avec toutes les relations préchargées
        """
        from .models_avance import AvanceLoyer, ConsommationAvance
        from .models import Paiement
        
        return AvanceLoyer.objects.select_related(
            'contrat',
            'contrat__locataire',
            'contrat__propriete',
            'contrat__propriete__bailleur',
            'paiement'
        ).prefetch_related(
            Prefetch(
                'consommations',
                queryset=ConsommationAvance.objects.select_related('paiement').order_by('-mois_consomme')
            ),
            Prefetch(
                'contrat__paiements',
                # *** CORRECTION : pas de slice dans un Prefetch. ***
                # Django applique ensuite un .filter() sur ce queryset pour le
                # rattacher a l'objet parent, ce qui leve
                # "Cannot filter a query once a slice has been taken"
                # et renvoyait une 500 sur /paiements/avances/detail/<id>/.
                # La limitation eventuelle se fait cote template/vue.
                queryset=Paiement.objects.filter(
                    type_paiement='loyer',
                    statut='valide'
                ).order_by('-date_paiement')
            )
        ).get(id=avance_id)
    
    @staticmethod
    def get_avances_contrat_optimisees(contrat_id: int, statut: Optional[str] = None):
        """
        Récupère toutes les avances d'un contrat avec optimisations.
        
        Args:
            contrat_id: ID du contrat
            statut: Statut optionnel pour filtrer
        
        Returns:
            QuerySet optimisé des avances du contrat
        """
        from .models_avance import AvanceLoyer, ConsommationAvance
        
        queryset = AvanceLoyer.objects.filter(
            contrat_id=contrat_id
        ).select_related(
            'contrat',
            'contrat__locataire',
            'paiement'
        ).prefetch_related(
            Prefetch(
                'consommations',
                queryset=ConsommationAvance.objects.order_by('-mois_consomme')
            )
        )
        
        if statut:
            queryset = queryset.filter(statut=statut)
        
        return queryset.order_by('date_avance')
    
    @staticmethod
    def calculer_stats_avances_optimisees(filters: Optional[Dict] = None):
        """
        Calcule les statistiques des avances en une seule requête optimisée.
        
        Args:
            filters: Dictionnaire de filtres optionnels
        
        Returns:
            Dictionnaire avec les statistiques
        """
        from .models_avance import AvanceLoyer
        
        queryset = AvanceLoyer.objects.all()
        
        # Appliquer les filtres
        if filters:
            if filters.get('contrat_id'):
                queryset = queryset.filter(contrat_id=filters['contrat_id'])
            if filters.get('statut'):
                queryset = queryset.filter(statut=filters['statut'])
            if filters.get('mois_debut'):
                queryset = queryset.filter(date_avance__gte=filters['mois_debut'])
            if filters.get('mois_fin'):
                queryset = queryset.filter(date_avance__lte=filters['mois_fin'])
        
        # Calculer toutes les stats en une seule requête
        stats = queryset.aggregate(
            total_avances=Count('id'),
            avances_actives=Count('id', filter=Q(statut='active')),
            avances_epuisees=Count('id', filter=Q(statut='epuisee')),
            montant_total_avances=Sum('montant_avance'),
            montant_restant_total=Sum('montant_restant')
        )
        
        return {
            'total_avances': stats['total_avances'] or 0,
            'avances_actives': stats['avances_actives'] or 0,
            'avances_epuisees': stats['avances_epuisees'] or 0,
            'montant_total_avances': stats['montant_total_avances'] or Decimal('0'),
            'montant_restant': stats['montant_restant_total'] or Decimal('0'),
        }
    
    @staticmethod
    def consommer_avances_avec_cache(contrat_id: Optional[int] = None, force: bool = False):
        """
        Consomme les avances automatiquement avec cache pour éviter les appels répétés.
        
        Args:
            contrat_id: ID du contrat optionnel (si None, consomme toutes les avances)
            force: Si True, force la consommation même si elle est en cache
        
        Returns:
            Résultat de la consommation
        """
        from .services_consommation_dynamique import ServiceConsommationDynamique
        
        # Clé de cache spécifique au contrat ou globale
        cache_key = f"{ServiceOptimisationAvances.CACHE_KEY_CONSOMMATION}_{contrat_id or 'all'}"
        
        # Vérifier le cache pour éviter les appels répétés
        if not force:
            cache_value = cache.get(cache_key)
            if cache_value:
                # Retourner un résultat vide si déjà en cours ou récemment exécuté
                return {
                    'consommees': 0,
                    'erreurs': 0,
                    'total': 0,
                    'from_cache': True
                }
        
        # Marquer comme en cours
        cache.set(cache_key, True, ServiceOptimisationAvances.CACHE_TIMEOUT_CONSOMMATION)
        
        try:
            # Exécuter la consommation
            resultat = ServiceConsommationDynamique.consommer_avances_automatiquement(
                contrat_id if contrat_id else None
            )
            return resultat
        finally:
            # Ne pas supprimer le cache immédiatement pour éviter les appels répétés
            pass
    
    @staticmethod
    def get_dashboard_stats_optimisees():
        """
        Calcule les statistiques du dashboard en requêtes optimisées.
        
        Returns:
            Dictionnaire avec toutes les statistiques du dashboard
        """
        from .models_avance import AvanceLoyer
        from contrats.models import Contrat
        
        mois_courant = date.today().replace(day=1)
        
        # Toutes les stats en une seule requête avec annotations
        stats = AvanceLoyer.objects.aggregate(
            total_avances_actives=Count('id', filter=Q(statut='active')),
            total_avances_epuisees=Count('id', filter=Q(statut='epuisee')),
            montant_total_avances=Sum('montant_avance', filter=Q(statut='active')),
            avances_ce_mois=Count('id', filter=Q(
                statut='active',
                date_avance__year=mois_courant.year,
                date_avance__month=mois_courant.month
            )),
            montant_avances_ce_mois=Sum('montant_avance', filter=Q(
                statut='active',
                date_avance__year=mois_courant.year,
                date_avance__month=mois_courant.month
            ))
        )
        
        # Contrats avec avances (une seule requête)
        contrats_avec_avances = Contrat.objects.filter(
            avances_loyer__isnull=False
        ).distinct().count()
        
        # Avances récentes (limitées et optimisées)
        avances_recentes = AvanceLoyer.objects.select_related(
            'contrat__locataire',
            'contrat__propriete'
        ).order_by('-created_at')[:5]
        
        # Calculer les pourcentages
        total_avances = (stats['total_avances_actives'] or 0) + (stats['total_avances_epuisees'] or 0)
        pourcentage_actives = round(
            ((stats['total_avances_actives'] or 0) * 100) / total_avances, 1
        ) if total_avances > 0 else 0
        pourcentage_epuisees = round(
            ((stats['total_avances_epuisees'] or 0) * 100) / total_avances, 1
        ) if total_avances > 0 else 0
        
        return {
            'total_avances': total_avances,
            'montant_total_avances': stats['montant_total_avances'] or Decimal('0'),
            'avances_epuisees': stats['total_avances_epuisees'] or 0,
            'avances_actives': stats['total_avances_actives'] or 0,
            'pourcentage_actives': pourcentage_actives,
            'pourcentage_epuisees': pourcentage_epuisees,
            'avances_recentes': avances_recentes,
            'contrats_avec_avances': contrats_avec_avances,
            'avances_ce_mois': stats['avances_ce_mois'] or 0,
            'montant_avances_ce_mois': stats['montant_avances_ce_mois'] or Decimal('0'),
        }
    
    @staticmethod
    def get_historique_paiements_optimise(contrat_id: int, limit: int = 12):
        """
        Récupère l'historique des paiements d'un contrat de manière optimisée.
        
        Args:
            contrat_id: ID du contrat
            limit: Nombre maximum de paiements à récupérer
        
        Returns:
            Liste des paiements avec relations préchargées
        """
        from .models import Paiement
        
        return list(
            Paiement.objects.filter(
                contrat_id=contrat_id,
                is_deleted=False
            ).select_related(
                'contrat',
                'contrat__locataire',
                'contrat__propriete'
            ).order_by('-date_paiement')[:limit]
        )
