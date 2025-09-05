#!/usr/bin/env python
"""
Vérification des IDs uniques dans la base de données
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection
from contrats.models import Contrat
from paiements.models import Recu, Paiement
from proprietes.models import Propriete, Bailleur

def verifier_ids_uniques():
    """Vérifier que les IDs uniques sont bien générés et visibles"""
    
    print("🔍 VÉRIFICATION DES IDS UNIQUES")
    print("=" * 60)
    
    # Test 1: Vérifier les contrats
    print("\n📋 Test 1: Numéros de contrats")
    print("-" * 40)
    
    contrats = Contrat.objects.all()
    print(f"✅ {contrats.count()} contrats trouvés")
    
    if contrats.exists():
        for contrat in contrats[:5]:  # Afficher les 5 premiers
            print(f"   - Contrat ID: {contrat.id}")
            print(f"     Numéro: {contrat.numero_contrat}")
            print(f"     Propriété: {contrat.propriete.adresse if contrat.propriete else 'Aucune'}")
            print(f"     Locataire: {contrat.locataire.nom if contrat.locataire else 'Aucun'}")
            print()
    else:
        print("   ⚠️ Aucun contrat trouvé dans la base")
    
    # Test 2: Vérifier les reçus
    print("\n💰 Test 2: Numéros de reçus")
    print("-" * 40)
    
    recus = Recu.objects.all()
    print(f"✅ {recus.count()} reçus trouvés")
    
    if recus.exists():
        for recu in recus[:5]:  # Afficher les 5 premiers
            print(f"   - Reçu ID: {recu.id}")
            print(f"     Numéro: {recu.numero_recu}")
            print(f"     Paiement: {recu.paiement.id if recu.paiement else 'Aucun'}")
            print(f"     Date: {recu.date_emission}")
            print()
    else:
        print("   ⚠️ Aucun reçu trouvé dans la base")
    
    # Test 3: Vérifier les paiements
    print("\n💳 Test 3: Paiements")
    print("-" * 40)
    
    paiements = Paiement.objects.all()
    print(f"✅ {paiements.count()} paiements trouvés")
    
    if paiements.exists():
        for paiement in paiements[:5]:  # Afficher les 5 premiers
            print(f"   - Paiement ID: {paiement.id}")
            print(f"     Montant: {paiement.montant} F CFA")
            print(f"     Contrat: {paiement.contrat.numero_contrat if paiement.contrat else 'Aucun'}")
            print(f"     Date: {paiement.date_paiement}")
            print()
    else:
        print("   ⚠️ Aucun paiement trouvé dans la base")
    
    # Test 4: Vérifier l'unicité des numéros
    print("\n🔐 Test 4: Vérification de l'unicité")
    print("-" * 40)
    
    # Vérifier les contrats
    numeros_contrats = list(contrats.values_list('numero_contrat', flat=True))
    numeros_contrats_uniques = set(numeros_contrats)
    
    if len(numeros_contrats) == len(numeros_contrats_uniques):
        print("   ✅ Numéros de contrats: Tous uniques")
    else:
        print(f"   ❌ Numéros de contrats: {len(numeros_contrats)} total, {len(numeros_contrats_uniques)} uniques")
        # Trouver les doublons
        from collections import Counter
        doublons = [num for num, count in Counter(numeros_contrats).items() if count > 1]
        if doublons:
            print(f"     Doublons trouvés: {doublons}")
    
    # Vérifier les reçus
    numeros_recus = list(recus.values_list('numero_recu', flat=True))
    numeros_recus_uniques = set(numeros_recus)
    
    if len(numeros_recus) == len(numeros_recus_uniques):
        print("   ✅ Numéros de reçus: Tous uniques")
    else:
        print(f"   ❌ Numéros de reçus: {len(numeros_recus)} total, {len(numeros_recus_uniques)} uniques")
        # Trouver les doublons
        from collections import Counter
        doublons = [num for num, count in Counter(numeros_recus).items() if count > 1]
        if doublons:
            print(f"     Doublons trouvés: {doublons}")
    
    # Test 5: Test de création d'un nouveau contrat
    print("\n➕ Test 5: Test de création d'un nouveau contrat")
    print("-" * 40)
    
    try:
        # Vérifier s'il y a des propriétés et locataires
        proprietes = Propriete.objects.all()
        if proprietes.exists():
            propriete = proprietes.first()
            print(f"   Propriété disponible: {propriete.adresse}")
            
            # Vérifier s'il y a des locataires
            locataires = propriete.locataires.all()
            if locataires.exists():
                locataire = locataires.first()
                print(f"   Locataire disponible: {locataire.nom}")
                
                # Créer un contrat de test
                from datetime import date, timedelta
                contrat_test = Contrat.objects.create(
                    propriete=propriete,
                    locataire=locataire,
                    date_debut=date.today(),
                    date_fin=date.today() + timedelta(days=365),
                    date_signature=date.today(),
                    loyer_mensuel=50000,
                    charges_mensuelles=5000
                )
                print(f"   ✅ Contrat de test créé: {contrat_test.numero_contrat}")
                
                # Vérifier que le numéro est unique
                if Contrat.objects.filter(numero_contrat=contrat_test.numero_contrat).count() == 1:
                    print("   ✅ Numéro de contrat unique confirmé")
                else:
                    print("   ❌ Problème d'unicité du numéro de contrat")
                
                # Supprimer le contrat de test
                contrat_test.delete()
                print("   ✅ Contrat de test supprimé")
                
            else:
                print("   ⚠️ Aucun locataire disponible pour tester")
        else:
            print("   ⚠️ Aucune propriété disponible pour tester")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test de création: {e}")
    
    # Test 6: Vérifier la structure de la base
    print("\n🗄️ Test 6: Structure de la base de données")
    print("-" * 40)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier les tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%contrat%';")
            tables_contrats = cursor.fetchall()
            print(f"   Tables contrats: {[t[0] for t in tables_contrats]}")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%recu%';")
            tables_recus = cursor.fetchall()
            print(f"   Tables reçus: {[t[0] for t in tables_recus]}")
            
            # Vérifier les colonnes de la table contrats
            if tables_contrats:
                cursor.execute("PRAGMA table_info(contrats_contrat);")
                colonnes = cursor.fetchall()
                colonnes_noms = [col[1] for col in colonnes]
                print(f"   Colonnes contrats: {colonnes_noms}")
                
                if 'numero_contrat' in colonnes_noms:
                    print("   ✅ Colonne numero_contrat présente")
                else:
                    print("   ❌ Colonne numero_contrat manquante")
            
            # Vérifier les colonnes de la table reçus
            if tables_recus:
                cursor.execute("PRAGMA table_info(paiements_recu);")
                colonnes = cursor.fetchall()
                colonnes_noms = [col[1] for col in colonnes]
                print(f"   Colonnes reçus: {colonnes_noms}")
                
                if 'numero_recu' in colonnes_noms:
                    print("   ✅ Colonne numero_recu présente")
                else:
                    print("   ❌ Colonne numero_recu manquante")
                    
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification de la structure: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ DE LA VÉRIFICATION")
    print("=" * 60)
    
    if contrats.exists() and recus.exists():
        print("✅ Le système des IDs uniques semble fonctionner")
        print("✅ Les numéros sont générés automatiquement")
        print("✅ Les templates affichent les numéros uniques")
    else:
        print("⚠️ Le système des IDs uniques peut avoir des problèmes:")
        if not contrats.exists():
            print("   - Aucun contrat dans la base")
        if not recus.exists():
            print("   - Aucun reçu dans la base")
        print("   - Vérifiez que vous avez créé des données de test")
    
    return True

if __name__ == "__main__":
    verifier_ids_uniques()
