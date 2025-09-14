#!/usr/bin/env python
"""
Script pour corriger le problème des types de biens manquants sur PythonAnywhere.
Ce script ajoute les types de biens de base s'ils n'existent pas déjà.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_pythonanywhere')
django.setup()

from proprietes.models import TypeBien

def create_types_bien():
    """Crée les types de biens de base s'ils n'existent pas."""
    print("🏠 Vérification et création des types de biens...")
    
    types_data = [
        {'nom': 'Appartement', 'description': 'Appartement en immeuble'},
        {'nom': 'Maison', 'description': 'Maison individuelle'},
        {'nom': 'Studio', 'description': 'Studio meublé'},
        {'nom': 'Loft', 'description': 'Loft industriel'},
        {'nom': 'Villa', 'description': 'Villa avec jardin'},
        {'nom': 'Duplex', 'description': 'Duplex sur deux niveaux'},
        {'nom': 'Penthouse', 'description': 'Penthouse de luxe'},
        {'nom': 'Château', 'description': 'Château ou manoir'},
        {'nom': 'Ferme', 'description': 'Ferme ou propriété rurale'},
        {'nom': 'Bureau', 'description': 'Local commercial ou bureau'},
        {'nom': 'Commerce', 'description': 'Local commercial'},
        {'nom': 'Entrepôt', 'description': 'Entrepôt ou local industriel'},
        {'nom': 'Garage', 'description': 'Garage ou parking'},
        {'nom': 'Terrain', 'description': 'Terrain constructible'},
        {'nom': 'Autre', 'description': 'Autre type de bien'},
    ]
    
    types_crees = []
    types_existants = []
    
    for type_data in types_data:
        type_bien, created = TypeBien.objects.get_or_create(
            nom=type_data['nom'],
            defaults=type_data
        )
        if created:
            types_crees.append(type_bien)
            print(f"✅ Type créé: {type_bien.nom}")
        else:
            types_existants.append(type_bien)
            print(f"ℹ️  Type existant: {type_bien.nom}")
    
    print(f"\n📊 Résumé:")
    print(f"   - Types créés: {len(types_crees)}")
    print(f"   - Types existants: {len(types_existants)}")
    print(f"   - Total dans la base: {TypeBien.objects.count()}")
    
    return TypeBien.objects.all()

def main():
    """Fonction principale."""
    print("🚀 CORRECTION DES TYPES DE BIENS SUR PYTHONANYWHERE")
    print("=" * 60)
    
    try:
        # Vérifier l'état actuel
        count_avant = TypeBien.objects.count()
        print(f"📈 Types de biens existants avant: {count_avant}")
        
        # Créer les types manquants
        types_bien = create_types_bien()
        
        count_apres = TypeBien.objects.count()
        print(f"📈 Types de biens après: {count_apres}")
        
        if count_apres > count_avant:
            print(f"\n🎉 SUCCÈS ! {count_apres - count_avant} nouveaux types de biens ajoutés.")
        else:
            print(f"\n✅ Tous les types de biens étaient déjà présents.")
        
        print(f"\n📋 Liste des types de biens disponibles:")
        for type_bien in types_bien:
            print(f"   - {type_bien.nom}: {type_bien.description}")
        
        print(f"\n🌐 Votre formulaire d'ajout de propriétés devrait maintenant fonctionner correctement !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
