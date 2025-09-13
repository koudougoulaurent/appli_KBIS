#!/usr/bin/env python
"""
Script de correction FORCÉE des groupes - SOLUTION DÉFINITIVE
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import transaction
from utilisateurs.models import GroupeTravail

def force_fix_groups():
    """Correction FORCÉE des groupes - SOLUTION DÉFINITIVE"""
    print("🔥 CORRECTION FORCÉE DES GROUPES - SOLUTION DÉFINITIVE")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # 1. Supprimer TOUS les groupes existants
            print("🗑️  Suppression de tous les groupes existants...")
            GroupeTravail.objects.all().delete()
            
            # 2. Créer les groupes avec des IDs spécifiques
            print("🔧 Création des groupes avec IDs fixes...")
            
            groupes_data = [
                {'id': 1, 'nom': 'ADMINISTRATION', 'description': 'GESTION ADMINISTRATIVE'},
                {'id': 2, 'nom': 'CAISSE', 'description': 'GESTION DES PAIEMENTS ET RETRAITS'},
                {'id': 3, 'nom': 'CONTROLES', 'description': 'GESTION DU CONTRÔLE'},
                {'id': 4, 'nom': 'PRIVILEGE', 'description': 'ACCÈS COMPLET'}
            ]
            
            for groupe_data in groupes_data:
                # Forcer la création avec ID spécifique
                groupe = GroupeTravail(
                    id=groupe_data['id'],
                    nom=groupe_data['nom'],
                    description=groupe_data['description'],
                    actif=True,
                    permissions={'modules': []}
                )
                groupe.save(force_insert=True)
                print(f"✅ Groupe créé : {groupe.nom} (ID: {groupe.id})")
            
            # 3. Vérifier que tous les groupes sont actifs
            print("\n🔍 Vérification des groupes...")
            for groupe in GroupeTravail.objects.all():
                if not groupe.actif:
                    groupe.actif = True
                    groupe.save()
                    print(f"✅ Groupe activé : {groupe.nom}")
                else:
                    print(f"✅ Groupe actif : {groupe.nom}")
            
            print("\n" + "=" * 60)
            print("🎉 CORRECTION TERMINÉE AVEC SUCCÈS !")
            print("✅ Tous les groupes sont créés et actifs")
            print("✅ L'erreur 'PRIVILEGE n'existe pas' est corrigée")
            print("🔄 Rafraîchissez votre page web maintenant !")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("🔄 Tentative de récupération...")
        
        # Tentative de récupération
        try:
            GroupeTravail.objects.all().delete()
            for i, nom in enumerate(['ADMINISTRATION', 'CAISSE', 'CONTROLES', 'PRIVILEGE'], 1):
                GroupeTravail.objects.create(
                    nom=nom,
                    description=f'Groupe {nom}',
                    actif=True
                )
            print("✅ Récupération réussie !")
        except Exception as e2:
            print(f"❌ Échec de la récupération: {e2}")
            sys.exit(1)

if __name__ == '__main__':
    force_fix_groups()
