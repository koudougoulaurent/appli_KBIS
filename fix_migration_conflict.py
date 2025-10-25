#!/usr/bin/env python
"""
Script pour résoudre le conflit de migration sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

from django.db import connection
from django.core.management import call_command

def fix_migration_conflict():
    """Résout le conflit de migration en marquant la migration comme appliquée"""
    print("RÉSOLUTION DU CONFLIT DE MIGRATION")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Vérifier si la table existe
        try:
            cursor.execute("SELECT COUNT(*) FROM paiements_chargebailleur;")
            count = cursor.fetchone()[0]
            print(f"✅ Table paiements_chargebailleur existe avec {count} enregistrements")
            
            # Marquer la migration comme appliquée sans l'exécuter
            print("🔧 Marquage de la migration 0019 comme appliquée...")
            call_command('migrate', 'paiements', '0019', '--fake')
            print("✅ Migration 0019 marquée comme appliquée")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = fix_migration_conflict()
    if success:
        print("\n🎉 Conflit de migration résolu !")
    else:
        print("\n💥 Échec de la résolution du conflit")
