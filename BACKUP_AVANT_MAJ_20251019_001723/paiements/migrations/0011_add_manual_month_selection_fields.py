# Generated manually for manual month selection fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0050_add_mois_effet_personnalise'),
    ]

    operations = [
        migrations.AddField(
            model_name='avanceloyer',
            name='mois_couverts_manuels',
            field=models.JSONField(blank=True, default=list, help_text='Liste des mois sélectionnés manuellement pour cette avance', verbose_name='Mois couverts sélectionnés manuellement'),
        ),
        migrations.AddField(
            model_name='avanceloyer',
            name='mode_selection_mois',
            field=models.CharField(choices=[('automatique', 'Calcul automatique'), ('manuel', 'Sélection manuelle')], default='automatique', help_text='Choisissez comment déterminer les mois couverts par cette avance', max_length=20, verbose_name='Mode de sélection des mois'),
        ),
    ]
