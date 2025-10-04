# Generated manually to fix missing created_at and updated_at fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0043_add_est_valide_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargedeductible',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True
            ),
        ),
        migrations.AddField(
            model_name='chargedeductible',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True
            ),
        ),
    ]
