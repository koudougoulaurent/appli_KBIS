#!/usr/bin/env python
"""
Script pour créer les tables manuellement
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def create_tables():
    """Crée les tables manuellement"""
    
    # Table TypeContrat
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contrats_typecontrat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom VARCHAR(100) UNIQUE NOT NULL,
                description TEXT NOT NULL,
                duree_min_mois INTEGER NOT NULL DEFAULT 12,
                duree_max_mois INTEGER NOT NULL DEFAULT 36,
                caution_requise BOOLEAN NOT NULL DEFAULT 1,
                charges_comprises BOOLEAN NOT NULL DEFAULT 0
            );
        """)
        
        # Table TypePaiement
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paiements_typepaiement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom VARCHAR(100) UNIQUE NOT NULL,
                description TEXT NOT NULL,
                est_recurrent BOOLEAN NOT NULL DEFAULT 0,
                est_remboursable BOOLEAN NOT NULL DEFAULT 0,
                couleur VARCHAR(7) NOT NULL DEFAULT '#007bff'
            );
        """)
        
        print("Tables créées avec succès !")

if __name__ == '__main__':
    print("Création des tables...")
    create_tables()
    print("Terminé !") 