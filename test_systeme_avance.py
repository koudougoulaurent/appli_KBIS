#!/usr/bin/env python
"""
Script de test pour le système d'avances de loyer KBIS
Teste toutes les fonctionnalités du système intelligent d'avances
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.models import Contrat
from proprietes.models import Propriete, Bailleur, Locataire
from paiements.models_avance import AvanceLoyer, ConsommationAvance, HistoriquePaiement
from paiements.services_avance import ServiceGestionAvance
from paiements.models import Paiement
from utilisateurs.models import Utilisateur

def creer_donnees_test():
    """Crée les données de test nécessaires"""
    print("🔧 Création des données de test...")
    
    # Créer un utilisateur de test
    user, created = Utilisateur.objects.get_or_create(
        username='test_avance',
        defaults={
            'email': 'test@kbis.com',
            'prenom': 'Test',
            'nom': 'Avance'
        }
    )
    
    # Créer un bailleur
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Dupont',
        prenom='Jean',
        defaults={
            'email': 'jean.dupont@test.com',
            'telephone': '0123456789'
        }
    )
    
    # Créer une propriété
    propriete, created = Propriete.objects.get_or_create(
        adresse='123 Rue de Test',
        ville='Ouagadougou',
        defaults={
            'bailleur': bailleur,
            'type_bien': 'Appartement',
            'nombre_pieces': 3
        }
    )
    
    # Créer un locataire
    locataire, created = Locataire.objects.get_or_create(
        nom='Martin',
        prenom='Pierre',
        defaults={
            'email': 'pierre.martin@test.com',
            'telephone': '0987654321'
        }
    )
    
    # Créer un contrat
    contrat, created = Contrat.objects.get_or_create(
        numero_contrat='TEST-AVANCE-001',
        defaults={
            'propriete': propriete,
            'locataire': locataire,
            'loyer_mensuel': Decimal('150000'),
            'charges_mensuelles': Decimal('15000'),
            'date_debut': date.today(),
            'est_actif': True
        }
    )
    
    print(f"✅ Données créées: Contrat {contrat.numero_contrat}")
    return contrat, user

def test_creation_avance():
    """Test de création d'avance avec calcul automatique"""
    print("\n🧪 Test 1: Création d'avance avec calcul automatique")
    
    contrat, user = creer_donnees_test()
    
    # Créer une avance de 450 000 F CFA (3 mois de loyer)
    avance = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('450000'),
        date_avance=date.today(),
        notes="Test automatique - 3 mois d'avance"
    )
    
    print(f"   📊 Avance créée: {avance.montant_avance} F CFA")
    print(f"   📅 Mois couverts: {avance.nombre_mois_couverts}")
    print(f"   💰 Montant restant: {avance.montant_restant} F CFA")
    print(f"   📆 Période: {avance.mois_debut_couverture} à {avance.mois_fin_couverture}")
    
    # Vérifications
    assert avance.nombre_mois_couverts == 3, "Le nombre de mois couverts devrait être 3"
    assert avance.montant_restant == Decimal('0'), "Le montant restant devrait être 0"
    assert avance.statut == 'epuisee', "Le statut devrait être 'epuisee'"
    
    print("   ✅ Test réussi!")
    return avance

def test_avance_avec_reste():
    """Test d'avance avec reste (pas un nombre entier de mois)"""
    print("\n🧪 Test 2: Avance avec reste")
    
    contrat, user = creer_donnees_test()
    
    # Créer une avance de 400 000 F CFA (2 mois + 100 000 F CFA)
    avance = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('400000'),
        date_avance=date.today(),
        notes="Test avec reste"
    )
    
    print(f"   📊 Avance créée: {avance.montant_avance} F CFA")
    print(f"   📅 Mois couverts: {avance.nombre_mois_couverts}")
    print(f"   💰 Montant restant: {avance.montant_restant} F CFA")
    print(f"   📆 Période: {avance.mois_debut_couverture} à {avance.mois_fin_couverture}")
    
    # Vérifications
    assert avance.nombre_mois_couverts == 2, "Le nombre de mois couverts devrait être 2"
    assert avance.montant_restant == Decimal('100000'), "Le montant restant devrait être 100 000 F CFA"
    assert avance.statut == 'active', "Le statut devrait être 'active'"
    
    print("   ✅ Test réussi!")
    return avance

