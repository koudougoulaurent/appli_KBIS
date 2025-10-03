#!/usr/bin/env python
"""
Test simple du formulaire d'unités locatives
"""
import os
import sys

# Ajouter le répertoire du projet au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration Django minimale
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    import django
    django.setup()
    
    from proprietes.forms_unites import UniteLocativeForm
    
    print("🔧 Test du formulaire d'unités locatives")
    print("=" * 50)
    
    # Créer le formulaire
    form = UniteLocativeForm()
    
    print("✅ Formulaire créé avec succès")
    
    # Vérifier le champ type_unite
    print(f"\n📋 Champ type_unite :")
    print(f"   - Type : {type(form.fields['type_unite']).__name__}")
    print(f"   - Choix disponibles : {len(form.fields['type_unite'].choices)}")
    
    for choice in form.fields['type_unite'].choices:
        print(f"     - {choice[0]}: {choice[1]}")
    
    # Vérifier le champ propriete
    print(f"\n🏢 Champ propriete :")
    print(f"   - Type : {type(form.fields['propriete']).__name__}")
    print(f"   - Queryset : {form.fields['propriete'].queryset.count()} éléments")
    
    # Vérifier le champ bailleur
    print(f"\n👤 Champ bailleur :")
    print(f"   - Type : {type(form.fields['bailleur']).__name__}")
    print(f"   - Queryset : {form.fields['bailleur'].queryset.count()} éléments")
    
    print("\n✅ Test terminé avec succès !")
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()
