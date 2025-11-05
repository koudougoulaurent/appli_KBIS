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
        with schema_editor.connection.cursor() as cursor:
            if schema_editor.connection.vendor == 'sqlite':
                # Pour SQLite, utiliser des placeholders ?
                placeholders = ','.join(['?'] * len(ids_sans_bailleur))
                
                # Supprimer les relations ManyToMany avec paiements_concernes
                if ids_sans_bailleur:
                    sql = f"DELETE FROM paiements_recapmensuel_paiements_concernes WHERE recapmensuel_id IN ({placeholders})"
                    cursor.execute(sql, ids_sans_bailleur)
                
                # Supprimer les relations ManyToMany avec charges_deductibles
                if ids_sans_bailleur:
                    sql = f"DELETE FROM paiements_recapmensuel_charges_deductibles WHERE recapmensuel_id IN ({placeholders})"
                    cursor.execute(sql, ids_sans_bailleur)
                
                # Enfin, supprimer les récapitulatifs eux-mêmes
                if ids_sans_bailleur:
                    sql = f"DELETE FROM paiements_recapmensuel WHERE id IN ({placeholders})"
                    cursor.execute(sql, ids_sans_bailleur)
            else:
                # Pour PostgreSQL et autres bases de données
                placeholders = ','.join(['%s'] * len(ids_sans_bailleur))
                
                # Supprimer les relations ManyToMany avec paiements_concernes
                if ids_sans_bailleur:
                    sql = f"DELETE FROM paiements_recapmensuel_paiements_concernes WHERE recapmensuel_id IN ({placeholders})"
                    cursor.execute(sql, ids_sans_bailleur)
                
                # Supprimer les relations ManyToMany avec charges_deductibles
                if ids_sans_bailleur:
                    sql = f"DELETE FROM paiements_recapmensuel_charges_deductibles WHERE recapmensuel_id IN ({placeholders})"
                    cursor.execute(sql, ids_sans_bailleur)
                
                # Enfin, supprimer les récapitulatifs eux-mêmes
                if ids_sans_bailleur:
                    sql = f"DELETE FROM paiements_recapmensuel WHERE id IN ({placeholders})"
                    cursor.execute(sql, ids_sans_bailleur)
        
        print(f"⚠️  {count} récapitulatif(s) sans bailleur ont été supprimés physiquement.")
        print("   Ces récapitulatifs ne peuvent pas être utilisés sans bailleur.")


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

