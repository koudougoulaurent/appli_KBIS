#!/usr/bin/env python
"""
Script de test pour vérifier la visibilité des nouveaux IDs uniques
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Bailleur, Locataire, Propriete
from paiements.models import Paiement
from core.id_generator import IDGenerator

def test_visibilite_ids():
    """Test de la visibilité des nouveaux IDs uniques"""
    
    print("🔍 TEST DE VISIBILITÉ DES NOUVEAUX IDS UNIQUES")
    print("=" * 60)
    
    # Test 1: Vérification des modèles
    print("\n📋 TEST 1: Vérification des modèles")
    print("-" * 40)
    
    try:
        # Vérifier si les nouveaux champs existent dans les modèles
        bailleur_fields = [f.name for f in Bailleur._meta.fields]
        locataire_fields = [f.name for f in Locataire._meta.fields]
        propriete_fields = [f.name for f in Propriete._meta.fields]
        paiement_fields = [f.name for f in Paiement._meta.fields]
        
        print(f"Champs Bailleur: {bailleur_fields}")
        print(f"Champs Locataire: {locataire_fields}")
        print(f"Champs Propriété: {propriete_fields}")
        print(f"Champs Paiement: {paiement_fields}")
        
        # Vérifier la présence des nouveaux champs
        nouveaux_champs = ['numero_bailleur', 'numero_locataire', 'numero_propriete', 'numero_paiement']
        for champ in nouveaux_champs:
            if champ in bailleur_fields or champ in locataire_fields or champ in propriete_fields or champ in paiement_fields:
                print(f"✅ {champ}: Présent")
            else:
                print(f"❌ {champ}: Absent")
                
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des modèles: {e}")
    
    # Test 2: Vérification des données existantes
    print("\n📊 TEST 2: Vérification des données existantes")
    print("-" * 40)
    
    try:
        # Compter les enregistrements avec des IDs uniques
        bailleurs_avec_id = Bailleur.objects.filter(numero_bailleur__isnull=False).count()
        locataires_avec_id = Locataire.objects.filter(numero_locataire__isnull=False).count()
        proprietes_avec_id = Propriete.objects.filter(numero_propriete__isnull=False).count()
        paiements_avec_id = Paiement.objects.filter(numero_paiement__isnull=False).count()
        
        print(f"Bailleurs avec ID unique: {bailleurs_avec_id}")
        print(f"Locataires avec ID unique: {locataires_avec_id}")
        print(f"Propriétés avec ID unique: {proprietes_avec_id}")
        print(f"Paiements avec ID unique: {paiements_avec_id}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des données: {e}")
    
    # Test 3: Test de génération d'IDs
    print("\n🔄 TEST 3: Test de génération d'IDs")
    print("-" * 40)
    
    try:
        generator = IDGenerator()
        
        # Générer des exemples d'IDs
        id_bailleur = generator.generate_id('bailleur')
        id_locataire = generator.generate_id('locataire')
        id_propriete = generator.generate_id('propriete')
        id_paiement = generator.generate_id('paiement')
        
        print(f"ID Bailleur généré: {id_bailleur}")
        print(f"ID Locataire généré: {id_locataire}")
        print(f"ID Propriété généré: {id_propriete}")
        print(f"ID Paiement généré: {id_paiement}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération d'IDs: {e}")
    
    # Test 4: Vérification des vues
    print("\n👁️ TEST 4: Vérification des vues")
    print("-" * 40)
    
    try:
        from proprietes.views import BailleurListView, LocataireListView, ProprieteListView
        
        # Vérifier les colonnes des vues
        bailleur_view = BailleurListView()
        locataire_view = LocataireListView()
        propriete_view = ProprieteListView()
        
        print("Colonnes BailleurListView:")
        for col in bailleur_view.columns:
            print(f"  - {col['field']}: {col['label']}")
            
        print("\nColonnes LocataireListView:")
        for col in locataire_view.columns:
            print(f"  - {col['field']}: {col['label']}")
            
        print("\nColonnes ProprieteListView:")
        for col in propriete_view.columns:
            print(f"  - {col['field']}: {col['label']}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des vues: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test de visibilité terminé!")

if __name__ == '__main__':
    test_visibilite_ids()
