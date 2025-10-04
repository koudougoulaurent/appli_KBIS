# Generated manually to fix missing est_deductible_loyer field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0041_add_reference_paiement_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargedeductible',
            name='est_deductible_loyer',
            field=models.BooleanField(
                default=True,
                verbose_name='Déductible du loyer'
            ),
        ),
        migrations.AddField(
            model_name='chargedeductible',
            name='est_valide',
            field=models.BooleanField(
                default=False,
                verbose_name='Validé'
            ),
        ),
    ]
