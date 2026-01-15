# Migration pour corriger le stockage du champ garant_piece_identite
# Ce champ utilise maintenant FileSystemStorage au lieu de db_file_storage
# pour éviter les erreurs de format de nom

from django.db import migrations, models
from django.core.files.storage import FileSystemStorage


# Stockage local pour les pièces d'identité des garants
garant_storage = FileSystemStorage(location='media_local/garants')


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0038_contratgestion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locataire',
            name='garant_piece_identite',
            field=models.FileField(
                blank=True,
                null=True,
                storage=garant_storage,
                upload_to='garants/pieces_identite/',
                verbose_name="Pièce d'identité du garant"
            ),
        ),
    ]
