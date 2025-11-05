# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def supprimer_recaps_sans_bailleur(apps, schema_editor):
    """Supprime physiquement les récapitulatifs sans bailleur."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    
    # Récupérer tous les IDs des récapitulatifs sans bailleur
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'sqlite':
            cursor.execute("""
                SELECT id FROM paiements_recapmensuel 
                WHERE bailleur_id IS NULL
            """)
        else:
            cursor.execute("""
                SELECT id FROM paiements_recapmensuel 
                WHERE bailleur_id IS NULL
            """)
        ids_sans_bailleur = [row[0] for row in cursor.fetchall()]
    
    count = len(ids_sans_bailleur)
    
    if count > 0:
        # Supprimer physiquement ces récapitulatifs
        # Utiliser l'ORM Django pour éviter les problèmes de syntaxe SQL
        RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
        
        # Supprimer les relations ManyToMany d'abord
        for recap_id in ids_sans_bailleur:
            try:
                recap = RecapMensuel.objects.get(pk=recap_id)
                # Supprimer les relations ManyToMany
                recap.paiements_concernes.clear()
                recap.charges_deductibles.clear()
            except RecapMensuel.DoesNotExist:
                pass
        
        # Ensuite, supprimer les récapitulatifs eux-mêmes
        RecapMensuel.objects.filter(id__in=ids_sans_bailleur).delete()
        
        print(f"[INFO] {count} recapitulatif(s) sans bailleur ont ete supprimes physiquement.")
        print("   Ces recapitulatifs ne peuvent pas etre utilises sans bailleur.")


def reverse_supprimer_recaps_sans_bailleur(apps, schema_editor):
    """Fonction de rollback - ne fait rien car on ne peut pas restaurer automatiquement les suppressions physiques."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0024_update_existing_retraits_commission'),
        ('proprietes', '0036_fix_charges_bailleur_numero_unique'),
    ]

    operations = [
        # D'abord, supprimer physiquement les récapitulatifs sans bailleur
        # Utiliser RunPython pour gérer les différentes bases de données
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

