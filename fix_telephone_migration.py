#!/usr/bin/env python
"""
Script pour corriger directement les champs téléphone en base de données
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Fonction principale de correction"""
    print("🔧 Correction des champs téléphone...")
    
    # Configuration Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
    django.setup()
    
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            print("📊 Vérification de la structure actuelle...")
            
            # Vérifier la structure de la table locataire
            cursor.execute("""
                SELECT column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'proprietes_locataire' 
                AND column_name IN ('telephone', 'telephone_mobile', 'garant_telephone')
            """)
            
            columns = cursor.fetchall()
            print("Colonnes actuelles:", columns)
            
            # Modifier les colonnes si nécessaire
            print("🔄 Modification des colonnes...")
            
            # Modifier telephone
            cursor.execute("""
                ALTER TABLE proprietes_locataire 
                ALTER COLUMN telephone TYPE VARCHAR(30)
            """)
            print("✅ telephone modifié")
            
            # Modifier telephone_mobile
            cursor.execute("""
                ALTER TABLE proprietes_locataire 
                ALTER COLUMN telephone_mobile TYPE VARCHAR(30)
            """)
            print("✅ telephone_mobile modifié")
            
            # Modifier garant_telephone
            cursor.execute("""
                ALTER TABLE proprietes_locataire 
                ALTER COLUMN garant_telephone TYPE VARCHAR(30)
            """)
            print("✅ garant_telephone modifié")
            
            # Modifier les colonnes de la table bailleur
            cursor.execute("""
                ALTER TABLE proprietes_bailleur 
                ALTER COLUMN telephone TYPE VARCHAR(30)
            """)
            print("✅ bailleur.telephone modifié")
            
            cursor.execute("""
                ALTER TABLE proprietes_bailleur 
                ALTER COLUMN telephone_mobile TYPE VARCHAR(30)
            """)
            print("✅ bailleur.telephone_mobile modifié")
            
            print("🎉 Toutes les colonnes ont été modifiées avec succès!")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
