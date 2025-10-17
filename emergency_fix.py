#!/usr/bin/env python
"""
Script de correction d'urgence pour les champs téléphone
Exécution immédiate et forcée
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

from django.db import connection

def main():
    """Correction d'urgence des champs téléphone"""
    print("URGENCE: CORRECTION DES CHAMPS TELEPHONE")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            print("Verification de la structure actuelle...")
            
            # Vérifier la structure de la table locataire
            cursor.execute("""
                SELECT column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'proprietes_locataire' 
                AND column_name IN ('telephone', 'telephone_mobile', 'garant_telephone')
                ORDER BY column_name
            """)
            
            columns = cursor.fetchall()
            print("Colonnes de proprietes_locataire:")
            for col in columns:
                print(f"  - {col[0]}: VARCHAR({col[1]})")
            
            print("\nCorrection des colonnes...")
            
            # Modifier telephone
            try:
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN telephone TYPE VARCHAR(30)")
                print("OK: proprietes_locataire.telephone modifie (20 -> 30)")
            except Exception as e:
                print(f"ERREUR telephone: {e}")
            
            # Modifier telephone_mobile
            try:
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN telephone_mobile TYPE VARCHAR(30)")
                print("OK: proprietes_locataire.telephone_mobile modifie (20 -> 30)")
            except Exception as e:
                print(f"ERREUR telephone_mobile: {e}")
            
            # Modifier garant_telephone
            try:
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN garant_telephone TYPE VARCHAR(30)")
                print("OK: proprietes_locataire.garant_telephone modifie (20 -> 30)")
            except Exception as e:
                print(f"ERREUR garant_telephone: {e}")
            
            # Modifier les colonnes de la table bailleur
            try:
                cursor.execute("ALTER TABLE proprietes_bailleur ALTER COLUMN telephone TYPE VARCHAR(30)")
                print("OK: proprietes_bailleur.telephone modifie (20 -> 30)")
            except Exception as e:
                print(f"ERREUR bailleur.telephone: {e}")
            
            try:
                cursor.execute("ALTER TABLE proprietes_bailleur ALTER COLUMN telephone_mobile TYPE VARCHAR(30)")
                print("OK: proprietes_bailleur.telephone_mobile modifie (20 -> 30)")
            except Exception as e:
                print(f"ERREUR bailleur.telephone_mobile: {e}")
            
            print("\nVerification finale...")
            
            # Vérification finale
            cursor.execute("""
                SELECT table_name, column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name IN ('proprietes_locataire', 'proprietes_bailleur')
                AND column_name IN ('telephone', 'telephone_mobile', 'garant_telephone')
                ORDER BY table_name, column_name
            """)
            
            final_columns = cursor.fetchall()
            print("Structure finale:")
            for col in final_columns:
                print(f"  - {col[0]}.{col[1]}: VARCHAR({col[2]})")
            
            print("\nCORRECTION TERMINEE!")
            
    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
