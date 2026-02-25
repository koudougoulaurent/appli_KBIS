from django.db import migrations


class Migration(migrations.Migration):
    """
    Merge migration : réconcilie la branche 0031_paiement_est_saisie_manuelle_historique
    (créée le 2026-02-12) avec la branche principale 0050_add_mois_effet_personnalise.
    """

    dependencies = [
        ('paiements', '0031_paiement_est_saisie_manuelle_historique'),
        ('paiements', '0050_add_mois_effet_personnalise'),
    ]

    operations = [
    ]
