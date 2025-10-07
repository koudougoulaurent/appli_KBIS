# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0048_merge_20251007_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consommationavance',
            name='paiement',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name='consommations_avance',
                to='paiements.paiement',
                verbose_name='Paiement'
            ),
        ),
    ]
