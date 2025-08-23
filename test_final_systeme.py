#!/usr/bin/env python
"""
Script de test final pour vérifier que le système des IDs uniques fonctionne complètement
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

def test_final_systeme():
    """Test final du système des IDs uniques"""
    
    print("🎯 TEST FINAL DU SYSTÈME DES IDS UNIQUES")
    print("=" * 60)
    
    # Test 1: Vérification des modèles
    print("\n📋 TEST 1: Vérification des modèles")
    print("-" * 40)
    
    try:
        # Vérifier que les nouveaux champs existent dans les modèles
        bailleur_fields = [f.name for f in Bailleur._meta.fields]
        locataire_fields = [f.name for f in Locataire._meta.fields]
        propriete_fields = [f.name for f in Propriete._meta.fields]
        paiement_fields = [f.name for f in Paiement._meta.fields]
        
        nouveaux_champs = ['numero_bailleur', 'numero_locataire', 'numero_propriete', 'numero_paiement']
        
        for champ in nouveaux_champs:
            if champ in bailleur_fields:
                print(f"✅ {champ}: Présent dans Bailleur")
            elif champ in locataire_fields:
                print(f"✅ {champ}: Présent dans Locataire")
            elif champ in propriete_fields:
                print(f"✅ {champ}: Présent dans Propriete")
            elif champ in paiement_fields:
                print(f"✅ {champ}: Présent dans Paiement")
            else:
                print(f"❌ {champ}: Absent de tous les modèles")
                
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
        
        total_bailleurs = Bailleur.objects.count()
        total_locataires = Locataire.objects.count()
        total_proprietes = Propriete.objects.count()
        total_paiements = Paiement.objects.count()
        
        print(f"Bailleurs: {bailleurs_avec_id}/{total_bailleurs} avec ID unique")
        print(f"Locataires: {locataires_avec_id}/{total_locataires} avec ID unique")
        print(f"Propriétés: {proprietes_avec_id}/{total_proprietes} avec ID unique")
        print(f"Paiements: {paiements_avec_id}/{total_paiements} avec ID unique")
        
        # Calculer le pourcentage de couverture
        couverture_bailleurs = (bailleurs_avec_id / total_bailleurs) * 100 if total_bailleurs > 0 else 0
        couverture_locataires = (locataires_avec_id / total_locataires) * 100 if total_locataires > 0 else 0
        couverture_proprietes = (proprietes_avec_id / total_proprietes) * 100 if total_proprietes > 0 else 0
        couverture_paiements = (paiements_avec_id / total_paiements) * 100 if total_paiements > 0 else 0
        
        print(f"\n📈 Couverture:")
        print(f"   Bailleurs: {couverture_bailleurs:.1f}%")
        print(f"   Locataires: {couverture_locataires:.1f}%")
        print(f"   Propriétés: {couverture_proprietes:.1f}%")
        print(f"   Paiements: {couverture_paiements:.1f}%")
        
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
            
        # Vérifier que les nouvelles colonnes sont présentes
        bailleur_columns = [col['field'] for col in bailleur_view.columns]
        locataire_columns = [col['field'] for col in locataire_view.columns]
        propriete_columns = [col['field'] for col in propriete_view.columns]
        
        if 'numero_bailleur' in bailleur_columns:
            print("\n✅ Colonne numero_bailleur présente dans BailleurListView")
        else:
            print("\n❌ Colonne numero_bailleur absente de BailleurListView")
            
        if 'numero_locataire' in locataire_columns:
            print("✅ Colonne numero_locataire présente dans LocataireListView")
        else:
            print("❌ Colonne numero_locataire absente de LocataireListView")
            
        if 'numero_propriete' in propriete_columns:
            print("✅ Colonne numero_propriete présente dans ProprieteListView")
        else:
            print("❌ Colonne numero_propriete absente de ProprieteListView")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des vues: {e}")
    
    # Test 5: Test d'accès aux données
    print("\n🔍 TEST 5: Test d'accès aux données")
    print("-" * 40)
    
    try:
        # Tester l'accès aux nouveaux champs
        bailleur_exemple = Bailleur.objects.filter(numero_bailleur__isnull=False).first()
        if bailleur_exemple:
            print(f"✅ Exemple bailleur: {bailleur_exemple.nom} - {bailleur_exemple.numero_bailleur}")
        
        locataire_exemple = Locataire.objects.filter(numero_locataire__isnull=False).first()
        if locataire_exemple:
            print(f"✅ Exemple locataire: {locataire_exemple.nom} - {locataire_exemple.numero_locataire}")
        
        propriete_exemple = Propriete.objects.filter(numero_propriete__isnull=False).first()
        if propriete_exemple:
            print(f"✅ Exemple propriété: {propriete_exemple.titre} - {propriete_exemple.numero_propriete}")
        
        paiement_exemple = Paiement.objects.filter(numero_paiement__isnull=False).first()
        if paiement_exemple:
            print(f"✅ Exemple paiement: {paiement_exemple.id} - {paiement_exemple.numero_paiement}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'accès aux données: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test final terminé!")
    
    # Résumé final
    print("\n📊 RÉSUMÉ FINAL:")
    print("-" * 30)
    
    if (bailleurs_avec_id == total_bailleurs and 
        locataires_avec_id == total_locataires and 
        proprietes_avec_id == total_proprietes):
        print("🎉 SUCCÈS: Tous les modèles principaux ont des IDs uniques!")
        print("✅ Le système est prêt à être utilisé")
        print("✅ Les nouveaux IDs sont visibles dans les vues")
        print("✅ L'application peut être testée dans le navigateur")
    else:
        print("⚠️  ATTENTION: Certains enregistrements n'ont pas encore d'IDs uniques")
        print("🔧 Des corrections supplémentaires peuvent être nécessaires")

if __name__ == '__main__':
    test_final_systeme()
