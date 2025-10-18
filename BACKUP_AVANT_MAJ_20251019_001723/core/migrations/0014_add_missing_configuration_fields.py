# Generated manually to add missing fields to ConfigurationTableauBord

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_add_security_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurationtableaubord',
            name='ordre_widgets',
            field=models.JSONField(default=list, verbose_name='Ordre des widgets'),
        ),
        migrations.AddField(
            model_name='configurationtableaubord',
            name='configuration_widgets',
            field=models.JSONField(default=dict, verbose_name='Configuration des widgets'),
        ),
        migrations.AddField(
            model_name='configurationtableaubord',
            name='affichage_anonymise',
            field=models.BooleanField(default=False, verbose_name='Affichage anonymisé'),
        ),
        migrations.AddField(
            model_name='configurationtableaubord',
            name='limite_donnees_recentes',
            field=models.PositiveIntegerField(default=30, verbose_name='Limiter aux données récentes (jours)'),
        ),
    ]
