# Generated manually for type_gestion field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0021_alter_propriete_charges_locataire'),
    ]

    operations = [
        migrations.AddField(
            model_name='propriete',
            name='type_gestion',
            field=models.CharField(
                choices=[
                    ('propriete_entiere', 'Propriété entière (louable en une seule fois)'),
                    ('unites_multiples', 'Propriété avec unités locatives multiples'),
                ],
                default='propriete_entiere',
                help_text='Définit si la propriété est louable entièrement ou par unités multiples',
                max_length=20,
                verbose_name='Type de gestion'
            ),
        ),
    ]
