# Generated manually for adding montant_reste field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0016_fix_existing_receipts_amounts'),
    ]

    operations = [
        migrations.AddField(
            model_name='avanceloyer',
            name='montant_reste',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Montant qui reste après la division par le loyer mensuel',
                max_digits=12,
                verbose_name='Montant restant après division'
            ),
        ),
    ]
