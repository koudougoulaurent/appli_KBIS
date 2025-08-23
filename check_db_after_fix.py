import sqlite3

def check_db_after_fix():
    print("Checking database after fix...")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check contracts table
        print("\n=== CONTRATS TABLE (after fix) ===")
        cursor.execute("SELECT id, numero_contrat, loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer FROM contrats_contrat LIMIT 5")
        contracts = cursor.fetchall()
        
        for contract in contracts:
            contract_id, numero, loyer, charges, depot, avance = contract
            print(f"\nContract {contract_id} ({numero}):")
            print(f"  loyer_mensuel: '{loyer}' (type: {type(loyer)})")
            print(f"  charges_mensuelles: '{charges}' (type: {type(charges)})")
            print(f"  depot_garantie: '{depot}' (type: {type(depot)})")
            print(f"  avance_loyer: '{avance}' (type: {type(avance)})")
            
            # Check if values are now strings
            if isinstance(loyer, str):
                print(f"    ✅ loyer_mensuel is now a string")
            else:
                print(f"    ❌ loyer_mensuel is still {type(loyer)}")
        
        # Check the actual SQL schema
        print("\n=== TABLE SCHEMA ===")
        cursor.execute("PRAGMA table_info(contrats_contrat)")
        columns = cursor.fetchall()
        
        for col in columns:
            if 'loyer' in col[1] or 'charges' in col[1] or 'depot' in col[1] or 'avance' in col[1]:
                print(f"  {col[1]}: {col[2]} (type: {col[2]})")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db_after_fix()
