#!/usr/bin/env python3
"""
Script de test pour vérifier que tous les champs select des formulaires fonctionnent correctement
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from proprietes.forms import BailleurForm, LocataireForm, ProprieteForm
from contrats.forms import ContratForm
from paiements.forms import PaiementForm, ChargeDeductibleForm
from utilisateurs.forms import UtilisateurForm

def test_form_select_fields():
    """Teste que tous les champs select des formulaires ont les bonnes classes CSS"""
    
    print("🧪 Test des champs select dans les formulaires")
    print("=" * 50)
    
    # Liste des formulaires à tester
    forms_to_test = [
        ("BailleurForm", BailleurForm),
        ("LocataireForm", LocataireForm),
        ("ProprieteForm", ProprieteForm),
        ("ContratForm", ContratForm),
        ("PaiementForm", PaiementForm),
        ("ChargeDeductibleForm", ChargeDeductibleForm),
        ("UtilisateurForm", UtilisateurForm),
    ]
    
    total_forms = len(forms_to_test)
    forms_with_issues = []
    
    for form_name, form_class in forms_to_test:
        print(f"\n📋 Test de {form_name}...")
        
        try:
            # Créer une instance du formulaire
            form = form_class()
            
            # Vérifier les champs select
            select_fields = []
            for field_name, field in form.fields.items():
                if hasattr(field.widget, 'attrs') and 'class' in field.widget.attrs:
                    classes = field.widget.attrs['class']
                    if 'form-select' in classes or 'form-control' in classes:
                        select_fields.append((field_name, classes))
            
            if select_fields:
                print(f"   ✅ {len(select_fields)} champs select trouvés:")
                for field_name, classes in select_fields:
                    if 'form-select' in classes:
                        print(f"      ✅ {field_name}: {classes}")
                    else:
                        print(f"      ⚠️  {field_name}: {classes} (devrait être form-select)")
                        forms_with_issues.append((form_name, field_name, classes))
            else:
                print(f"   ℹ️  Aucun champ select trouvé")
                
        except Exception as e:
            print(f"   ❌ Erreur lors du test de {form_name}: {e}")
            forms_with_issues.append((form_name, "ERROR", str(e)))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    if forms_with_issues:
        print(f"⚠️  {len(forms_with_issues)} problèmes trouvés:")
        for form_name, field_name, issue in forms_with_issues:
            print(f"   - {form_name}.{field_name}: {issue}")
    else:
        print("✅ Tous les formulaires sont correctement configurés!")
    
    print(f"\n📈 Statistiques:")
    print(f"   - Formulaires testés: {total_forms}")
    print(f"   - Problèmes trouvés: {len(forms_with_issues)}")
    print(f"   - Taux de réussite: {((total_forms - len(forms_with_issues)) / total_forms * 100):.1f}%")
    
    return len(forms_with_issues) == 0

def test_css_files():
    """Teste que les fichiers CSS de correction existent"""
    
    print("\n🎨 Test des fichiers CSS de correction")
    print("=" * 50)
    
    css_files = [
        "static/css/fix_select_display.css",
    ]
    
    js_files = [
        "static/js/fix_select_display.js",
    ]
    
    all_files_exist = True
    
    for css_file in css_files:
        if os.path.exists(css_file):
            print(f"✅ {css_file} existe")
        else:
            print(f"❌ {css_file} manquant")
            all_files_exist = False
    
    for js_file in js_files:
        if os.path.exists(js_file):
            print(f"✅ {js_file} existe")
        else:
            print(f"❌ {js_file} manquant")
            all_files_exist = False
    
    return all_files_exist

def main():
    """Fonction principale de test"""
    
    print("🚀 DÉMARRAGE DES TESTS DES CHAMPS SELECT")
    print("=" * 60)
    
    # Test des formulaires
    forms_ok = test_form_select_fields()
    
    # Test des fichiers
    files_ok = test_css_files()
    
    # Résultat final
    print("\n" + "=" * 60)
    print("🏁 RÉSULTAT FINAL")
    print("=" * 60)
    
    if forms_ok and files_ok:
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print("🎉 Les champs select devraient maintenant afficher les options correctement.")
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("🔧 Veuillez corriger les problèmes identifiés ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
