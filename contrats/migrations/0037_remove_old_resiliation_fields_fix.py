# Generated migration fix to ensure old fields are removed

from django.db import migrations


def _postgres_drop_columns(apps, schema_editor):
    # Only run on PostgreSQL. For SQLite/MySQL locally, do nothing.
    if schema_editor.connection.vendor != 'postgresql':
        return
    statements = [
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='travaux_peinture') THEN ALTER TABLE contrats_resiliationcontrat DROP COLUMN travaux_peinture; END IF; END $$;",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='facture_onea') THEN ALTER TABLE contrats_resiliationcontrat DROP COLUMN facture_onea; END IF; END $$;",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='facture_sonabel') THEN ALTER TABLE contrats_resiliationcontrat DROP COLUMN facture_sonabel; END IF; END $$;",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='travaux_ventilateur') THEN ALTER TABLE contrats_resiliationcontrat DROP COLUMN travaux_ventilateur; END IF; END $$;",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='autres_depenses') THEN ALTER TABLE contrats_resiliationcontrat DROP COLUMN autres_depenses; END IF; END $$;",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='contrats_resiliationcontrat' AND column_name='description_autres_depenses') THEN ALTER TABLE contrats_resiliationcontrat DROP COLUMN description_autres_depenses; END IF; END $$;",
    ]
    with schema_editor.connection.cursor() as cursor:
        for sql in statements:
            cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0036_add_dynamic_expenses'),
    ]

    operations = [
        migrations.RunPython(code=_postgres_drop_columns, reverse_code=migrations.RunPython.noop),
    ]

