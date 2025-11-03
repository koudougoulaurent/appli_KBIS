# Generated manually for commission agence feature
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0022_alter_recap_bailleur_set_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='retraitbailleur',
            name='commission_agence',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Commission agence (10%)',
                help_text="Commission de l'agence de gestion immobilière (10% du montant net)"
            ),
        ),
        migrations.AddField(
            model_name='retraitbailleur',
            name='montant_reellement_paye',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Montant réellement payé',
                help_text='Montant net - Commission agence - Charges bailleur'
            ),
        ),
    ]

