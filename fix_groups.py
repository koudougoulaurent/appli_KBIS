#!/usr/bin/env python
"""
Script de correction automatique des groupes pour Render
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail

def fix_groups():
    """Corriger les groupes de travail"""
    print("🔧 Correction des groupes de travail...")
    
    # Supprimer tous les groupes existants
    GroupeTravail.objects.all().delete()
    print("🗑️  Anciens groupes supprimés")
    
    # Créer les groupes correctement
    groupes_data = [
        {'nom': 'ADMINISTRATION', 'description': 'GESTION ADMINISTRATIVE'},
        {'nom': 'CAISSE', 'description': 'GESTION DES PAIEMENTS ET RETRAITS'},
        {'nom': 'CONTROLES', 'description': 'GESTION DU CONTRÔLE'},
        {'nom': 'PRIVILEGE', 'description': 'ACCÈS COMPLET'}
    ]
    
    for groupe_data in groupes_data:
        groupe = GroupeTravail.objects.create(
            nom=groupe_data['nom'],
            description=groupe_data['description'],
            actif=True
        )
        print(f"✅ Groupe créé : {groupe.nom}")
    
    print("\n🎉 Tous les groupes sont maintenant créés et actifs !")
    print("🔄 Rafraîchissez votre page web pour voir les changements")

if __name__ == '__main__':
    fix_groups()
