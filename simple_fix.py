import sqlite3

def fix_decimal_issue():
    print("Fixing decimal field issue by changing column types...")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Change decimal columns to TEXT type
        print("Changing loyer_mensuel to TEXT...")
        cursor.execute("ALTER TABLE contrats_contrat ADD COLUMN loyer_mensuel_new TEXT")
        cursor.execute("UPDATE contrats_contrat SET loyer_mensuel_new = loyer_mensuel || '.00'")
        cursor.execute("ALTER TABLE contrats_contrat DROP COLUMN loyer_mensuel")
        cursor.execute("ALTER TABLE contrats_contrat RENAME COLUMN loyer_mensuel_new TO loyer_mensuel")
        
        print("Changing charges_mensuelles to TEXT...")
        cursor.execute("ALTER TABLE contrats_contrat ADD COLUMN charges_mensuelles_new TEXT")
        cursor.execute("UPDATE contrats_contrat SET charges_mensuelles_new = charges_mensuelles || '.00'")
        cursor.execute("ALTER TABLE contrats_contrat DROP COLUMN charges_mensuelles")
        cursor.execute("ALTER TABLE contrats_contrat RENAME COLUMN charges_mensuelles_new TO charges_mensuelles")
        
        print("Changing depot_garantie to TEXT...")
        cursor.execute("ALTER TABLE contrats_contrat ADD COLUMN depot_garantie_new TEXT")
        cursor.execute("UPDATE contrats_contrat SET depot_garantie_new = depot_garantie || '.00'")
        cursor.execute("ALTER TABLE contrats_contrat DROP COLUMN depot_garantie")
        cursor.execute("ALTER TABLE contrats_contrat RENAME COLUMN depot_garantie_new TO depot_garantie")
        
        print("Changing avance_loyer to TEXT...")
        cursor.execute("ALTER TABLE contrats_contrat ADD COLUMN avance_loyer_new TEXT")
        cursor.execute("UPDATE contrats_contrat SET avance_loyer_new = avance_loyer || '.00'")
        cursor.execute("ALTER TABLE contrats_contrat DROP COLUMN avance_loyer")
        cursor.execute("ALTER TABLE contrats_contrat RENAME COLUMN avance_loyer_new TO avance_loyer")
        
        conn.commit()
        print("✅ All columns changed to TEXT type")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_decimal_issue()
