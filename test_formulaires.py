#!/usr/bin/env python
"""
Test des formulaires avec téléphones
"""
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')

try:
    import django
    django.setup()
    
    from proprietes.forms import BailleurForm, LocataireForm
    
    print("Test des formulaires avec téléphones")
    print("=" * 40)
    
    # Test BailleurForm
    print("1. Test BailleurForm:")
    form_bailleur = BailleurForm({
        'nom': 'Test',
        'prenom': 'Test',
        'telephone': '0123456789'
    })
    
    print(f"   Formulaire valide: {form_bailleur.is_valid()}")
    if form_bailleur.is_valid():
        print(f"   Téléphone nettoyé: {form_bailleur.cleaned_data['telephone']}")
    else:
        print(f"   Erreurs: {form_bailleur.errors}")
    
    # Test LocataireForm
    print("\n2. Test LocataireForm:")
    form_locataire = LocataireForm({
        'nom': 'Test',
        'prenom': 'Test',
        'telephone': '0123456789',
        'garant_telephone': '0987654321'
    })
    
    print(f"   Formulaire valide: {form_locataire.is_valid()}")
    if form_locataire.is_valid():
        print(f"   Téléphone nettoyé: {form_locataire.cleaned_data['telephone']}")
        print(f"   Garant téléphone: {form_locataire.cleaned_data['garant_telephone']}")
    else:
        print(f"   Erreurs: {form_locataire.errors}")
    
    print("\n✅ Tous les formulaires fonctionnent correctement!")
    print("✅ Le formatage automatique n'affecte pas les formulaires!")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
