# Generated manually to fix telephone field length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0029_add_convertir_en_contrat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bailleur',
            name='telephone',
            field=models.CharField(max_length=30, verbose_name='Téléphone'),
        ),
        migrations.AlterField(
            model_name='bailleur',
            name='telephone_mobile',
            field=models.CharField(blank=True, max_length=30, verbose_name='Mobile'),
        ),
        migrations.AlterField(
            model_name='locataire',
            name='telephone',
            field=models.CharField(max_length=30, verbose_name='Téléphone'),
        ),
        migrations.AlterField(
            model_name='locataire',
            name='telephone_mobile',
            field=models.CharField(blank=True, max_length=30, verbose_name='Mobile'),
        ),
        migrations.AlterField(
            model_name='locataire',
            name='garant_telephone',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Téléphone du garant'),
        ),
    ]
