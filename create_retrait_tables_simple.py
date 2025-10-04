#!/usr/bin/env python
"""
Script simple pour créer les tables des retraits
"""
import sqlite3
import os

def create_tables():
    """Crée les tables des retraits directement en SQL"""
    
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print("Base de données non trouvée !")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Table RetraitBailleur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paiements_retraitbailleur (
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
            CREATE TABLE IF NOT EXISTS paiements_retraitquittance (
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
            CREATE INDEX IF NOT EXISTS paiements_r_bailleu_123456_idx 
            ON paiements_retraitbailleur (bailleur_id, mois_retrait)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS paiements_r_statut_123456_idx 
            ON paiements_retraitbailleur (statut)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS paiements_r_date_de_123456_idx 
            ON paiements_retraitbailleur (date_demande)
        """)
        
        conn.commit()
        print("Tables des retraits creees avec succes !")
        print("Table paiements_retraitbailleur creee")
        print("Table paiements_retraitquittance creee")
        print("Index crees")
        
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
