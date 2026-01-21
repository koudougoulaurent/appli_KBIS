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
    ÉVITE LA RÉCURSION : Ne traite pas si on est déjà en synchronisation
    """
    try:
        # ÉVITER LA RÉCURSION : Ne pas traiter si on est déjà en train de synchroniser
        if hasattr(instance, '_en_synchronisation') or hasattr(instance, '_en_verification_completion'):
            return
        
        with transaction.atomic():
            # Invalider le cache du dashboard pour tous les utilisateurs
            DashboardOptimizer.clear_cache()
            
            # Invalider aussi les caches spécifiques si on a le locataire/bailleur
            # Utiliser getattr pour éviter les erreurs si contrat n'est pas chargé
            contrat_id = getattr(instance, 'contrat_id', None)
            if contrat_id:
                try:
                    from contrats.models import Contrat
                    contrat = Contrat.objects.select_related('locataire', 'propriete', 'propriete__bailleur').get(pk=contrat_id)
                    
                    if contrat.locataire:
                        # Invalider le cache des statistiques du locataire
                        cache_key_locataire = f"stats_locataire_{contrat.locataire.pk}"
                        cache.delete(cache_key_locataire)
                    
                    if contrat.propriete and contrat.propriete.bailleur:
                        # Invalider le cache des statistiques du bailleur
                        cache_key_bailleur = f"stats_bailleur_{contrat.propriete.bailleur.pk}"
                        cache.delete(cache_key_bailleur)
                except Exception:
                    # Si erreur, continuer sans invalider les caches spécifiques
                    pass
            
            # Invalider le cache des paiements partiels
            cache.delete('contrats_avec_paiements_partiels')
            cache.delete('statistiques_paiements_partiels')
                    
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
            
            # Invalider le cache des paiements partiels
            cache.delete('contrats_avec_paiements_partiels')
            cache.delete('statistiques_paiements_partiels')
                    
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache après suppression paiement: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=Contrat)
def invalider_cache_statistiques_apres_contrat(sender, instance, created, **kwargs):
    """
    Invalide le cache des statistiques financières après création/modification d'un contrat.
    CORRIGÉ : Met à jour dynamiquement les statistiques financières
    OPTIMISÉ : Skip si update partiel non significatif (ex: sync avances)
    """
    try:
        # OPTIMISATION CRITIQUE : Vérifier si l'update concerne des champs significatifs
        update_fields = kwargs.get('update_fields')
        
        # Si c'est un update partiel, vérifier s'il concerne des champs qui impactent les stats
        if update_fields is not None:
            # Champs non significatifs (ne nécessitent pas d'invalidation de cache)
            champs_non_significatifs = {
                'avance_loyer', 
                'avance_loyer_payee', 
                'date_paiement_avance',
                'caution_payee',
                'date_paiement_caution',
            }
            
            # Si TOUS les champs modifiés sont non significatifs, skip l'invalidation
            if set(update_fields).issubset(champs_non_significatifs):
                return  # ← SKIP (optimisation)
        
        # Si on arrive ici : c'est une création OU un update significatif
        with transaction.atomic():
            # Invalider le cache du dashboard pour tous les utilisateurs
            DashboardOptimizer.clear_cache()
            
            # Invalider aussi les caches spécifiques
            # OPTIMISATION : Utiliser getattr pour éviter requêtes DB si déjà chargé
            if hasattr(instance, 'locataire') and instance.locataire:
                cache_key_locataire = f"stats_locataire_{instance.locataire.pk}"
                cache.delete(cache_key_locataire)
            
            # OPTIMISATION : Éviter l'accès à propriete.bailleur si possible
            if hasattr(instance, 'propriete_id') and instance.propriete_id:
                # Utiliser select_related si nécessaire ou accéder directement à l'ID
                try:
                    if hasattr(instance, '_propriete_cache'):
                        # Si propriete est déjà en cache (from select_related)
                        bailleur = instance.propriete.bailleur if instance.propriete else None
                    else:
                        # Récupérer juste pour le cache (inevitable ici)
                        bailleur = instance.propriete.bailleur if instance.propriete else None
                    
                    if bailleur:
                        cache_key_bailleur = f"stats_bailleur_{bailleur.pk}"
                        cache.delete(cache_key_bailleur)
                except Exception:
                    pass  # Si erreur d'accès, on skip juste cette partie
            
            # Invalider le cache des paiements partiels
            cache.delete('contrats_avec_paiements_partiels')
            cache.delete('statistiques_paiements_partiels')
                    
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
            
            # Invalider le cache des paiements partiels
            cache.delete('contrats_avec_paiements_partiels')
            cache.delete('statistiques_paiements_partiels')
                    
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache après suppression contrat: {str(e)}")
        import traceback
        traceback.print_exc()
















