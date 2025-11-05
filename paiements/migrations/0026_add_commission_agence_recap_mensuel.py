# Generated manually for commission agence feature in RecapMensuel

from django.db import migrations, models
from decimal import Decimal


def calculer_commission_recaps_existants(apps, schema_editor):
    """Calcule la commission agence et le montant réellement payé pour les récapitulatifs existants."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    
    recaps = RecapMensuel.objects.all()
    updated_count = 0
    
    for recap in recaps:
        # Calculer la commission agence (10% du montant net à payer)
        commission_agence = recap.total_net_a_payer * Decimal('0.10')
        
        # Calculer le montant réellement payé
        montant_reellement_paye = recap.total_net_a_payer - commission_agence
        if montant_reellement_paye < 0:
            montant_reellement_paye = Decimal('0')
        
        recap.commission_agence = commission_agence
        recap.montant_reellement_paye = montant_reellement_paye
        recap.save(update_fields=['commission_agence', 'montant_reellement_paye'])
        updated_count += 1
    
    print(f"\n✅ {updated_count} récapitulatif(s) mensuel(s) mis à jour avec commission agence et montant réellement payé.")


def reverse_calculer_commission_recaps_existants(apps, schema_editor):
    """Fonction de rollback - remet les valeurs à 0."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    RecapMensuel.objects.all().update(
        commission_agence=Decimal('0'),
        montant_reellement_paye=Decimal('0')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0025_rendre_bailleur_obligatoire_recap'),
    ]

    operations = [
        migrations.AddField(
            model_name='recapmensuel',
            name='commission_agence',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Commission agence (10%)',
                help_text='Commission de l\'agence de gestion immobilière (10% du montant net)'
            ),
        ),
        migrations.AddField(
            model_name='recapmensuel',
            name='montant_reellement_paye',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Montant réellement payé',
                help_text='Montant net - Commission agence'
            ),
        ),
        migrations.RunPython(
            calculer_commission_recaps_existants,
            reverse_calculer_commission_recaps_existants
        ),
    ]

