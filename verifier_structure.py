#!/usr/bin/env python
"""
Script pour vérifier la structure des tables de la base de données.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def verifier_structure():
    """Vérifie la structure des tables"""
    print("🔍 Vérification de la structure des tables...")
    
    with connection.cursor() as cursor:
        # Vérifier la structure de la table proprietes_propriete
        print("\n📋 Structure de proprietes_propriete:")
        cursor.execute("PRAGMA table_info(proprietes_propriete)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Vérifier la structure de la table contrats_contrat
        print("\n📋 Structure de contrats_contrat:")
        cursor.execute("PRAGMA table_info(contrats_contrat)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Vérifier la structure de la table paiements_paiement
        print("\n📋 Structure de paiements_paiement:")
        cursor.execute("PRAGMA table_info(paiements_paiement)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Vérifier la structure de la table paiements_recu
        print("\n📋 Structure de paiements_recu:")
        cursor.execute("PRAGMA table_info(paiements_recu)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Vérifier la structure de la table contrats_quittance
        print("\n📋 Structure de contrats_quittance:")
        cursor.execute("PRAGMA table_info(contrats_quittance)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Vérifier la structure de la table paiements_chargedeductible
        print("\n📋 Structure de paiements_chargedeductible:")
        cursor.execute("PRAGMA table_info(paiements_chargedeductible)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

if __name__ == "__main__":
    verifier_structure()
