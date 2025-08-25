# Generated manually for adding garant fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='locataire',
            name='garant_civilite',
            field=models.CharField(blank=True, choices=[('M', 'Monsieur'), ('Mme', 'Madame'), ('Mlle', 'Mademoiselle')], max_length=5, null=True, verbose_name='Civilité du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_nom',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Nom du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_prenom',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Prénom du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_telephone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Téléphone du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_profession',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Profession du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_employeur',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Employeur du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_revenus_mensuels',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Revenus mensuels du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_adresse',
            field=models.TextField(blank=True, null=True, verbose_name='Adresse du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_code_postal',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Code postal du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_ville',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Ville du garant'),
        ),
        migrations.AddField(
            model_name='locataire',
            name='garant_pays',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Pays du garant'),
        ),
    ]
