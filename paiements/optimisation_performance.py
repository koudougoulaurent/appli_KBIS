"""
Optimisations de Performance pour le Module Paiements
=====================================================

Ce fichier contient les optimisations pour améliorer les performances
en production, notamment pour les avances de loyer.
"""
from django.db import models, connection
from django.core.cache import cache
from functools import wraps
import hashlib
import json


def cache_requete(timeout=300):
    """
    Décorateur pour mettre en cache le résultat d'une requête.
    
    Args:
        timeout: Durée du cache en secondes (par défaut 5 minutes)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Créer une clé de cache unique basée sur la fonction et les arguments
            cache_key = f"cache_{func.__name__}_{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Vérifier le cache
            resultat = cache.get(cache_key)
            if resultat is not None:
                return resultat
            
            # Exécuter la fonction
            resultat = func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(cache_key, resultat, timeout)
            
            return resultat
        return wrapper
    return decorator


def optimiser_requetes_avances():
    """
    Optimise les requêtes sur les avances de loyer en ajoutant des index.
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Index sur les champs fréquemment utilisés
        optimisations = [
            # Index pour filtrer par contrat
            "CREATE INDEX IF NOT EXISTS idx_avanceloyer_contrat ON paiements_avanceloyer(contrat_id) WHERE is_deleted = FALSE;",
            
            # Index pour filtrer par statut
            "CREATE INDEX IF NOT EXISTS idx_avanceloyer_statut ON paiements_avanceloyer(statut) WHERE is_deleted = FALSE;",
            
            # Index composite pour les requêtes fréquentes
            "CREATE INDEX IF NOT EXISTS idx_avanceloyer_contrat_statut ON paiements_avanceloyer(contrat_id, statut) WHERE is_deleted = FALSE;",
            
            # Index pour les dates de couverture
            "CREATE INDEX IF NOT EXISTS idx_avanceloyer_dates ON paiements_avanceloyer(mois_debut_couverture, mois_fin_couverture);",
            
            # Index pour les paiements
            "CREATE INDEX IF NOT EXISTS idx_paiement_contrat_type ON paiements_paiement(contrat_id, type_paiement, statut) WHERE is_deleted = FALSE;",
            
            # Index pour mois_paye
            "CREATE INDEX IF NOT EXISTS idx_paiement_mois_paye ON paiements_paiement(mois_paye) WHERE mois_paye IS NOT NULL;",
        ]
        
        for sql in optimisations:
            try:
                cursor.execute(sql)
                print(f"✓ {sql}")
            except Exception as e:
                print(f"⚠️  Erreur: {e}")


