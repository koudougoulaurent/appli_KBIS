# Generated manually to fix missing motif_deduction column

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0027_alter_locataire_civilite_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargesbailleur',
            name='motif_deduction',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name='Motif de la déduction',
                help_text='Raison de la déduction du retrait mensuel'
            ),
        ),
        migrations.AddField(
            model_name='chargesbailleur',
            name='notes_deduction',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Notes de déduction',
                help_text='Commentaires sur la déduction'
            ),
        ),
    ]
