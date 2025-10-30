# Safety migration: relax NOT NULL on legacy columns, then drop them if present

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0037_remove_old_resiliation_fields_fix'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        -- travaux_peinture
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'contrats_resiliationcontrat'
                              AND column_name = 'travaux_peinture'
                        ) THEN
                            BEGIN
                                ALTER TABLE contrats_resiliationcontrat
                                    ALTER COLUMN travaux_peinture DROP NOT NULL,
                                    ALTER COLUMN travaux_peinture SET DEFAULT 0;
                            EXCEPTION WHEN undefined_column THEN
                                -- ignore
                                NULL;
                            END;
                        END IF;

                        -- facture_onea
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'contrats_resiliationcontrat'
                              AND column_name = 'facture_onea'
                        ) THEN
                            BEGIN
                                ALTER TABLE contrats_resiliationcontrat
                                    ALTER COLUMN facture_onea DROP NOT NULL,
                                    ALTER COLUMN facture_onea SET DEFAULT 0;
                            EXCEPTION WHEN undefined_column THEN
                                NULL;
                            END;
                        END IF;

                        -- facture_sonabel
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'contrats_resiliationcontrat'
                              AND column_name = 'facture_sonabel'
                        ) THEN
                            BEGIN
                                ALTER TABLE contrats_resiliationcontrat
                                    ALTER COLUMN facture_sonabel DROP NOT NULL,
                                    ALTER COLUMN facture_sonabel SET DEFAULT 0;
                            EXCEPTION WHEN undefined_column THEN
                                NULL;
                            END;
                        END IF;

                        -- travaux_ventilateur
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'contrats_resiliationcontrat'
                              AND column_name = 'travaux_ventilateur'
                        ) THEN
                            BEGIN
                                ALTER TABLE contrats_resiliationcontrat
                                    ALTER COLUMN travaux_ventilateur DROP NOT NULL,
                                    ALTER COLUMN travaux_ventilateur SET DEFAULT 0;
                            EXCEPTION WHEN undefined_column THEN
                                NULL;
                            END;
                        END IF;

                        -- autres_depenses
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'contrats_resiliationcontrat'
                              AND column_name = 'autres_depenses'
                        ) THEN
                            BEGIN
                                ALTER TABLE contrats_resiliationcontrat
                                    ALTER COLUMN autres_depenses DROP NOT NULL,
                                    ALTER COLUMN autres_depenses SET DEFAULT 0;
                            EXCEPTION WHEN undefined_column THEN
                                NULL;
                            END;
                        END IF;

                        -- description_autres_depenses (text) -> just drop not null if any
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'contrats_resiliationcontrat'
                              AND column_name = 'description_autres_depenses'
                        ) THEN
                            BEGIN
                                ALTER TABLE contrats_resiliationcontrat
                                    ALTER COLUMN description_autres_depenses DROP NOT NULL;
                            EXCEPTION WHEN undefined_column THEN
                                NULL;
                            END;
                        END IF;
                    END$$;

                    -- Now drop columns if they are still present (idempotent)
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='travaux_peinture') THEN
                            ALTER TABLE contrats_resiliationcontrat DROP COLUMN travaux_peinture;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='facture_onea') THEN
                            ALTER TABLE contrats_resiliationcontrat DROP COLUMN facture_onea;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='facture_sonabel') THEN
                            ALTER TABLE contrats_resiliationcontrat DROP COLUMN facture_sonabel;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='travaux_ventilateur') THEN
                            ALTER TABLE contrats_resiliationcontrat DROP COLUMN travaux_ventilateur;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='autres_depenses') THEN
                            ALTER TABLE contrats_resiliationcontrat DROP COLUMN autres_depenses;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='description_autres_depenses') THEN
                            ALTER TABLE contrats_resiliationcontrat DROP COLUMN description_autres_depenses;
                        END IF;
                    END$$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                # No state operations — fields already removed from models
            ],
        ),
    ]