class OptimisateurRequetesAvances:
    """
    Classe pour optimiser les requêtes sur les avances de loyer.
    """
    
    @staticmethod
    def get_avances_actives_contrat(contrat):
        """
        Récupère les avances actives d'un contrat avec préchargement des relations.
        
        Optimisations :
        - select_related pour éviter N+1
        - Filtrage optimal
        - Mise en cache
        """
        cache_key = f"avances_actives_contrat_{contrat.id}"
        avances = cache.get(cache_key)
        
        if avances is None:
            from paiements.models_avance import AvanceLoyer
            
            avances = list(
                AvanceLoyer.objects.filter(
                    contrat=contrat,
                    statut='active',
                    montant_restant__gt=0
                ).select_related('contrat', 'contrat__locataire', 'contrat__propriete')
            )
            
            # Cache de 2 minutes (court car les avances changent souvent)
            cache.set(cache_key, avances, 120)
        
        return avances
    
    @staticmethod
    def get_derniers_paiements_contrat(contrat, limit=10):
        """
        Récupère les derniers paiements d'un contrat avec préchargement.
        
        Optimisations :
        - Limite du nombre de résultats
        - Préchargement des relations
        - Ordre optimisé
        """
        from paiements.models import Paiement
        
        return Paiement.objects.filter(
            contrat=contrat,
            is_deleted=False
        ).select_related(
            'contrat',
            'contrat__locataire',
            'contrat__propriete'
        ).order_by('-date_paiement')[:limit]
    
    @staticmethod
    @cache_requete(timeout=300)  # 5 minutes
    def calculer_stats_avances_contrat(contrat_id):
        """
        Calcule les statistiques d'avances pour un contrat (avec cache).
        
        Args:
            contrat_id: ID du contrat
        
        Returns:
            dict: Statistiques (montant total, mois couverts, etc.)
        """
        from paiements.models_avance import AvanceLoyer
        from django.db.models import Sum, Count
        
        stats = AvanceLoyer.objects.filter(
            contrat_id=contrat_id,
            statut='active'
        ).aggregate(
            montant_total=Sum('montant_restant'),
            nombre_avances=Count('id'),
            mois_couverts_total=Sum('nombre_mois_couverts')
        )
        
        return {
            'montant_total': stats['montant_total'] or 0,
            'nombre_avances': stats['nombre_avances'] or 0,
            'mois_couverts_total': stats['mois_couverts_total'] or 0
        }
    
    @staticmethod
    def invalider_cache_contrat(contrat_id):
        """
        Invalide le cache pour un contrat spécifique.
        
        À appeler après modification d'un paiement ou d'une avance.
        """
        cache.delete(f"avances_actives_contrat_{contrat_id}")
        
        # Invalider aussi les stats
        cache_pattern = f"cache_calculer_stats_avances_contrat_*{contrat_id}*"
        # Note: Pour invalider les patterns, utiliser cache.delete_pattern si Redis
        # Sinon, stocker les clés dans une liste


def analyser_performances_requetes():
    """
    Analyse les requêtes lentes dans le log Django.
    
    À exécuter en mode DEBUG pour identifier les requêtes problématiques.
    """
    from django.db import connection
    
    print(f"\n{'='*80}")
    print("ANALYSE DES PERFORMANCES")
    print(f"{'='*80}\n")
    
    print(f"Nombre total de requêtes: {len(connection.queries)}")
    
    # Trier par temps d'exécution
    queries_triees = sorted(
        connection.queries,
        key=lambda q: float(q['time']),
        reverse=True
    )
    
    print(f"\n10 REQUÊTES LES PLUS LENTES:")
    print(f"{'-'*80}")
    
    for i, query in enumerate(queries_triees[:10], 1):
        print(f"\n{i}. Temps: {query['time']}s")
        print(f"   SQL: {query['sql'][:200]}...")
    
    # Détecter les requêtes N+1
    sql_counts = {}
    for query in connection.queries:
        sql_pattern = query['sql'][:100]  # Premiers 100 caractères
        sql_counts[sql_pattern] = sql_counts.get(sql_pattern, 0) + 1
    
    print(f"\n\nREQUÊTES RÉPÉTÉES (potentiels N+1):")
    print(f"{'-'*80}")
    
    for sql, count in sorted(sql_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        if count > 5:  # Seuil arbitraire
            print(f"\n{count}x : {sql}...")
    
    print(f"\n{'='*80}\n")


# Fonction utilitaire pour logger les requêtes lentes
class LoggerRequetesLentes:
    """
    Context manager pour logger les requêtes lentes.
    
    Usage:
        with LoggerRequetesLentes(seuil=0.1):
            # Code à analyser
            avances = AvanceLoyer.objects.filter(...)
    """
    
    def __init__(self, seuil=0.1):
        """
        Args:
            seuil: Temps minimum en secondes pour logger (défaut: 0.1s)
        """
        self.seuil = seuil
        self.nb_queries_debut = 0
    
    def __enter__(self):
        self.nb_queries_debut = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        nouvelles_queries = connection.queries[self.nb_queries_debut:]
        
        requetes_lentes = [
            q for q in nouvelles_queries
            if float(q['time']) >= self.seuil
        ]
        
        if requetes_lentes:
            print(f"\n⚠️  {len(requetes_lentes)} requête(s) lente(s) détectée(s):")
            for q in requetes_lentes:
                print(f"  - {q['time']}s : {q['sql'][:150]}...")
