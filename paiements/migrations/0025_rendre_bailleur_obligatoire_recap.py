# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def supprimer_recaps_sans_bailleur(apps, schema_editor):
    """Supprime (logiquement) les récapitulatifs sans bailleur."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    
    # Marquer comme supprimés les récapitulatifs sans bailleur
    recaps_sans_bailleur = RecapMensuel.objects.filter(bailleur__isnull=True, is_deleted=False)
    count = recaps_sans_bailleur.count()
    
    if count > 0:
        # Option 1: Les supprimer logiquement
        from django.utils import timezone
        recaps_sans_bailleur.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        print(f"⚠️  {count} récapitulatif(s) sans bailleur ont été marqués comme supprimés.")
        print("   Vous pouvez les restaurer manuellement si nécessaire.")


def reverse_supprimer_recaps_sans_bailleur(apps, schema_editor):
    """Fonction de rollback - ne fait rien car on ne peut pas restaurer automatiquement."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0024_update_existing_retraits_commission'),
        ('proprietes', '__latest__'),
    ]

    operations = [
        # D'abord, supprimer (logiquement) les récapitulatifs sans bailleur
        migrations.RunPython(
            supprimer_recaps_sans_bailleur,
            reverse_supprimer_recaps_sans_bailleur
        ),
        
        # Ensuite, rendre le champ obligatoire
        migrations.AlterField(
            model_name='recapmensuel',
            name='bailleur',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='recaps_mensuels',
                to='proprietes.bailleur',
                verbose_name='Bailleur'
            ),
        ),
    ]