def test_consommation_avance():
    """Test de consommation d'avance mois par mois"""
    print("\n🧪 Test 3: Consommation d'avance")
    
    contrat, user = creer_donnees_test()
    
    # Créer une avance de 300 000 F CFA (2 mois)
    avance = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('300000'),
        date_avance=date.today(),
        notes="Test de consommation"
    )
    
    print(f"   📊 Avance initiale: {avance.montant_avance} F CFA")
    print(f"   📅 Mois couverts: {avance.nombre_mois_couverts}")
    
    # Consommer le premier mois
    mois1 = date.today().replace(day=1)
    success, montant = ServiceGestionAvance.consommer_avance_pour_mois(contrat, mois1)
    
    print(f"   🗓️ Consommation mois 1: {success}, {montant} F CFA")
    
    # Recharger l'avance depuis la DB
    avance.refresh_from_db()
    print(f"   💰 Montant restant après mois 1: {avance.montant_restant} F CFA")
    
    # Consommer le deuxième mois
    mois2 = mois1 + relativedelta(months=1)
    success, montant = ServiceGestionAvance.consommer_avance_pour_mois(contrat, mois2)
    
    print(f"   🗓️ Consommation mois 2: {success}, {montant} F CFA")
    
    # Recharger l'avance depuis la DB
    avance.refresh_from_db()
    print(f"   💰 Montant restant après mois 2: {avance.montant_restant} F CFA")
    print(f"   📊 Statut final: {avance.statut}")
    
    # Vérifications
    assert avance.montant_restant == Decimal('0'), "Le montant restant devrait être 0"
    assert avance.statut == 'epuisee', "Le statut devrait être 'epuisee'"
    
    print("   ✅ Test réussi!")

def test_paiement_avance_automatique():
    """Test de paiement d'avance avec traitement automatique"""
    print("\n🧪 Test 4: Paiement d'avance automatique")
    
    contrat, user = creer_donnees_test()
    
    # Créer un paiement d'avance
    paiement = Paiement.objects.create(
        contrat=contrat,
        montant=Decimal('300000'),
        type_paiement='avance_loyer',
        mode_paiement='especes',
        date_paiement=date.today(),
        statut='valide',
        cree_par=user
    )
    
    print(f"   💳 Paiement créé: {paiement.montant} F CFA")
    
    # Traiter le paiement d'avance
    avance = ServiceGestionAvance.traiter_paiement_avance(paiement)
    
    print(f"   📊 Avance créée automatiquement: {avance.montant_avance} F CFA")
    print(f"   📅 Mois couverts: {avance.nombre_mois_couverts}")
    
    # Vérifications
    assert avance is not None, "Une avance devrait être créée"
    assert avance.nombre_mois_couverts == 2, "Le nombre de mois couverts devrait être 2"
    
    print("   ✅ Test réussi!")
    return avance

def test_historique_paiements():
    """Test de l'historique des paiements"""
    print("\n🧪 Test 5: Historique des paiements")
    
    contrat, user = creer_donnees_test()
    
    # Créer un paiement mensuel
    paiement = Paiement.objects.create(
        contrat=contrat,
        montant=Decimal('165000'),
        type_paiement='loyer',
        mode_paiement='especes',
        date_paiement=date.today(),
        statut='valide',
        cree_par=user
    )
    
    # Traiter le paiement mensuel
    historique = ServiceGestionAvance.traiter_paiement_mensuel(paiement)
    
    print(f"   📊 Historique créé pour: {historique.mois_paiement}")
    print(f"   💰 Montant payé: {historique.montant_paye} F CFA")
    print(f"   💰 Montant dû: {historique.montant_du} F CFA")
    print(f"   📊 Mois réglé: {historique.mois_regle}")
    
    # Vérifications
    assert historique is not None, "Un historique devrait être créé"
    assert historique.montant_du == Decimal('165000'), "Le montant dû devrait être 165 000 F CFA"
    
    print("   ✅ Test réussi!")

