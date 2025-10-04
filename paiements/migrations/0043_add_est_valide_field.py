# Generated manually to fix missing est_valide field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0042_add_est_deductible_loyer_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargedeductible',
            name='est_valide',
            field=models.BooleanField(
                default=False,
                verbose_name='Validé'
            ),
        ),
        migrations.AddField(
            model_name='chargedeductible',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True
            ),
        ),
        migrations.AddField(
            model_name='chargedeductible',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True
            ),
        ),
    ]
