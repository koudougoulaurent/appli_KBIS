#!/usr/bin/env python
"""Script de debug pour tester les apps après avoir défini le module de settings"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test des apps après définition du module de settings...")

# Définir le module de settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    print("1. Test import core...")
    import core
    print("   ✅ Core importé")
except Exception as e:
    print(f"   ❌ Erreur core: {e}")

try:
    print("2. Test import core.models...")
    from core.models import Devise
    print("   ✅ Devise importé")
except Exception as e:
    print(f"   ❌ Erreur Devise: {e}")

try:
    print("3. Test import proprietes...")
    import proprietes
    print("   ✅ Proprietes importé")
except Exception as e:
    print(f"   ❌ Erreur proprietes: {e}")

try:
    print("4. Test import proprietes.models...")
    from proprietes.models import Locataire
    print("   ✅ Locataire importé")
except Exception as e:
    print(f"   ❌ Erreur Locataire: {e}")

try:
    print("5. Test import paiements...")
    import paiements
    print("   ✅ Paiements importé")
except Exception as e:
    print(f"   ❌ Erreur paiements: {e}")

try:
    print("6. Test import paiements.models...")
    from paiements.models import Paiement
    print("   ✅ Paiement importé")
except Exception as e:
    print(f"   ❌ Erreur Paiement: {e}")

print("✅ Tests terminés")
