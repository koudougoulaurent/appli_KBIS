# Generated migration fix to ensure old fields are removed

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0036_add_dynamic_expenses'),
    ]

    operations = [
        # Try to remove fields that might still exist in the database
        # These operations will be ignored if the fields don't exist
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # PostgreSQL - Check and drop columns if they exist
                migrations.RunSQL(
                    sql="""
                        DO $$ 
                        BEGIN 
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='contrats_resiliationcontrat' 
                                       AND column_name='travaux_peinture') THEN 
                                ALTER TABLE contrats_resiliationcontrat DROP COLUMN travaux_peinture; 
                            END IF; 
                            
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='contrats_resiliationcontrat' 
                                       AND column_name='facture_onea') THEN 
                                ALTER TABLE contrats_resiliationcontrat DROP COLUMN facture_onea; 
                            END IF; 
                            
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='contrats_resiliationcontrat' 
                                       AND column_name='facture_sonabel') THEN 
                                ALTER TABLE contrats_resiliationcontrat DROP COLUMN facture_sonabel; 
                            END IF; 
                            
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='contrats_resiliationcontrat' 
                                       AND column_name='travaux_ventilateur') THEN 
                                ALTER TABLE contrats_resiliationcontrat DROP COLUMN travaux_ventilateur; 
                            END IF; 
                            
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='contrats_resiliationcontrat' 
                                       AND column_name='autres_depenses') THEN 
                                ALTER TABLE contrats_resiliationcontrat DROP COLUMN autres_depenses; 
                            END IF; 
                            
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='contrats_resiliationcontrat' 
                                       AND column_name='description_autres_depenses') THEN 
                                ALTER TABLE contrats_resiliationcontrat DROP COLUMN description_autres_depenses; 
                            END IF; 
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                # No state changes needed - fields already removed in migration 0036
            ],
        ),
    ]

