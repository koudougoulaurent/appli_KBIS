import sqlite3

def verify_fix():
    print("Verifying that the decimal field fix worked...")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check the new schema
        print("\n=== NEW SCHEMA ===")
        cursor.execute("PRAGMA table_info(contrats_contrat)")
        columns = cursor.fetchall()
        
        for col in columns:
            if 'loyer' in col[1] or 'charges' in col[1] or 'depot' in col[1] or 'avance' in col[1]:
                print(f"  {col[1]}: {col[2]} (type: {col[2]})")
        
        # Check the actual values
        print("\n=== ACTUAL VALUES ===")
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
            if isinstance(loyer, str) and '.' in loyer:
                print(f"    ✅ loyer_mensuel is properly formatted")
            else:
                print(f"    ❌ loyer_mensuel still needs fixing")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_fix()
