# Generated manually for the recap_lie field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='retraitbailleur',
            name='recap_lie',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.SET_NULL, 
                related_name='retraits_lies', 
                to='paiements.recapmensuel',
                verbose_name='Récapitulatif lié',
                help_text='Récapitulatif mensuel à l\'origine de ce retrait'
            ),
        ),
    ]
