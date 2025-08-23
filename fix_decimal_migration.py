import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def create_fix_migration():
    print("Creating a migration to fix decimal field types...")
    
    # Connect to SQLite database directly
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # First, let's check the current schema
        print("\n=== CURRENT SCHEMA ===")
        cursor.execute("PRAGMA table_info(contrats_contrat)")
        columns = cursor.fetchall()
        
        for col in columns:
            if 'loyer' in col[1] or 'charges' in col[1] or 'depot' in col[1] or 'avance' in col[1]:
                print(f"  {col[1]}: {col[2]} (type: {col[2]})")
        
        # The issue is that SQLite doesn't have a native decimal type
        # We need to change these to TEXT type so Django can handle them properly
        print("\n=== FIXING SCHEMA ===")
        
        # Create a temporary table with the correct schema
        cursor.execute("""
            CREATE TABLE contrats_contrat_temp (
                id INTEGER PRIMARY KEY,
                numero_contrat VARCHAR(50) NOT NULL UNIQUE,
                propriete_id INTEGER NOT NULL,
                locataire_id INTEGER NOT NULL,
                date_debut DATE NOT NULL,
                date_fin DATE NOT NULL,
                date_signature DATE NOT NULL,
                loyer_mensuel TEXT NOT NULL,
                charges_mensuelles TEXT NOT NULL DEFAULT '0.00',
                depot_garantie TEXT NOT NULL DEFAULT '0.00',
                avance_loyer TEXT NOT NULL DEFAULT '0.00',
                caution_payee BOOLEAN NOT NULL DEFAULT 0,
                avance_loyer_payee BOOLEAN NOT NULL DEFAULT 0,
                date_paiement_caution DATE,
                date_paiement_avance DATE,
                jour_paiement INTEGER NOT NULL DEFAULT 1,
                mode_paiement VARCHAR(20) NOT NULL DEFAULT 'virement',
                est_actif BOOLEAN NOT NULL DEFAULT 1,
                est_resilie BOOLEAN NOT NULL DEFAULT 0,
                date_resiliation DATE,
                motif_resiliation TEXT,
                date_creation DATETIME NOT NULL,
                date_modification DATETIME NOT NULL,
                notes TEXT,
                cree_par_id INTEGER,
                is_deleted BOOLEAN NOT NULL DEFAULT 0,
                deleted_at DATETIME,
                deleted_by_id INTEGER
            )
        """)
        
        print("  ✅ Temporary table created")
        
        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO contrats_contrat_temp 
            SELECT 
                id, numero_contrat, propriete_id, locataire_id, date_debut, date_fin, date_signature,
                loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer,
                caution_payee, avance_loyer_payee, date_paiement_caution, date_paiement_avance,
                jour_paiement, mode_paiement, est_actif, est_resilie, date_resiliation, motif_resiliation,
                date_creation, date_modification, notes, cree_par_id, is_deleted, deleted_at, deleted_by_id
            FROM contrats_contrat
        """)
        
        print("  ✅ Data copied to temporary table")
        
        # Drop the old table
        cursor.execute("DROP TABLE contrats_contrat")
        print("  ✅ Old table dropped")
        
        # Rename the temporary table
        cursor.execute("ALTER TABLE contrats_contrat_temp RENAME TO contrats_contrat")
        print("  ✅ Temporary table renamed")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX idx_contrats_propriete_date ON contrats_contrat(propriete_id, date_debut)")
        cursor.execute("CREATE INDEX contrats_contrat_deleted_by_id_b8ae96b9 ON contrats_contrat(deleted_by_id)")
        cursor.execute("CREATE INDEX contrats_contrat_propriete_id_8cc56521 ON contrats_contrat(propriete_id)")
        cursor.execute("CREATE INDEX contrats_contrat_locataire_id_715d7cc6 ON contrats_contrat(locataire_id)")
        cursor.execute("CREATE INDEX contrats_contrat_cree_par_id_800ca7fa ON contrats_contrat(cree_par_id)")
        cursor.execute("CREATE UNIQUE INDEX sqlite_autoindex_contrats_contrat_1 ON contrats_contrat(numero_contrat)")
        
        print("  ✅ Indexes recreated")
        
        # Now update the decimal values to proper format
        print("\n=== UPDATING DECIMAL VALUES ===")
        
        cursor.execute("SELECT id, loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer FROM contrats_contrat")
        contracts = cursor.fetchall()
        
        contracts_fixed = 0
        for contract in contracts:
            contract_id, loyer, charges, depot, avance = contract
            
            # Convert to proper decimal strings
            loyer_fixed = f"{loyer}.00" if isinstance(loyer, int) else str(loyer)
            charges_fixed = f"{charges}.00" if isinstance(charges, int) else str(charges)
            depot_fixed = f"{depot}.00" if isinstance(depot, int) else str(depot)
            avance_fixed = f"{avance}.00" if isinstance(avance, int) else str(avance)
            
            cursor.execute("""
                UPDATE contrats_contrat 
                SET loyer_mensuel = ?, charges_mensuelles = ?, depot_garantie = ?, avance_loyer = ?
                WHERE id = ?
            """, (loyer_fixed, charges_fixed, depot_fixed, avance_fixed, contract_id))
            
            contracts_fixed += 1
            print(f"  Fixed contract {contract_id}: {loyer} -> {loyer_fixed}")
        
        print(f"  ✅ {contracts_fixed} contracts fixed")
        
        # Commit changes
        conn.commit()
        print(f"\n✅ All changes committed to database")
        
        # Verify the new schema
        print("\n=== NEW SCHEMA ===")
        cursor.execute("PRAGMA table_info(contrats_contrat)")
        columns = cursor.fetchall()
        
        for col in columns:
            if 'loyer' in col[1] or 'charges' in col[1] or 'depot' in col[1] or 'avance' in col[1]:
                print(f"  {col[1]}: {col[2]} (type: {col[2]})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_django_access():
    print("\n=== TESTING DJANGO ACCESS ===")
    
    try:
        from contrats.models import Contrat
        
        print("  Testing Django model access...")
        contracts = Contrat.objects.all()
        print(f"  Total contracts: {contracts.count()}")
        
        # Try to access the first contract
        if contracts.exists():
            first_contract = contracts.first()
            print(f"  First contract: {first_contract.numero_contrat}")
            print(f"  Loyer mensuel: {first_contract.loyer_mensuel} (type: {type(first_contract.loyer_mensuel)})")
            print(f"  Charges mensuelles: {first_contract.charges_mensuelles} (type: {type(first_contract.charges_mensuelles)})")
            print(f"  Depot garantie: {first_contract.depot_garantie} (type: {type(first_contract.depot_garantie)})")
            print(f"  Avance loyer: {first_contract.avance_loyer} (type: {type(first_contract.avance_loyer)})")
            print("  ✅ Django model access successful!")
        else:
            print("  No contracts found")
            
    except Exception as e:
        print(f"  ❌ Django model access failed: {e}")

if __name__ == "__main__":
    print("Script to fix decimal field types by recreating the table schema")
    print("=" * 70)
    
    # First, fix the schema
    create_fix_migration()
    
    # Then, test Django access
    test_django_access()
    
    print("\n✅ Script completed. Try accessing the contracts list page now.")
