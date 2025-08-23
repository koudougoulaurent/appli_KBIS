import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_fixed_model():
    print("Testing the fixed Django model...")
    
    try:
        from contrats.models import Contrat
        
        print("✅ Django setup successful")
        print("✅ Contrat model imported successfully")
        
        # Try to access contracts
        print("\nAttempting to access contracts...")
        contracts = Contrat.objects.all()
        print(f"✅ Contracts queryset created: {contracts.count()} contracts found")
        
        # Try to access the first contract
        if contracts.exists():
            first_contract = contracts.first()
            print(f"✅ First contract accessed: {first_contract.numero_contrat}")
            
            # Try to access the fields
            print(f"  Loyer mensuel: {first_contract.loyer_mensuel} (type: {type(first_contract.loyer_mensuel)})")
            print(f"  Charges mensuelles: {first_contract.charges_mensuelles} (type: {type(first_contract.charges_mensuelles)})")
            print(f"  Depot garantie: {first_contract.depot_garantie} (type: {type(first_contract.depot_garantie)})")
            print(f"  Avance loyer: {first_contract.avance_loyer} (type: {type(first_contract.avance_loyer)})")
            
            print("✅ All fields accessed successfully!")
            print("✅ The InvalidOperation error should be resolved!")
            
            # Test if we can iterate through all contracts
            print(f"\nTesting iteration through all contracts...")
            count = 0
            for contract in contracts:
                count += 1
                if count <= 3:  # Only show first 3
                    print(f"  Contract {count}: {contract.numero_contrat} - Loyer: {contract.loyer_mensuel}")
            
            print(f"✅ Successfully iterated through {count} contracts!")
            
        else:
            print("⚠️ No contracts found in database")
            
    except Exception as e:
        print(f"❌ Django access failed: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_model()
