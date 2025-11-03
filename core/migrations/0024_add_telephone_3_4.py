# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_add_auto_number_sequence'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurationentreprise',
            name='telephone_3',
            field=models.CharField(blank=True, max_length=20, verbose_name='Téléphone 3'),
        ),
        migrations.AddField(
            model_name='configurationentreprise',
            name='telephone_4',
            field=models.CharField(blank=True, max_length=20, verbose_name='Téléphone 4'),
        ),
    ]

