# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0026_add_commission_agence_recap_mensuel'),
    ]

    operations = [
        # Supprimer l'ancienne contrainte unique_together
        migrations.AlterUniqueTogether(
            name='recapmensuel',
            unique_together=set(),
        ),
        # Ajouter la nouvelle contrainte conditionnelle qui ne s'applique qu'aux récapitulatifs non supprimés
        migrations.AddConstraint(
            model_name='recapmensuel',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_deleted', False)),
                fields=('bailleur', 'mois_recap'),
                name='unique_recap_bailleur_mois_actif'
            ),
        ),
    ]

