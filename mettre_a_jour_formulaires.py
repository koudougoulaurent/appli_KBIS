#!/usr/bin/env python
"""
Script pour mettre à jour tous les formulaires afin qu'ils utilisent les nouveaux champs numero_* 
et le système de génération d'IDs uniques
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def mettre_a_jour_formulaires():
    """Met à jour tous les formulaires pour utiliser les nouveaux champs numero_*"""
    
    print("🔧 MISE À JOUR DES FORMULAIRES POUR LES NOUVEAUX IDS UNIQUES")
    print("=" * 70)
    
    # 1. Mettre à jour le formulaire ProprieteForm
    print("\n🏠 MISE À JOUR DU FORMULAIRE PROPRIETE")
    print("-" * 40)
    
    try:
        from proprietes.forms import ProprieteForm
        
        # Ajouter le champ numero_propriete au formulaire
        if 'numero_propriete' not in ProprieteForm.Meta.fields:
            ProprieteForm.Meta.fields.insert(0, 'numero_propriete')
            print("✅ Champ numero_propriete ajouté au formulaire ProprieteForm")
        else:
            print("✅ Champ numero_propriete déjà présent dans ProprieteForm")
            
        # Ajouter le widget pour numero_propriete
        if 'numero_propriete' not in ProprieteForm.Meta.widgets:
            ProprieteForm.Meta.widgets['numero_propriete'] = forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement'
            })
            print("✅ Widget pour numero_propriete ajouté")
        else:
            print("✅ Widget pour numero_propriete déjà présent")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de ProprieteForm: {e}")
    
    # 2. Mettre à jour le formulaire BailleurForm
    print("\n👤 MISE À JOUR DU FORMULAIRE BAİLLEUR")
    print("-" * 40)
    
    try:
        from proprietes.forms import BailleurForm
        
        # Remplacer code_bailleur par numero_bailleur
        if 'code_bailleur' in BailleurForm.Meta.fields:
            index = BailleurForm.Meta.fields.index('code_bailleur')
            BailleurForm.Meta.fields[index] = 'numero_bailleur'
            print("✅ Champ code_bailleur remplacé par numero_bailleur")
        else:
            # Ajouter numero_bailleur au début si pas de code_bailleur
            if 'numero_bailleur' not in BailleurForm.Meta.fields:
                BailleurForm.Meta.fields.insert(0, 'numero_bailleur')
                print("✅ Champ numero_bailleur ajouté au formulaire BailleurForm")
            else:
                print("✅ Champ numero_bailleur déjà présent dans BailleurForm")
        
        # Ajouter le widget pour numero_bailleur
        if 'numero_bailleur' not in BailleurForm.Meta.widgets:
            BailleurForm.Meta.widgets['numero_bailleur'] = forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement'
            })
            print("✅ Widget pour numero_bailleur ajouté")
        else:
            print("✅ Widget pour numero_bailleur déjà présent")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de BailleurForm: {e}")
    
    # 3. Mettre à jour le formulaire LocataireForm
    print("\n👥 MISE À JOUR DU FORMULAIRE LOCATAIRE")
    print("-" * 40)
    
    try:
        from proprietes.forms import LocataireForm
        
        # Remplacer code_locataire par numero_locataire
        if 'code_locataire' in LocataireForm.Meta.fields:
            index = LocataireForm.Meta.fields.index('code_locataire')
            LocataireForm.Meta.fields[index] = 'numero_locataire'
            print("✅ Champ code_locataire remplacé par numero_locataire")
        else:
            # Ajouter numero_locataire au début si pas de code_locataire
            if 'numero_locataire' not in LocataireForm.Meta.fields:
                LocataireForm.Meta.fields.insert(0, 'numero_locataire')
                print("✅ Champ numero_locataire ajouté au formulaire LocataireForm")
            else:
                print("✅ Champ numero_locataire déjà présent dans LocataireForm")
        
        # Ajouter le widget pour numero_locataire
        if 'numero_locataire' not in LocataireForm.Meta.widgets:
            LocataireForm.Meta.widgets['numero_locataire'] = forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement'
            })
            print("✅ Widget pour numero_locataire ajouté")
        else:
            print("✅ Widget pour numero_locataire déjà présent")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de LocataireForm: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 PROCHAINES ÉTAPES:")
    print("1. Modifier manuellement les formulaires dans proprietes/forms.py")
    print("2. Mettre à jour les vues pour générer automatiquement les IDs")
    print("3. Tester la création de nouveaux enregistrements")
    print("=" * 70)

if __name__ == '__main__':
    mettre_a_jour_formulaires()
