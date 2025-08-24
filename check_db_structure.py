#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def check_devise_table():
    with connection.cursor() as cursor:
        # Check if the table exists and get its structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='core_devise';")
        result = cursor.fetchone()
        if result:
            print("Table core_devise structure:")
            print(result[0])
            print("\n")
            
            # Get column information
            cursor.execute("PRAGMA table_info(core_devise);")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - NOT NULL: {col[3]} - DEFAULT: {col[4]}")
        else:
            print("Table core_devise does not exist")

if __name__ == "__main__":
    check_devise_table()
