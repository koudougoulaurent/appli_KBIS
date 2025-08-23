import sqlite3

def check_raw_db():
    print("Checking raw database values...")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check contracts table with raw values
        print("\n=== RAW CONTRACTS TABLE VALUES ===")
        cursor.execute("SELECT id, numero_contrat, loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer FROM contrats_contrat LIMIT 5")
        contracts = cursor.fetchall()
        
        for contract in contracts:
            contract_id, numero, loyer, charges, depot, avance = contract
            print(f"\nContract {contract_id} ({numero}):")
            print(f"  loyer_mensuel: '{loyer}' (raw: {repr(loyer)})")
            print(f"  charges_mensuelles: '{charges}' (raw: {repr(charges)})")
            print(f"  depot_garantie: '{depot}' (raw: {repr(depot)})")
            print(f"  avance_loyer: '{avance}' (raw: {repr(avance)})")
        
        # Check the actual SQL schema and constraints
        print("\n=== TABLE SCHEMA DETAILS ===")
        cursor.execute("PRAGMA table_info(contrats_contrat)")
        columns = cursor.fetchall()
        
        for col in columns:
            if 'loyer' in col[1] or 'charges' in col[1] or 'depot' in col[1] or 'avance' in col[1]:
                print(f"  {col[1]}: {col[2]} (notnull: {col[3]}, default: {col[4]}, pk: {col[5]})")
        
        # Check if there are any constraints
        print("\n=== TABLE CONSTRAINTS ===")
        cursor.execute("PRAGMA index_list(contrats_contrat)")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  Index: {idx}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_raw_db()
