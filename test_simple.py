#!/usr/bin/env python
"""
Script de test simple pour vérifier la correction des champs téléphone
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
django.setup()

from django.db import connection

def main():
    """Test de la correction des champs téléphone"""
    print("TEST DE LA CORRECTION DES CHAMPS TELEPHONE")
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
            
            # Vérifier la structure de la table bailleur
            cursor.execute("""
                SELECT column_name, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'proprietes_bailleur' 
                AND column_name IN ('telephone', 'telephone_mobile')
                ORDER BY column_name
            """)
            
            columns_bailleur = cursor.fetchall()
            print("\nColonnes de proprietes_bailleur:")
            for col in columns_bailleur:
                print(f"  - {col[0]}: VARCHAR({col[1]})")
            
            # Vérifier si toutes les colonnes sont à 30 caractères
            all_correct = True
            for col in columns + columns_bailleur:
                if col[1] != 30:
                    all_correct = False
                    print(f"ERREUR: {col[0]} a encore {col[1]} caracteres")
                else:
                    print(f"OK: {col[0]} a bien 30 caracteres")
            
            if all_correct:
                print("\nTOUS LES CHAMPS SONT CORRECTS!")
            else:
                print("\nCERTAINS CHAMPS NECESSITENT ENCORE UNE CORRECTION")
            
    except Exception as e:
        print(f"ERREUR: {e}")

if __name__ == '__main__':
    main()
