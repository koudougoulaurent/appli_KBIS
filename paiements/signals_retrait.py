from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import ChargeDeductible, ChargeBailleur
from .services_retrait import ServiceGestionRetrait


@receiver(post_save, sender=ChargeDeductible)
def mettre_a_jour_retrait_charge_deductible(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement les retraits quand une charge déductible est ajoutée/modifiée
    """
    if instance.statut == 'validee':
        # Mettre à jour les retraits pour le mois de la charge
        mois_charge = instance.date_charge.replace(day=1)
        ServiceGestionRetrait.mettre_a_jour_charges_immediatement(
            instance.contrat.propriete, 
            mois_charge
        )


@receiver(post_save, sender=ChargeBailleur)
def mettre_a_jour_retrait_charge_bailleur(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement les retraits quand une charge bailleur est ajoutée/modifiée
    LOGIQUE: Si retrait déjà validé → charge reportée au mois suivant
    """
    # Protection contre la récursion infinie
    if hasattr(instance, '_signal_processing'):
        return
    instance._signal_processing = True
    
    try:
        if instance.statut in ['en_attente', 'utilise']:
            # Mettre à jour les retraits pour le mois de la charge
            from datetime import date
            if isinstance(instance.date_charge, str):
                # Si c'est une chaîne, la convertir en date
                mois_charge = date.fromisoformat(instance.date_charge).replace(day=1)
            else:
                # Si c'est déjà un objet date
                mois_charge = instance.date_charge.replace(day=1)
            
            # Pour ChargeBailleur, on utilise le bailleur au lieu de la propriété
            from paiements.models import RetraitBailleur
            from django.db import transaction
            
            try:
                with transaction.atomic():
                    # Vérifier s'il existe un retrait VALIDÉ pour ce mois
                    retrait_valide = RetraitBailleur.objects.filter(
                        bailleur=instance.bailleur,
                        mois_retrait__year=mois_charge.year,
                        mois_retrait__month=mois_charge.month,
                        statut__in=['valide', 'paye']  # Retrait déjà validé ou payé
                    ).first()
                    
                    if retrait_valide:
                        # LOGIQUE: Si retrait déjà validé → charge reportée au mois suivant
                        mois_suivant = mois_charge + relativedelta(months=1)
                        
                        # Mettre à jour le mois_charge de la charge pour le mois suivant
                        # Utiliser update_fields pour éviter de déclencher le signal
                        ChargeBailleur.objects.filter(id=instance.id).update(mois_charge=mois_suivant)
                        
                        # Log de l'action
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Charge {instance.numero_charge} reportée au mois suivant car retrait déjà validé pour {mois_charge.strftime('%B %Y')}")
                        
                    else:
                        # Retrait pas encore validé → mettre à jour normalement
                        retraits_a_mettre_a_jour = RetraitBailleur.objects.filter(
                            bailleur=instance.bailleur,
                            mois_retrait__year=mois_charge.year,
                            mois_retrait__month=mois_charge.month,
                            statut='en_attente'
                        )
                        
                        for retrait in retraits_a_mettre_a_jour:
                            # Recalculer le retrait
                            calcul = ServiceGestionRetrait.calculer_retrait_optimise(retrait.bailleur, retrait.mois_retrait)
                            
                            if calcul['success']:
                                # Mettre à jour les montants
                                retrait.montant_loyers_bruts = calcul['montant_loyers_bruts']
                                retrait.montant_charges_deductibles = calcul['montant_charges_deductibles']
                                retrait.montant_charges_bailleur = calcul['montant_charges_bailleur']
                                retrait.montant_net_a_payer = calcul['montant_net_total']
                                retrait.save()
                                
            except Exception as e:
                # Log l'erreur mais ne pas faire échouer la sauvegarde
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la mise à jour des retraits après ajout/modification de charge: {e}")
    finally:
        # Nettoyer le flag de protection
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


@receiver(post_delete, sender=ChargeDeductible)
def mettre_a_jour_retrait_suppression_charge_deductible(sender, instance, **kwargs):
    """
    Met à jour automatiquement les retraits quand une charge déductible est supprimée
    """
    mois_charge = instance.date_charge.replace(day=1)
    ServiceGestionRetrait.mettre_a_jour_charges_immediatement(
        instance.contrat.propriete, 
        mois_charge
    )


@receiver(post_delete, sender=ChargeBailleur)
def mettre_a_jour_retrait_suppression_charge_bailleur(sender, instance, **kwargs):
    """
    Met à jour automatiquement les retraits quand une charge bailleur est supprimée
    LOGIQUE: Si retrait déjà validé → pas de mise à jour nécessaire
    """
    from datetime import date
    if isinstance(instance.date_charge, str):
        # Si c'est une chaîne, la convertir en date
        mois_charge = date.fromisoformat(instance.date_charge).replace(day=1)
    else:
        # Si c'est déjà un objet date
        mois_charge = instance.date_charge.replace(day=1)
    
    # Pour ChargeBailleur, on utilise le bailleur au lieu de la propriété
    # Mettre à jour tous les retraits du bailleur pour ce mois
    from paiements.models import RetraitBailleur
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Vérifier s'il existe un retrait VALIDÉ pour ce mois
            retrait_valide = RetraitBailleur.objects.filter(
                bailleur=instance.bailleur,
                mois_retrait__year=mois_charge.year,
                mois_retrait__month=mois_charge.month,
                statut__in=['valide', 'paye']  # Retrait déjà validé ou payé
            ).first()
            
            if retrait_valide:
                # LOGIQUE: Si retrait déjà validé → pas de mise à jour nécessaire
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Suppression de charge {instance.numero_charge} ignorée car retrait déjà validé pour {mois_charge.strftime('%B %Y')}")
                return
            
            # Retrait pas encore validé → mettre à jour normalement
            retraits_a_mettre_a_jour = RetraitBailleur.objects.filter(
                bailleur=instance.bailleur,
                mois_retrait__year=mois_charge.year,
                mois_retrait__month=mois_charge.month,
                statut='en_attente'
            )
            
            for retrait in retraits_a_mettre_a_jour:
                # Recalculer le retrait
                calcul = ServiceGestionRetrait.calculer_retrait_optimise(retrait.bailleur, retrait.mois_retrait)
                
                if calcul['success']:
                    # Mettre à jour les montants
                    retrait.montant_loyers_bruts = calcul['montant_loyers_bruts']
                    retrait.montant_charges_deductibles = calcul['montant_charges_deductibles']
                    retrait.montant_charges_bailleur = calcul['montant_charges_bailleur']
                    retrait.montant_net_a_payer = calcul['montant_net_total']
                    retrait.save()
    except Exception as e:
        # Log l'erreur mais ne pas faire échouer la suppression
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la mise à jour des retraits après suppression de charge: {e}")
