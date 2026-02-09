"""
Script pour ajouter manuellement le champ est_saisie_manuelle_historique à la base SQLite
"""
import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(paiements_paiement)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'est_saisie_manuelle_historique' in columns:
        print("✅ La colonne 'est_saisie_manuelle_historique' existe déjà!")
    else:
        # Ajouter la colonne
        cursor.execute("""
            ALTER TABLE paiements_paiement 
            ADD COLUMN est_saisie_manuelle_historique INTEGER DEFAULT 0 NOT NULL
        """)
        conn.commit()
        print("✅ Colonne 'est_saisie_manuelle_historique' ajoutée avec succès!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    conn.rollback()
finally:
    conn.close()
