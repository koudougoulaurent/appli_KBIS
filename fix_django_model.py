import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_with_char_fields():
    print("Testing with CharField approach...")
    
    try:
        # Import the model
        from contrats.models import Contrat
        
        # Create a temporary model with CharField for decimal fields
        from django.db import models
        
        class TempContrat(models.Model):
            id = models.IntegerField(primary_key=True)
            numero_contrat = models.CharField(max_length=50)
            loyer_mensuel = models.CharField(max_length=20)
            charges_mensuelles = models.CharField(max_length=20)
            depot_garantie = models.CharField(max_length=20)
            avance_loyer = models.CharField(max_length=20)
            
            class Meta:
                managed = False
                db_table = 'contrats_contrat'
        
        print("✅ Temporary model created")
        
        # Test access
        contracts = TempContrat.objects.all()
        print(f"✅ Contracts queryset created: {contracts.count()} contracts found")
        
        if contracts.exists():
            first_contract = contracts.first()
            print(f"✅ First contract accessed: {first_contract.numero_contrat}")
            print(f"  Loyer mensuel: {first_contract.loyer_mensuel}")
            print(f"  Charges mensuelles: {first_contract.charges_mensuelles}")
            print(f"  Depot garantie: {first_contract.depot_garantie}")
            print(f"  Avance loyer: {first_contract.avance_loyer}")
            
            print("✅ All fields accessed successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_direct_sql():
    print("\nTesting with direct SQL approach...")
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, numero_contrat, loyer_mensuel, charges_mensuelles, depot_garantie, avance_loyer FROM contrats_contrat LIMIT 5")
            contracts = cursor.fetchall()
            
            print(f"✅ Direct SQL successful: {len(contracts)} contracts found")
            
            for contract in contracts:
                contract_id, numero, loyer, charges, depot, avance = contract
                print(f"  Contract {contract_id} ({numero}):")
                print(f"    Loyer: {loyer}, Charges: {charges}, Depot: {depot}, Avance: {avance}")
            
            print("✅ Direct SQL access successful!")
            
    except Exception as e:
        print(f"❌ Direct SQL error: {e}")

if __name__ == "__main__":
    test_with_char_fields()
    test_direct_sql()
