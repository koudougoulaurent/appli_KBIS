#!/usr/bin/env python
"""
Script pour créer les tables des retraits via Django
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def create_tables():
    """Crée les tables des retraits"""
    
    print("Création des tables des retraits...")
    
    with connection.cursor() as cursor:
        # Vérifier si les tables existent déjà
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='paiements_retraitbailleur'
        """)
        
        if cursor.fetchone():
            print("Les tables existent déjà.")
            return
        
        # Table RetraitBailleur
        cursor.execute("""
            CREATE TABLE paiements_retraitbailleur (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mois_retrait DATE NOT NULL,
                montant_loyers_bruts DECIMAL(12,2) DEFAULT 0 NOT NULL,
                montant_charges_deductibles DECIMAL(12,2) DEFAULT 0 NOT NULL,
                montant_charges_bailleur DECIMAL(12,2) DEFAULT 0 NOT NULL,
                montant_net_a_payer DECIMAL(12,2) DEFAULT 0 NOT NULL,
                statut VARCHAR(20) DEFAULT 'en_attente' NOT NULL,
                type_retrait VARCHAR(20) DEFAULT 'mensuel' NOT NULL,
                mode_retrait VARCHAR(20) DEFAULT 'virement' NOT NULL,
                date_demande DATE NOT NULL,
                date_validation DATE NULL,
                date_paiement DATE NULL,
                notes TEXT NOT NULL,
                is_deleted BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                bailleur_id INTEGER NOT NULL,
                cree_par_id INTEGER NULL,
                valide_par_id INTEGER NULL,
                FOREIGN KEY (bailleur_id) REFERENCES proprietes_bailleur (id),
                FOREIGN KEY (cree_par_id) REFERENCES utilisateurs_utilisateur (id),
                FOREIGN KEY (valide_par_id) REFERENCES utilisateurs_utilisateur (id)
            )
        """)
        
        # Table RetraitQuittance
        cursor.execute("""
            CREATE TABLE paiements_retraitquittance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_quittance VARCHAR(50) UNIQUE NOT NULL,
                date_emission DATE NOT NULL,
                created_at DATETIME NOT NULL,
                retrait_id INTEGER UNIQUE NOT NULL,
                cree_par_id INTEGER NULL,
                FOREIGN KEY (retrait_id) REFERENCES paiements_retraitbailleur (id),
                FOREIGN KEY (cree_par_id) REFERENCES utilisateurs_utilisateur (id)
            )
        """)
        
        # Index
        cursor.execute("""
            CREATE INDEX paiements_r_bailleu_123456_idx 
            ON paiements_retraitbailleur (bailleur_id, mois_retrait)
        """)
        
        cursor.execute("""
            CREATE INDEX paiements_r_statut_123456_idx 
            ON paiements_retraitbailleur (statut)
        """)
        
        cursor.execute("""
            CREATE INDEX paiements_r_date_de_123456_idx 
            ON paiements_retraitbailleur (date_demande)
        """)
        
        print("Tables créées avec succès !")
        print("Vous pouvez maintenant tester le module des retraits.")

if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)
