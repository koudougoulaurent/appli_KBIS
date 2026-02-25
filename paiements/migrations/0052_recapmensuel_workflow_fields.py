import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Ajoute les champs de workflow manquants au modèle RecapMensuel :
    date_validation, date_envoi, date_paiement, valide_par.
    Ces champs sont nécessaires pour le bon fonctionnement de l'admin Django.
    """

    dependencies = [
        ('paiements', '0051_merge_branches'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='recapmensuel',
            name='date_validation',
            field=models.DateField(blank=True, null=True, verbose_name='Date de validation'),
        ),
        migrations.AddField(
            model_name='recapmensuel',
            name='date_envoi',
            field=models.DateField(blank=True, null=True, verbose_name="Date d'envoi au bailleur"),
        ),
        migrations.AddField(
            model_name='recapmensuel',
            name='date_paiement',
            field=models.DateField(blank=True, null=True, verbose_name='Date de paiement au bailleur'),
        ),
        migrations.AddField(
            model_name='recapmensuel',
            name='valide_par',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recaps_mensuels_valides',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Validé par',
            ),
        ),
    ]
