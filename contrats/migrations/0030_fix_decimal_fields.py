# Generated manually to fix decimal fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0029_add_convertir_en_contrat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contrat',
            name='loyer_mensuel',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Loyer mensuel'),
        ),
        migrations.AlterField(
            model_name='contrat',
            name='depot_garantie',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Dépôt de garantie ou Caution'),
        ),
        migrations.AlterField(
            model_name='contrat',
            name='avance_loyer',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Avance de loyer'),
        ),
    ]
