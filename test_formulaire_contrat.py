#!/usr/bin/env python
"""
Script de test pour vérifier que le formulaire de contrat fonctionne avec le remplissage automatique du loyer
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.forms import ContratForm
from proprietes.models import Propriete

def test_formulaire_contrat():
    """Test du formulaire de contrat avec remplissage automatique du loyer"""
    
    print("🧪 Test du formulaire de contrat avec remplissage automatique du loyer")
    print("=" * 70)
    
    try:
        # 1. Créer le formulaire
        print("\n1. Création du formulaire...")
        form = ContratForm()
        print("   ✅ Formulaire créé avec succès")
        
        # 2. Vérifier les données des propriétés
        print("\n2. Vérification des données des propriétés...")
        if hasattr(form, 'proprietes_data'):
            print(f"   ✅ Données des propriétés disponibles : {len(form.proprietes_data)} propriétés")
            
            for prop_id, prop_data in form.proprietes_data.items():
                print(f"      - ID {prop_id}: {prop_data['titre']} - Loyer: {prop_data['loyer']} XOF")
        else:
            print("   ❌ Données des propriétés non disponibles")
        
        # 3. Vérifier que les champs sont optionnels
        print("\n3. Vérification des champs optionnels...")
        
        if not form.fields['charges_mensuelles'].required:
            print("   ✅ Champ charges_mensuelles rendu optionnel")
        else:
            print("   ❌ Champ charges_mensuelles toujours requis")
            
        if not form.fields['depot_garantie'].required:
            print("   ✅ Champ depot_garantie rendu optionnel")
        else:
            print("   ❌ Champ depot_garantie toujours requis")
        
        # 4. Vérifier que le champ loyer est en lecture seule
        print("\n4. Vérification du champ loyer...")
        loyer_widget = form.fields['loyer_mensuel'].widget
        if hasattr(loyer_widget, 'attrs') and loyer_widget.attrs.get('readonly'):
            print("   ✅ Champ loyer_mensuel configuré en lecture seule")
        else:
            print("   ❌ Champ loyer_mensuel n'est pas en lecture seule")
        
        # 5. Vérifier qu'il y a des propriétés disponibles
        print("\n5. Vérification des propriétés disponibles...")
        proprietes_disponibles = Propriete.objects.filter(disponible=True)
        print(f"   ✅ {proprietes_disponibles.count()} propriétés disponibles")
        
        if proprietes_disponibles.exists():
            for prop in proprietes_disponibles:
                print(f"      - {prop.titre} (ID: {prop.id}) - Loyer: {prop.loyer_actuel} XOF")
        
        print("\n🎉 Test du formulaire terminé avec succès !")
        print("\n📋 Pour tester le remplissage automatique :")
        print("   1. Allez sur http://localhost:8000/contrats/ajouter/")
        print("   2. Sélectionnez une propriété dans le formulaire")
        print("   3. Le champ loyer devrait se remplir automatiquement")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_formulaire_contrat()
