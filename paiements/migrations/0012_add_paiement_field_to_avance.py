# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0011_add_manual_month_selection_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='avanceloyer',
            name='paiement',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='avance_loyer',
                to='paiements.paiement',
                verbose_name='Paiement associé'
            ),
        ),
    ]
