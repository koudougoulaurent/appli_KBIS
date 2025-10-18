# Generated manually to fix missing column error

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0030_change_mois_paye_to_charfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='recapmensuel',
            name='total_charges_bailleur',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, null=True, blank=True, verbose_name='Total des charges bailleur'),
        ),
    ]
