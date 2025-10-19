#!/usr/bin/env python
"""
Test minimal pour isoler le problème d'import
"""
import os
import sys

# Configuration Django minimale
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

print("🔍 Test d'import minimal...")

try:
    # Test 1: Import Django de base
    import django
    print("✅ Django import successful")
    
    # Test 2: Configuration Django
    django.setup()
    print("✅ Django setup successful")
    
    # Test 3: Import des apps de base
    from django.contrib.auth.models import User
    print("✅ User model import successful")
    
    # Test 4: Import des apps personnalisées une par une
    from core.models import Entreprise
    print("✅ Core models import successful")
    
    from utilisateurs.models import Utilisateur
    print("✅ Utilisateurs models import successful")
    
    from proprietes.models import Propriete
    print("✅ Proprietes models import successful")
    
    from contrats.models import Contrat
    print("✅ Contrats models import successful")
    
    from paiements.models import Paiement
    print("✅ Paiements models import successful")
    
    print("🎉 Tous les imports réussis!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

