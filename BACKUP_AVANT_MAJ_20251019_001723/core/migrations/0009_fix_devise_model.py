# Generated manually to fix Devise model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_logaudit'),
    ]

    operations = [
        # Add missing fields to Devise model
        migrations.AddField(
            model_name='devise',
            name='date_creation',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='devise',
            name='date_modification',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='devise',
            name='taux_change',
            field=models.DecimalField(decimal_places=4, default=1.0, max_digits=10, verbose_name='Taux de change'),
        ),
        migrations.AddField(
            model_name='devise',
            name='par_defaut',
            field=models.BooleanField(default=False, verbose_name='Devise par défaut'),
        ),
    ]
