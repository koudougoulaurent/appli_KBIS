#!/usr/bin/env python3
"""
Script d'urgence pour corriger le champ numero_locataire
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
django.setup()

from django.db import connection

def fix_numero_locataire():
    """Corriger le champ numero_locataire de VARCHAR(20) à VARCHAR(50)"""
    
    print("CORRECTION DU CHAMP numero_locataire...")
    
    with connection.cursor() as cursor:
        try:
            # Vérifier la structure actuelle
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'proprietes_locataire' 
                AND column_name = 'numero_locataire';
            """)
            result = cursor.fetchone()
            
            if result:
                print(f"Structure actuelle: {result[0]} = {result[1]}({result[2]})")
                
                if result[2] == 20:
                    print("Correction necessaire: VARCHAR(20) -> VARCHAR(50)")
                    
                    # Corriger le champ
                    cursor.execute("""
                        ALTER TABLE proprietes_locataire 
                        ALTER COLUMN numero_locataire TYPE VARCHAR(50);
                    """)
                    
                    print("Champ numero_locataire corrige: VARCHAR(20) -> VARCHAR(50)")
                    
                    # Vérification
                    cursor.execute("""
                        SELECT column_name, data_type, character_maximum_length 
                        FROM information_schema.columns 
                        WHERE table_name = 'proprietes_locataire' 
                        AND column_name = 'numero_locataire';
                    """)
                    result = cursor.fetchone()
                    print(f"Structure finale: {result[0]} = {result[1]}({result[2]})")
                    
                else:
                    print(f"Champ deja correct: {result[1]}({result[2]})")
            else:
                print("Champ numero_locataire non trouve!")
                
        except Exception as e:
            print(f"Erreur: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("DEMARRAGE DE LA CORRECTION...")
    success = fix_numero_locataire()
    
    if success:
        print("CORRECTION TERMINEE AVEC SUCCES!")
    else:
        print("ECHEC DE LA CORRECTION!")
        sys.exit(1)
