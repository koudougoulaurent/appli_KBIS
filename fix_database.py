#!/usr/bin/env python
"""
Script to fix the database schema issues
"""
import os
import sys
import django
from django.db import connection

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

def fix_devise_table():
    """Add missing columns to core_devise table"""
    with connection.cursor() as cursor:
        try:
            # Check if taux_change column exists
            cursor.execute("PRAGMA table_info(core_devise);")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'taux_change' not in columns:
                print("Adding taux_change column...")
                cursor.execute("ALTER TABLE core_devise ADD COLUMN taux_change DECIMAL(10,4) DEFAULT 1.0;")
            
            if 'date_creation' not in columns:
                print("Adding date_creation column...")
                cursor.execute("ALTER TABLE core_devise ADD COLUMN date_creation DATETIME DEFAULT '2025-01-01 00:00:00';")
            
            if 'date_modification' not in columns:
                print("Adding date_modification column...")
                cursor.execute("ALTER TABLE core_devise ADD COLUMN date_modification DATETIME DEFAULT '2025-01-01 00:00:00';")
            
            if 'par_defaut' not in columns:
                print("Adding par_defaut column...")
                cursor.execute("ALTER TABLE core_devise ADD COLUMN par_defaut BOOLEAN DEFAULT 0;")
            
            if 'active' not in columns:
                print("Adding active column...")
                cursor.execute("ALTER TABLE core_devise ADD COLUMN active BOOLEAN DEFAULT 1;")
            
            print("Database schema fixed successfully!")
            
        except Exception as e:
            print(f"Error fixing database: {e}")

if __name__ == "__main__":
    fix_devise_table()
