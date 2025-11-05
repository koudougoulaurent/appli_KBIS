# Generated manually

from django.db import migrations, models
import django.db.models.deletion


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

