#!/usr/bin/env python
"""
Script de migration intelligent pour Render
Applique les migrations et gère les erreurs
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Fonction principale de migration"""
    print("🚀 Démarrage du script de migration intelligent...")
    
    # Configuration Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
    django.setup()
    
    print("📊 Vérification des migrations...")
    
    try:
        # Vérifier les migrations en attente
        from django.core.management import call_command
        from io import StringIO
        
        # Capturer la sortie de showmigrations
        output = StringIO()
        call_command('showmigrations', '--plan', stdout=output)
        migrations_output = output.getvalue()
        
        print("📋 État des migrations:")
        print(migrations_output)
        
        # Appliquer les migrations
        print("🔄 Application des migrations...")
        call_command('migrate', verbosity=2)
        
        print("✅ Migrations appliquées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        print("🔄 Tentative de correction directe des champs téléphone...")
        
        try:
            # Correction directe des champs téléphone
            from django.db import connection
            
            with connection.cursor() as cursor:
                print("🔧 Correction des champs téléphone...")
                
                # Modifier les colonnes de la table locataire
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN telephone TYPE VARCHAR(30)")
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN telephone_mobile TYPE VARCHAR(30)")
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN garant_telephone TYPE VARCHAR(30)")
                
                # Modifier les colonnes de la table bailleur
                cursor.execute("ALTER TABLE proprietes_bailleur ALTER COLUMN telephone TYPE VARCHAR(30)")
                cursor.execute("ALTER TABLE proprietes_bailleur ALTER COLUMN telephone_mobile TYPE VARCHAR(30)")
                
                print("✅ Correction directe réussie!")
                
        except Exception as e2:
            print(f"❌ Échec de la correction directe: {e2}")
            sys.exit(1)
    
    print("🎉 Migration terminée avec succès!")

if __name__ == '__main__':
    main()