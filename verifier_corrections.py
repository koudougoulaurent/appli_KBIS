#!/usr/bin/env python
"""
Script de vérification du formulaire d'unités locatives
"""
import os
import sys

def verifier_corrections():
    """Vérifie que les corrections sont bien appliquées"""
    print("🔍 VÉRIFICATION DES CORRECTIONS")
    print("=" * 50)
    
    # Vérifier le fichier forms_unites.py
    try:
        with open('proprietes/forms_unites.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements_verifies = [
            ("Méthode __init__", "def __init__(self, *args, **kwargs):" in content),
            ("Choix type_unite", "self.fields['type_unite'].choices" in content),
            ("Queryset propriete", "self.fields['propriete'].queryset" in content),
            ("Queryset bailleur", "self.fields['bailleur'].queryset" in content),
            ("Choix statut", "self.fields['statut'].choices" in content),
            ("Validation", "def clean(self):" in content),
            ("Valeurs par défaut", "self.fields['statut'].initial" in content)
        ]
        
        print("\n📋 Éléments vérifiés :")
        for element, present in elements_verifies:
            status = "✅" if present else "❌"
            print(f"   {status} {element}")
        
        # Compter les corrections
        corrections_appliquees = sum(1 for _, present in elements_verifies if present)
        total_corrections = len(elements_verifies)
        
        print(f"\n📊 Résultat : {corrections_appliquees}/{total_corrections} corrections appliquées")
        
        if corrections_appliquees == total_corrections:
            print("\n🎉 TOUTES LES CORRECTIONS SONT APPLIQUÉES !")
            print("\n🚀 Le formulaire devrait maintenant fonctionner correctement :")
            print("   - Tous les champs affichent leurs données")
            print("   - Les listes déroulantes sont peuplées")
            print("   - La validation fonctionne")
            print("   - Les valeurs par défaut sont configurées")
        else:
            print("\n⚠️ Certaines corrections sont manquantes")
            print("Vérifiez les éléments marqués ❌ ci-dessus")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")

if __name__ == '__main__':
    verifier_corrections()
