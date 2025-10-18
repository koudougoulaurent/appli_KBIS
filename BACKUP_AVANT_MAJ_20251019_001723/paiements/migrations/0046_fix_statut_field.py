# Migration de correction pour le champ statut manquant
# Generated manually on 2025-01-XX

from django.db import migrations, models, connection

def add_statut_column_if_not_exists(schema_editor):
    """Add statut column if it doesn't exist"""
    with connection.cursor() as cursor:
        # Check if column exists (PostgreSQL syntax)
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'paiements_retraitbailleur' 
            AND column_name = 'statut'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE paiements_retraitbailleur 
                ADD COLUMN statut VARCHAR(20) DEFAULT 'en_attente'
            """)

def remove_statut_column(schema_editor):
    """Remove statut column"""
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE paiements_retraitbailleur DROP COLUMN statut")

def create_statut_index_if_not_exists(schema_editor):
    """Create statut index if it doesn't exist"""
    with connection.cursor() as cursor:
        # Check if index exists (PostgreSQL syntax)
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'paiements_retraitbailleur' 
            AND indexname = 'paiements_r_statut_123456_idx'
        """)
        if not cursor.fetchone():
            cursor.execute("CREATE INDEX paiements_r_statut_123456_idx ON paiements_retraitbailleur (statut)")

def drop_statut_index(schema_editor):
    """Drop statut index"""
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS paiements_r_statut_123456_idx")

class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0031_add_total_charges_bailleur_column'),
    ]

    operations = [
        # Ajouter le champ statut s'il n'existe pas
        migrations.RunPython(
            code=lambda apps, schema_editor: add_statut_column_if_not_exists(schema_editor),
            reverse_code=lambda apps, schema_editor: remove_statut_column(schema_editor)
        ),
        
        # Créer l'index sur statut
        migrations.RunPython(
            code=lambda apps, schema_editor: create_statut_index_if_not_exists(schema_editor),
            reverse_code=lambda apps, schema_editor: drop_statut_index(schema_editor)
        ),
    ]
