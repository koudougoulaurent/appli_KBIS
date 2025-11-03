# Migration pour mettre à jour les retraits existants avec commission agence et montant réellement payé
from django.db import migrations
from decimal import Decimal


def update_existing_retraits(apps, schema_editor):  # noqa: ARG001
    """
    Met à jour tous les retraits existants pour calculer:
    - commission_agence = 10% du montant_net_a_payer
    - montant_reellement_paye = montant_net_a_payer - commission_agence - montant_charges_bailleur
    """
    RetraitBailleur = apps.get_model('paiements', 'RetraitBailleur')
    
    retraits = RetraitBailleur.objects.all()
    updated_count = 0
    
    for retrait in retraits:
        # Calculer la commission agence (10% du montant net à payer)
        commission_agence = retrait.montant_net_a_payer * Decimal('0.10')
        
        # Calculer le montant réellement payé
        # montant_net_a_payer contient déjà: loyers_bruts - charges_deductibles - charges_bailleur
        # Donc montant_reellement_paye = montant_net_a_payer - commission_agence - charges_bailleur
        montant_reellement_paye = retrait.montant_net_a_payer - commission_agence - retrait.montant_charges_bailleur
        
        # S'assurer que le montant n'est pas négatif
        if montant_reellement_paye < 0:
            montant_reellement_paye = Decimal('0')
        
        retrait.commission_agence = commission_agence
        retrait.montant_reellement_paye = montant_reellement_paye
        retrait.save(update_fields=['commission_agence', 'montant_reellement_paye'])
        updated_count += 1
    
    print(f"\n✅ {updated_count} retrait(s) mis à jour avec commission agence et montant réellement payé.")


def reverse_update_existing_retraits(apps, schema_editor):  # noqa: ARG001
    """
    Remet les valeurs à zéro en cas de rollback
    """
    RetraitBailleur = apps.get_model('paiements', 'RetraitBailleur')
    
    RetraitBailleur.objects.all().update(
        commission_agence=Decimal('0'),
        montant_reellement_paye=Decimal('0')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0023_add_commission_agence_retrait'),
    ]

    operations = [
        migrations.RunPython(
            update_existing_retraits,
            reverse_update_existing_retraits,
        ),
    ]

