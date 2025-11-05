# Generated manually

from django.db import migrations, models
import django.db.models.deletion


def supprimer_recaps_sans_bailleur(apps, schema_editor):
    """Supprime physiquement les récapitulatifs sans bailleur."""
    # Utiliser une requête SQL directe pour éviter les problèmes avec les relations
    # PostgreSQL: utiliser un bloc DO pour forcer la suppression avant l'alteration
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            # Supprimer les relations ManyToMany et les récapitulatifs en une seule transaction
            cursor.execute("""
                DO $$
                DECLARE
                    recap_ids INTEGER[];
                BEGIN
                    -- Récupérer les IDs des récapitulatifs sans bailleur
                    SELECT ARRAY_AGG(id) INTO recap_ids
                    FROM paiements_recapmensuel
                    WHERE bailleur_id IS NULL;
                    
                    -- Si des récapitulatifs existent, les supprimer
                    IF recap_ids IS NOT NULL AND array_length(recap_ids, 1) > 0 THEN
                        -- Supprimer les relations ManyToMany
                        DELETE FROM paiements_recapmensuel_paiements_concernes 
                        WHERE recapmensuel_id = ANY(recap_ids);
                        
                        DELETE FROM paiements_recapmensuel_charges_deductibles 
                        WHERE recapmensuel_id = ANY(recap_ids);
                        
                        -- Supprimer les récapitulatifs eux-mêmes
                        DELETE FROM paiements_recapmensuel 
                        WHERE id = ANY(recap_ids);
                        
                        RAISE NOTICE 'Supprimé % récapitulatifs sans bailleur', array_length(recap_ids, 1);
                    END IF;
                END $$;
            """)
    else:
        # Pour les autres bases de données
        RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM paiements_recapmensuel 
                WHERE bailleur_id IS NULL
            """)
            ids_sans_bailleur = [row[0] for row in cursor.fetchall()]
        
        count = len(ids_sans_bailleur)
        
        if count > 0:
            with schema_editor.connection.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(ids_sans_bailleur))
                
                if ids_sans_bailleur:
                    cursor.execute(f"""
                        DELETE FROM paiements_recapmensuel_paiements_concernes 
                        WHERE recapmensuel_id IN ({placeholders})
                    """, ids_sans_bailleur)
                    
                    cursor.execute(f"""
                        DELETE FROM paiements_recapmensuel_charges_deductibles 
                        WHERE recapmensuel_id IN ({placeholders})
                    """, ids_sans_bailleur)
                    
                    cursor.execute(f"""
                        DELETE FROM paiements_recapmensuel 
                        WHERE id IN ({placeholders})
                    """, ids_sans_bailleur)
            
            print(f"⚠️  {count} récapitulatif(s) sans bailleur ont été supprimés physiquement.")


def reverse_supprimer_recaps_sans_bailleur(apps, schema_editor):
    """Fonction de rollback - ne fait rien car on ne peut pas restaurer automatiquement les suppressions physiques."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0024_update_existing_retraits_commission'),
        ('proprietes', '__latest__'),
    ]

    operations = [
        # D'abord, supprimer physiquement les récapitulatifs sans bailleur
        # Utiliser RunSQL pour forcer l'exécution avant l'alteration
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    recap_ids INTEGER[];
                BEGIN
                    SELECT ARRAY_AGG(id) INTO recap_ids
                    FROM paiements_recapmensuel
                    WHERE bailleur_id IS NULL;
                    
                    IF recap_ids IS NOT NULL AND array_length(recap_ids, 1) > 0 THEN
                        DELETE FROM paiements_recapmensuel_paiements_concernes 
                        WHERE recapmensuel_id = ANY(recap_ids);
                        
                        DELETE FROM paiements_recapmensuel_charges_deductibles 
                        WHERE recapmensuel_id = ANY(recap_ids);
                        
                        DELETE FROM paiements_recapmensuel 
                        WHERE id = ANY(recap_ids);
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
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

