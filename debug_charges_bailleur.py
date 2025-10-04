"""
Debug pour les charges bailleur.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def debug_charges_bailleur():
    """Debug des charges bailleur."""
    print("Debug des charges bailleur...")
    
    try:
        from proprietes.models import Propriete, Bailleur
        
        # Debug 1: Vérifier les propriétés
        print("1. Propriétés disponibles:")
        proprietes = Propriete.objects.filter(is_deleted=False).select_related('bailleur')
        print(f"   Nombre: {proprietes.count()}")
        
        for i, prop in enumerate(proprietes[:3]):
            print(f"   {i+1}. ID:{prop.id} - {prop.adresse} - Bailleur: {prop.bailleur.get_nom_complet() if prop.bailleur else 'Aucun'}")
        
        # Debug 2: Vérifier les bailleurs
        print("\n2. Bailleurs disponibles:")
        bailleurs = Bailleur.objects.all()
        print(f"   Nombre: {bailleurs.count()}")
        
        for i, bailleur in enumerate(bailleurs[:3]):
            print(f"   {i+1}. ID:{bailleur.id} - {bailleur.get_nom_complet()}")
        
        # Debug 3: Vérifier la relation
        print("\n3. Relation propriété-bailleur:")
        for prop in proprietes[:3]:
            if prop.bailleur:
                print(f"   {prop.adresse} -> {prop.bailleur.get_nom_complet()}")
            else:
                print(f"   {prop.adresse} -> Aucun bailleur")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale."""
    print("DEBUG CHARGES BAILLEUR")
    print("=" * 30)
    
    success = debug_charges_bailleur()
    
    if success:
        print("\nSUCCES - Debug terminé")
    else:
        print("\nERREUR - Debug échoué")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
