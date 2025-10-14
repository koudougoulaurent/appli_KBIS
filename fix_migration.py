#!/usr/bin/env python
"""
Script pour résoudre les problèmes de migration sur Render
"""
import os
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def fix_migrations():
    """Résout les problèmes de migration"""
    print("🔧 Résolution des problèmes de migration...")
    
    try:
        # Marquer toutes les migrations comme appliquées sans les exécuter
        print("📋 Marquage des migrations comme appliquées...")
        execute_from_command_line(['manage.py', 'migrate', '--fake'])
        
        print("✅ Migrations marquées comme appliquées avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la résolution des migrations: {e}")
        return False

if __name__ == '__main__':
    fix_migrations()
