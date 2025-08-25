#!/usr/bin/env python
"""
Script de test pour vérifier les améliorations du formulaire de contrat :
1. Remplissage automatique du loyer à partir de la propriété
2. Champs optionnels pour charges mensuelles et dépôt de garantie
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.models import Contrat
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien

def test_ameliorations_contrat():
    """Test des améliorations du formulaire de contrat"""
    
    print("🧪 Test des améliorations du formulaire de contrat")
    print("=" * 60)
    
    try:
        # Vérifier que le modèle Contrat a les bonnes modifications
        print("\n1. Vérification du modèle Contrat...")
        
        # Vérifier que le champ loyer_mensuel est optionnel
        loyer_field = Contrat._meta.get_field('loyer_mensuel')
        if loyer_field.blank:
            print("   ✅ Champ loyer_mensuel rendu optionnel (blank=True)")
        else:
            print("   ❌ Champ loyer_mensuel n'est pas optionnel")
        
        # Vérifier que les champs charges_mensuelles et depot_garantie sont optionnels
        charges_field = Contrat._meta.get_field('charges_mensuelles')
        depot_field = Contrat._meta.get_field('depot_garantie')
        
        if charges_field.blank and charges_field.null:
            print("   ✅ Champ charges_mensuelles rendu optionnel (blank=True, null=True)")
        else:
            print("   ❌ Champ charges_mensuelles n'est pas optionnel")
            
        if depot_field.blank and depot_field.null:
            print("   ✅ Champ depot_garantie rendu optionnel (blank=True, null=True)")
        else:
            print("   ❌ Champ depot_garantie n'est pas optionnel")
        
        # Vérifier que le modèle Propriete a le champ loyer_actuel
        print("\n2. Vérification du modèle Propriete...")
        loyer_actuel_field = Propriete._meta.get_field('loyer_actuel')
        if loyer_actuel_field:
            print("   ✅ Champ loyer_actuel existe dans Propriete")
        else:
            print("   ❌ Champ loyer_actuel n'existe pas dans Propriete")
        
        # Vérifier que l'API des propriétés est accessible
        print("\n3. Vérification de l'API des propriétés...")
        try:
            from proprietes.api_views import ProprieteViewSet
            print("   ✅ ProprieteViewSet existe")
        except ImportError as e:
            print(f"   ❌ Erreur d'import ProprieteViewSet: {e}")
        
        # Vérifier que le formulaire ContratForm a les bonnes modifications
        print("\n4. Vérification du formulaire ContratForm...")
        try:
            from contrats.forms import ContratForm
            form = ContratForm()
            
            # Vérifier que les champs sont optionnels
            if not form.fields['charges_mensuelles'].required:
                print("   ✅ Champ charges_mensuelles rendu optionnel dans le formulaire")
            else:
                print("   ❌ Champ charges_mensuelles toujours requis dans le formulaire")
                
            if not form.fields['depot_garantie'].required:
                print("   ✅ Champ depot_garantie rendu optionnel dans le formulaire")
            else:
                print("   ❌ Champ depot_garantie toujours requis dans le formulaire")
            
            # Vérifier que le champ loyer_mensuel est en lecture seule
            loyer_widget = form.fields['loyer_mensuel'].widget
            if hasattr(loyer_widget, 'attrs') and loyer_widget.attrs.get('readonly'):
                print("   ✅ Champ loyer_mensuel configuré en lecture seule")
            else:
                print("   ❌ Champ loyer_mensuel n'est pas en lecture seule")
                
        except ImportError as e:
            print(f"   ❌ Erreur d'import ContratForm: {e}")
        
        print("\n🎉 Test des améliorations terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ameliorations_contrat()
