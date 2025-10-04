# Generated manually to add created_at and updated_at fields to Paiement model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0034_merge_20251004_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiement',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='paiement',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
