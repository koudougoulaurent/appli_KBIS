from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
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
    """
    if instance.statut in ['en_attente', 'deduite_retrait']:
        # Mettre à jour les retraits pour le mois de la charge
        mois_charge = instance.date_charge.replace(day=1)
        ServiceGestionRetrait.mettre_a_jour_charges_immediatement(
            instance.propriete, 
            mois_charge
        )


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
    """
    mois_charge = instance.date_charge.replace(day=1)
    ServiceGestionRetrait.mettre_a_jour_charges_immediatement(
        instance.propriete, 
        mois_charge
    )
