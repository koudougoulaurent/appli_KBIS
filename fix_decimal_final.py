import sqlite3

def fix_decimal_final():
    print("Fixing decimal values with proper SQLite handling...")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Fix contracts table - use proper decimal format for SQLite
        print("\n=== FIXING CONTRATS TABLE ===")
        
        # Get all contracts
        cursor.execute("SELECT id, loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer FROM contrats_contrat")
        contracts = cursor.fetchall()
        
        contracts_fixed = 0
        for contract in contracts:
            contract_id, loyer, charges, depot, avance = contract
            
            # Convert integer values to proper decimal strings with explicit decimal point
            loyer_fixed = f"{loyer}.00" if isinstance(loyer, int) else str(loyer)
            charges_fixed = f"{charges}.00" if isinstance(charges, int) else str(charges)
            depot_fixed = f"{depot}.00" if isinstance(depot, int) else str(depot)
            avance_fixed = f"{avance}.00" if isinstance(avance, int) else str(avance)
            
            # Update the database with explicit decimal strings
            cursor.execute("""
                UPDATE contrats_contrat 
                SET loyer_mensuel = ?, charges_mensuelles = ?, depot_garantie = ?, avance_loyer = ?
                WHERE id = ?
            """, (loyer_fixed, charges_fixed, depot_fixed, avance_fixed, contract_id))
            
            contracts_fixed += 1
            print(f"  Fixed contract {contract_id}: {loyer} -> {loyer_fixed}")
        
        print(f"  ✅ {contracts_fixed} contracts fixed")
        
        # Fix properties table
        print("\n=== FIXING PROPRIETES TABLE ===")
        
        # Check what decimal columns exist
        cursor.execute("PRAGMA table_info(proprietes_propriete)")
        columns = cursor.fetchall()
        
        decimal_columns = []
        for col in columns:
            if 'loyer' in col[1].lower() or 'prix' in col[1].lower() or 'charges' in col[1].lower():
                decimal_columns.append(col[1])
        
        if decimal_columns:
            print(f"  Decimal columns found: {decimal_columns}")
            
            # Get properties data
            select_cols = ', '.join(['id'] + decimal_columns)
            cursor.execute(f"SELECT {select_cols} FROM proprietes_propriete")
            properties = cursor.fetchall()
            
            properties_fixed = 0
            for prop in properties:
                prop_id = prop[0]
                values = prop[1:]
                
                # Prepare update values
                update_values = []
                for i, value in enumerate(values):
                    if isinstance(value, int):
                        fixed_value = f"{value}.00"
                    else:
                        fixed_value = str(value) if value else "0.00"
                    update_values.append(fixed_value)
                
                # Build update query
                set_clause = ', '.join([f"{col} = ?" for col in decimal_columns])
                cursor.execute(f"UPDATE proprietes_propriete SET {set_clause} WHERE id = ?", 
                             update_values + [prop_id])
                
                properties_fixed += 1
                print(f"  Fixed property {prop_id}")
            
            print(f"  ✅ {properties_fixed} properties fixed")
        
        # Fix payments table
        print("\n=== FIXING PAIEMENTS TABLE ===")
        
        cursor.execute("SELECT id, montant FROM paiements_paiement")
        payments = cursor.fetchall()
        
        payments_fixed = 0
        for payment in payments:
            payment_id, montant = payment
            
            if isinstance(montant, int):
                montant_fixed = f"{montant}.00"
                
                cursor.execute("UPDATE paiements_paiement SET montant = ? WHERE id = ?", 
                             (montant_fixed, payment_id))
                
                payments_fixed += 1
                print(f"  Fixed payment {payment_id}: {montant} -> {montant_fixed}")
        
        print(f"  ✅ {payments_fixed} payments fixed")
        
        # Commit changes
        conn.commit()
        print(f"\n✅ All changes committed to database")
        
        total_fixed = contracts_fixed + properties_fixed + payments_fixed
        print(f"✅ Total records fixed: {total_fixed}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_fixes():
    print("\n=== VERIFYING FIXES ===")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check contracts table with raw values
        print("\nChecking contracts table...")
        cursor.execute("SELECT id, loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer FROM contrats_contrat LIMIT 5")
        contracts = cursor.fetchall()
        
        for contract in contracts:
            contract_id, loyer, charges, depot, avance = contract
            print(f"  Contract {contract_id}:")
            print(f"    loyer_mensuel: '{loyer}' (raw: {repr(loyer)})")
            print(f"    charges_mensuelles: '{charges}' (raw: {repr(charges)})")
            print(f"    depot_garantie: '{depot}' (raw: {repr(depot)})")
            print(f"    avance_loyer: '{avance}' (raw: {repr(avance)})")
            
            # Check if values are now proper decimal strings
            if isinstance(loyer, str) and '.' in loyer:
                print(f"    ✅ loyer_mensuel is properly formatted")
            else:
                print(f"    ❌ loyer_mensuel still needs fixing")
        
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        conn.close()

def test_django_access():
    print("\n=== TESTING DJANGO ACCESS ===")
    
    try:
        import os
        import django
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
        django.setup()
        
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
    print("Script to fix decimal field values with proper SQLite handling")
    print("=" * 70)
    
    # First, fix the values
    fix_decimal_final()
    
    # Then, verify the fixes
    verify_fixes()
    
    # Finally, test Django access
    test_django_access()
    
    print("\n✅ Script completed. Try accessing the contracts list page now.")
