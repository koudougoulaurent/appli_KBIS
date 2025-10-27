# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0033_alter_contratkbis_paiement_debut_mois'),
    ]

    operations = [
        migrations.AddField(
            model_name='resiliationcontrat',
            name='travaux_peinture',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Travaux de peinture (F CFA)'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='facture_onea',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Facture ONEA (F CFA)'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='facture_sonabel',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Facture SONABEL (F CFA)'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='travaux_ventilateur',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Ventilateur (F CFA)'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='autres_depenses',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Autres dépenses (F CFA)'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='description_autres_depenses',
            field=models.TextField(blank=True, verbose_name='Description des autres dépenses'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='total_depenses',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Total des dépenses'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='caution_versee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Caution versée lors du contrat'),
        ),
        migrations.AddField(
            model_name='resiliationcontrat',
            name='solde_restant',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Solde restant (caution - dépenses)'),
        ),
    ]

