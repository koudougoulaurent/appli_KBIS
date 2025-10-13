#!/usr/bin/env python3
"""
Script pour corriger les données de permissions dans la base de données
Résout l'erreur 'str' object has no attribute 'get'
"""

import os
import sys
import django
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail

def fix_permissions_data():
    """Corrige les données de permissions mal formatées"""
    print("🔍 Vérification des données de permissions...")
    
    groupes_corriges = 0
    
    for groupe in GroupeTravail.objects.all():
        print(f"\n📋 Groupe: {groupe.nom}")
        print(f"   Type actuel: {type(groupe.permissions)}")
        print(f"   Valeur actuelle: {repr(groupe.permissions)}")
        
        # Si permissions est une chaîne, on essaie de la convertir
        if isinstance(groupe.permissions, str):
            try:
                # Essayer de parser le JSON
                permissions_dict = json.loads(groupe.permissions)
                groupe.permissions = permissions_dict
                groupe.save()
                print(f"   ✅ Converti en dictionnaire: {permissions_dict}")
                groupes_corriges += 1
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON valide, on met un dictionnaire vide
                groupe.permissions = {}
                groupe.save()
                print(f"   ⚠️  Chaîne invalide, remplacée par dictionnaire vide")
                groupes_corriges += 1
        elif isinstance(groupe.permissions, dict):
            print(f"   ✅ Déjà un dictionnaire")
        else:
            # Type inattendu, on le remplace par un dictionnaire vide
            groupe.permissions = {}
            groupe.save()
            print(f"   ⚠️  Type inattendu ({type(groupe.permissions)}), remplacé par dictionnaire vide")
            groupes_corriges += 1
    
    print(f"\n🎉 Correction terminée ! {groupes_corriges} groupes corrigés.")
    
    # Vérification finale
    print("\n🔍 Vérification finale...")
    for groupe in GroupeTravail.objects.all():
        print(f"   {groupe.nom}: {type(groupe.permissions)} - {groupe.permissions}")

if __name__ == "__main__":
    fix_permissions_data()

