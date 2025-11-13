"""
Signaux pour mettre à jour dynamiquement les statistiques financières
lors de changements dans les paiements, contrats, etc.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.cache import cache
from .models import Paiement
from contrats.models import Contrat
from core.optimizations_dashboard import DashboardOptimizer


@receiver(post_save, sender=Paiement)
def invalider_cache_statistiques_apres_paiement(sender, instance, created, **kwargs):
    """
    Invalide le cache des statistiques financières après création/modification d'un paiement.
    CORRIGÉ : Met à jour dynamiquement les statistiques financières
    """
    try:
        with transaction.atomic():
            # Invalider le cache du dashboard pour tous les utilisateurs
            DashboardOptimizer.clear_cache()
            
            # Invalider aussi les caches spécifiques si on a le locataire/bailleur
            if instance.contrat:
                if instance.contrat.locataire:
                    # Invalider le cache des statistiques du locataire
                    cache_key_locataire = f"stats_locataire_{instance.contrat.locataire.pk}"
                    cache.delete(cache_key_locataire)
                
                if instance.contrat.propriete and instance.contrat.propriete.bailleur:
                    # Invalider le cache des statistiques du bailleur
                    cache_key_bailleur = f"stats_bailleur_{instance.contrat.propriete.bailleur.pk}"
                    cache.delete(cache_key_bailleur)
                    
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache après paiement: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_delete, sender=Paiement)
def invalider_cache_statistiques_apres_suppression_paiement(sender, instance, **kwargs):
    """
    Invalide le cache des statistiques financières après suppression d'un paiement.
    CORRIGÉ : Met à jour dynamiquement les statistiques financières
    """
    try:
        with transaction.atomic():
            # Invalider le cache du dashboard pour tous les utilisateurs
            DashboardOptimizer.clear_cache()
            
            # Invalider aussi les caches spécifiques si on a le locataire/bailleur
            if instance.contrat:
                if instance.contrat.locataire:
                    # Invalider le cache des statistiques du locataire
                    cache_key_locataire = f"stats_locataire_{instance.contrat.locataire.pk}"
                    cache.delete(cache_key_locataire)
                
                if instance.contrat.propriete and instance.contrat.propriete.bailleur:
                    # Invalider le cache des statistiques du bailleur
                    cache_key_bailleur = f"stats_bailleur_{instance.contrat.propriete.bailleur.pk}"
                    cache.delete(cache_key_bailleur)
                    
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache après suppression paiement: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=Contrat)
def invalider_cache_statistiques_apres_contrat(sender, instance, created, **kwargs):
    """
    Invalide le cache des statistiques financières après création/modification d'un contrat.
    CORRIGÉ : Met à jour dynamiquement les statistiques financières
    """
    try:
        with transaction.atomic():
            # Invalider le cache du dashboard pour tous les utilisateurs
            DashboardOptimizer.clear_cache()
            
            # Invalider aussi les caches spécifiques
            if instance.locataire:
                cache_key_locataire = f"stats_locataire_{instance.locataire.pk}"
                cache.delete(cache_key_locataire)
            
            if instance.propriete and instance.propriete.bailleur:
                cache_key_bailleur = f"stats_bailleur_{instance.propriete.bailleur.pk}"
                cache.delete(cache_key_bailleur)
                    
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache après contrat: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_delete, sender=Contrat)
def invalider_cache_statistiques_apres_suppression_contrat(sender, instance, **kwargs):
    """
    Invalide le cache des statistiques financières après suppression d'un contrat.
    CORRIGÉ : Met à jour dynamiquement les statistiques financières
    """
    try:
        with transaction.atomic():
            # Invalider le cache du dashboard pour tous les utilisateurs
            DashboardOptimizer.clear_cache()
            
            # Invalider aussi les caches spécifiques
            if instance.locataire:
                cache_key_locataire = f"stats_locataire_{instance.locataire.pk}"
                cache.delete(cache_key_locataire)
            
            if instance.propriete and instance.propriete.bailleur:
                cache_key_bailleur = f"stats_bailleur_{instance.propriete.bailleur.pk}"
                cache.delete(cache_key_bailleur)
                    
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache après suppression contrat: {str(e)}")
        import traceback
        traceback.print_exc()

