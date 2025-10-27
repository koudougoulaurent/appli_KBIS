# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0034_add_resiliation_work_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resiliationcontrat',
            name='motif_resiliation',
            field=models.TextField(blank=True, null=True, verbose_name='Motif de résiliation'),
        ),
    ]

