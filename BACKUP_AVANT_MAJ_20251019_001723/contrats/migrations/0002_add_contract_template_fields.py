# Generated manually for contract template fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrat',
            name='garant_nom',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nom du garant'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='garant_profession',
            field=models.CharField(blank=True, max_length=100, verbose_name='Profession du garant'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='garant_adresse',
            field=models.CharField(blank=True, max_length=200, verbose_name='Adresse du garant'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='garant_telephone',
            field=models.CharField(blank=True, max_length=20, verbose_name='Téléphone du garant'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='garant_cnib',
            field=models.CharField(blank=True, max_length=20, verbose_name='Numéro CNIB du garant'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='numero_maison',
            field=models.CharField(blank=True, max_length=20, verbose_name='Numéro de la maison'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='secteur',
            field=models.CharField(blank=True, max_length=100, verbose_name='Secteur de la propriété'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='loyer_mensuel_texte',
            field=models.CharField(blank=True, max_length=100, verbose_name='Loyer mensuel en lettres'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='loyer_mensuel_numerique',
            field=models.CharField(blank=True, max_length=20, verbose_name='Loyer mensuel en chiffres'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='depot_garantie_texte',
            field=models.CharField(blank=True, max_length=100, verbose_name='Dépôt de garantie en lettres'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='depot_garantie_numerique',
            field=models.CharField(blank=True, max_length=20, verbose_name='Dépôt de garantie en chiffres'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='nombre_mois_caution',
            field=models.CharField(blank=True, max_length=50, verbose_name='Nombre de mois de caution'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='montant_garantie_max',
            field=models.CharField(blank=True, max_length=20, verbose_name='Montant maximum de garantie'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='montant_garantie_max_texte',
            field=models.CharField(blank=True, max_length=100, verbose_name='Montant maximum de garantie en lettres'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='mois_debut_paiement',
            field=models.CharField(blank=True, max_length=50, verbose_name='Mois de début de paiement'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='jour_remise_cles',
            field=models.CharField(default='01', max_length=10, verbose_name='Jour de remise des clés'),
        ),
    ]

