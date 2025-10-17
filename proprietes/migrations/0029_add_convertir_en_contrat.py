# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0028_add_motif_deduction_to_charges_bailleur'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservationunite',
            name='convertir_en_contrat',
            field=models.BooleanField(default=False, help_text='Cocher pour convertir immédiatement cette réservation en contrat de bail', verbose_name='Convertir en contrat'),
        ),
    ]