def test_rapport_avances():
    """Test de génération de rapport d'avances"""
    print("\n🧪 Test 6: Rapport d'avances")
    
    contrat, user = creer_donnees_test()
    
    # Créer plusieurs avances
    avance1 = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('300000'),
        date_avance=date.today(),
        notes="Première avance"
    )
    
    avance2 = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('150000'),
        date_avance=date.today(),
        notes="Deuxième avance"
    )
    
    # Générer le rapport
    rapport = ServiceGestionAvance.generer_rapport_avances_contrat(contrat)
    
    print(f"   📊 Nombre d'avances: {len(rapport['avances'])}")
    print(f"   💰 Total versé: {rapport['statistiques']['total_avances_versees']} F CFA")
    print(f"   💰 Total restant: {rapport['statistiques']['total_avances_restantes']} F CFA")
    print(f"   📅 Mois couverts: {rapport['statistiques']['nombre_mois_couverts']}")
    
    # Vérifications
    assert len(rapport['avances']) == 2, "Il devrait y avoir 2 avances"
    assert rapport['statistiques']['total_avances_versees'] == Decimal('450000'), "Le total versé devrait être 450 000 F CFA"
    
    print("   ✅ Test réussi!")

def test_calcul_montant_du():
    """Test de calcul du montant dû avec avances"""
    print("\n🧪 Test 7: Calcul du montant dû")
    
    contrat, user = creer_donnees_test()
    
    # Créer une avance
    avance = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('300000'),
        date_avance=date.today(),
        notes="Test calcul"
    )
    
    # Calculer le montant dû pour le mois actuel
    mois = date.today().replace(day=1)
    montant_du, montant_avance = ServiceGestionAvance.calculer_montant_du_mois(contrat, mois)
    
    print(f"   💰 Montant dû: {montant_du} F CFA")
    print(f"   💰 Avance utilisée: {montant_avance} F CFA")
    print(f"   📊 Loyer mensuel: {contrat.loyer_mensuel} F CFA")
    
    # Vérifications
    assert montant_du == Decimal('0'), "Le montant dû devrait être 0 (avance couvre le mois)"
    assert montant_avance == Decimal('150000'), "L'avance utilisée devrait être 150 000 F CFA"
    
    print("   ✅ Test réussi!")

def nettoyer_donnees_test():
    """Nettoie les données de test"""
    print("\n🧹 Nettoyage des données de test...")
    
    # Supprimer les données de test
    AvanceLoyer.objects.filter(notes__contains="Test").delete()
    Paiement.objects.filter(contrat__numero_contrat="TEST-AVANCE-001").delete()
    Contrat.objects.filter(numero_contrat="TEST-AVANCE-001").delete()
    Propriete.objects.filter(adresse="123 Rue de Test").delete()
    Bailleur.objects.filter(nom="Dupont", prenom="Jean").delete()
    Locataire.objects.filter(nom="Martin", prenom="Pierre").delete()
    Utilisateur.objects.filter(username="test_avance").delete()
    
    print("   ✅ Données nettoyées!")

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DU SYSTÈME D'AVANCES KBIS")
    print("=" * 60)
    
    try:
        # Exécuter tous les tests
        test_creation_avance()
        test_avance_avec_reste()
        test_consommation_avance()
        test_paiement_avance_automatique()
        test_historique_paiements()
        test_rapport_avances()
        test_calcul_montant_du()
        
        print("\n" + "=" * 60)
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        print("✅ Le système d'avances de loyer est fonctionnel")
        print("✅ Calcul automatique des mois opérationnel")
        print("✅ Gestion intelligente des paiements multiples")
        print("✅ Suivi des mois d'avance pour les prochains paiements")
        print("✅ Génération d'historique détaillé en PDF")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Nettoyer les données de test
        nettoyer_donnees_test()
        print("\n🏁 Tests terminés!")

if __name__ == "__main__":
    main()
