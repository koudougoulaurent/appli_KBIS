# Safety migration: relax NOT NULL on legacy columns, then drop them if present

from django.db import migrations


def _postgres_relax_and_drop(apps, schema_editor):
    # Skip on SQLite and other vendors
    if schema_editor.connection.vendor != 'postgresql':
        return
    statements = [
        # Relax NOT NULL + set default 0 if column exists
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='travaux_peinture') THEN
                ALTER TABLE contrats_resiliationcontrat ALTER COLUMN travaux_peinture DROP NOT NULL,
                                                       ALTER COLUMN travaux_peinture SET DEFAULT 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='facture_onea') THEN
                ALTER TABLE contrats_resiliationcontrat ALTER COLUMN facture_onea DROP NOT NULL,
                                                       ALTER COLUMN facture_onea SET DEFAULT 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='facture_sonabel') THEN
                ALTER TABLE contrats_resiliationcontrat ALTER COLUMN facture_sonabel DROP NOT NULL,
                                                       ALTER COLUMN facture_sonabel SET DEFAULT 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='travaux_ventilateur') THEN
                ALTER TABLE contrats_resiliationcontrat ALTER COLUMN travaux_ventilateur DROP NOT NULL,
                                                       ALTER COLUMN travaux_ventilateur SET DEFAULT 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='autres_depenses') THEN
                ALTER TABLE contrats_resiliationcontrat ALTER COLUMN autres_depenses DROP NOT NULL,
                                                       ALTER COLUMN autres_depenses SET DEFAULT 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='description_autres_depenses') THEN
                ALTER TABLE contrats_resiliationcontrat ALTER COLUMN description_autres_depenses DROP NOT NULL;
            END IF;
        END$$;
        """,
        # Drop if still present
        """
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
    ]
    with schema_editor.connection.cursor() as cursor:
        for sql in statements:
            cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0037_remove_old_resiliation_fields_fix'),
    ]

    operations = [
        migrations.RunPython(code=_postgres_relax_and_drop, reverse_code=migrations.RunPython.noop),
    ]


