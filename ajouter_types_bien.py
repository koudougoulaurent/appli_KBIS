#!/usr/bin/env python
"""
Script simple pour ajouter les types de biens sur Render
Exécuter avec: python ajouter_types_bien.py
"""

import os
import django

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import TypeBien

# Types de biens à ajouter
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

print("🏠 Ajout des types de biens...")
print("=" * 40)

types_crees = 0
types_existants = 0

for type_data in types_data:
    type_bien, created = TypeBien.objects.get_or_create(
        nom=type_data['nom'],
        defaults=type_data
    )
    if created:
        types_crees += 1
        print(f"✅ Créé: {type_bien.nom}")
    else:
        types_existants += 1
        print(f"ℹ️  Existant: {type_bien.nom}")

print("=" * 40)
print(f"📊 Résultat:")
print(f"   - Nouveaux types: {types_crees}")
print(f"   - Types existants: {types_existants}")
print(f"   - Total en base: {TypeBien.objects.count()}")

if types_crees > 0:
    print(f"\n🎉 SUCCÈS ! {types_crees} types ajoutés.")
else:
    print(f"\n✅ Tous les types étaient déjà présents.")

print(f"\n🌐 Le formulaire d'ajout de propriétés devrait maintenant fonctionner !")
