#!/usr/bin/env python
"""
Test d'import pour isoler le problème
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
    print("✅ Django setup successful")
    
    # Test d'import des modèles
    from paiements.models import Paiement
    print("✅ Paiement import successful")
    
    from paiements.models_avance import AvanceLoyer
    print("✅ AvanceLoyer import successful")
    
    from paiements.services_synchronisation_avances import ServiceSynchronisationAvances
    print("✅ ServiceSynchronisationAvances import successful")
    
    print("🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

