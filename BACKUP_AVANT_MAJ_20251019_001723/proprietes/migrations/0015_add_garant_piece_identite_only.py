# Generated manually for adding only garant_piece_identite field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0014_merge_20250825_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='locataire',
            name='garant_piece_identite',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='garants/pieces_identite/',
                verbose_name='Pièce d\'identité du garant'
            ),
        ),
    ]
