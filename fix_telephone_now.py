#!/usr/bin/env python
"""
Script de correction immédiate des champs téléphone
À exécuter manuellement sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

from django.db import connection

def main():
    """Correction immédiate des champs téléphone"""
    print("🔧 CORRECTION IMMÉDIATE DES CHAMPS TÉLÉPHONE")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            print("📊 Vérification de la structure actuelle...")
            
            # Vérifier la structure de la table locataire
            cursor.execute("""
                SELECT column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'proprietes_locataire' 
                AND column_name IN ('telephone', 'telephone_mobile', 'garant_telephone')
                ORDER BY column_name
            """)
            
            columns = cursor.fetchall()
            print("Colonnes actuelles de proprietes_locataire:")
            for col in columns:
                print(f"  - {col[0]}: VARCHAR({col[1]})")
            
            print("\n🔄 Modification des colonnes...")
            
            # Modifier telephone
            try:
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN telephone TYPE VARCHAR(30)")
                print("✅ proprietes_locataire.telephone modifié (20 → 30)")
            except Exception as e:
                print(f"⚠️ Erreur telephone: {e}")
            
            # Modifier telephone_mobile
            try:
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN telephone_mobile TYPE VARCHAR(30)")
                print("✅ proprietes_locataire.telephone_mobile modifié (20 → 30)")
            except Exception as e:
                print(f"⚠️ Erreur telephone_mobile: {e}")
            
            # Modifier garant_telephone
            try:
                cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN garant_telephone TYPE VARCHAR(30)")
                print("✅ proprietes_locataire.garant_telephone modifié (20 → 30)")
            except Exception as e:
                print(f"⚠️ Erreur garant_telephone: {e}")
            
            print("\n📊 Vérification de la structure de proprietes_bailleur...")
            
            # Vérifier la structure de la table bailleur
            cursor.execute("""
                SELECT column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'proprietes_bailleur' 
                AND column_name IN ('telephone', 'telephone_mobile')
                ORDER BY column_name
            """)
            
            columns_bailleur = cursor.fetchall()
            print("Colonnes actuelles de proprietes_bailleur:")
            for col in columns_bailleur:
                print(f"  - {col[0]}: VARCHAR({col[1]})")
            
            print("\n🔄 Modification des colonnes bailleur...")
            
            # Modifier telephone bailleur
            try:
                cursor.execute("ALTER TABLE proprietes_bailleur ALTER COLUMN telephone TYPE VARCHAR(30)")
                print("✅ proprietes_bailleur.telephone modifié (20 → 30)")
            except Exception as e:
                print(f"⚠️ Erreur bailleur.telephone: {e}")
            
            # Modifier telephone_mobile bailleur
            try:
                cursor.execute("ALTER TABLE proprietes_bailleur ALTER COLUMN telephone_mobile TYPE VARCHAR(30)")
                print("✅ proprietes_bailleur.telephone_mobile modifié (20 → 30)")
            except Exception as e:
                print(f"⚠️ Erreur bailleur.telephone_mobile: {e}")
            
            print("\n📊 Vérification finale...")
            
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
            
            print("\n🎉 CORRECTION TERMINÉE AVEC SUCCÈS!")
            print("Les champs téléphone acceptent maintenant 30 caractères.")
            
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
