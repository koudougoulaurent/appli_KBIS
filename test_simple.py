#!/usr/bin/env python
"""
Test simple pour vérifier la fonctionnalité type_gestion
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from proprietes.models import Propriete

def test_simple():
    """Test simple de la fonctionnalité"""
    print("=== Test simple de type_gestion ===\n")
    
    # Vérifier que le champ type_gestion existe
    print("1. Vérification du champ type_gestion...")
    try:
        # Créer une propriété de test
        propriete = Propriete(
            titre='Test Appartement',
            type_gestion='propriete_entiere'
        )
        print(f"   ✓ Champ type_gestion accepté: {propriete.type_gestion}")
        print(f"   ✓ Méthode est_propriete_entiere(): {propriete.est_propriete_entiere()}")
        print(f"   ✓ Méthode est_avec_unites_multiples(): {propriete.est_avec_unites_multiples()}")
        
        # Test avec l'autre type
        propriete2 = Propriete(
            titre='Test Colocation',
            type_gestion='unites_multiples'
        )
        print(f"   ✓ Type unites_multiples: {propriete2.type_gestion}")
        print(f"   ✓ est_propriete_entiere(): {propriete2.est_propriete_entiere()}")
        print(f"   ✓ est_avec_unites_multiples(): {propriete2.est_avec_unites_multiples()}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n2. Vérification des choix disponibles...")
    try:
        choices = Propriete.TYPE_GESTION_CHOICES
        print(f"   ✓ Choix disponibles: {len(choices)}")
        for choice in choices:
            print(f"   - {choice[0]}: {choice[1]}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n=== Test réussi ! ===")
    return True

if __name__ == '__main__':
    test_simple()
