"""
Signaux pour gérer automatiquement la complétion des paiements partiels
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Paiement
from .services_paiement_partiel import ServicePaiementPartiel
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Paiement)
def verifier_completion_automatique(sender, instance, created, **kwargs):
    """
    Signal qui vérifie automatiquement si un paiement partiel complète le reliquat
    après chaque sauvegarde de paiement.
    
    Ce signal se déclenche à CHAQUE sauvegarde de paiement (création ou modification)
    et vérifie dynamiquement si le paiement complète un reliquat existant.
    """
    # Éviter la récursion infinie
    if hasattr(instance, '_skip_signal_completion'):
        return
    
    # Seulement pour les paiements de type loyer ou paiement_partiel
    if instance.type_paiement not in ['loyer', 'paiement_partiel']:
        return
    
    # Seulement si le paiement est validé
    if instance.statut != 'valide':
        return
    
    # Vérifier si le paiement a un mois_paye défini
    if not instance.mois_paye:
        return
    
    # Vérifier si le paiement a un contrat
    if not instance.contrat:
        return
    
    try:
        # Marquer pour éviter la récursion
        instance._skip_signal_completion = True
        
        # Vérifier et compléter automatiquement le reliquat
        # Cette méthode est DYNAMIQUE et recalcule en temps réel
        completion_effectuee = ServicePaiementPartiel.verifier_et_completer_reliquat(
            paiement=instance,
            skip_save=True  # On utilise update() dans le service pour éviter la récursion
        )
        
        if completion_effectuee:
            logger.info(
                f"✅ SIGNAL: Reliquat complété automatiquement pour "
                f"{instance.contrat.numero_contrat} - {instance.mois_paye}"
            )
        else:
            logger.debug(
                f"📊 SIGNAL: Montants restants mis à jour pour "
                f"{instance.contrat.numero_contrat} - {instance.mois_paye}"
            )
    except Exception as e:
        logger.error(f"❌ Erreur signal complétion automatique: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Nettoyer le flag
        if hasattr(instance, '_skip_signal_completion'):
            delattr(instance, '_skip_signal_completion')


@receiver(post_save, sender=Paiement)
def synchroniser_paiement_partiel_automatique(sender, instance, created, **kwargs):
    """
    Signal qui synchronise automatiquement les paiements partiels
    après chaque création ou modification.
    """
    # Éviter la récursion infinie
    if hasattr(instance, '_skip_signal_sync'):
        return
    
    # Seulement pour les nouveaux paiements de type loyer
    if not created or instance.type_paiement not in ['loyer', 'paiement_partiel']:
        return
    
    # Seulement si le paiement est validé
    if instance.statut != 'valide':
        return
    
    try:
        # Marquer pour éviter la récursion
        instance._skip_signal_sync = True
        
        # Synchroniser le paiement partiel
        est_partiel = ServicePaiementPartiel.synchroniser_paiement_partiel(instance)
        
        if est_partiel:
            logger.info(
                f"📊 SIGNAL: Paiement partiel synchronisé pour "
                f"{instance.contrat.numero_contrat} - {instance.mois_paye}"
            )
    except Exception as e:
        logger.error(f"❌ Erreur signal synchronisation partielle: {str(e)}")
    finally:
        # Nettoyer le flag
        if hasattr(instance, '_skip_signal_sync'):
            delattr(instance, '_skip_signal_sync')
