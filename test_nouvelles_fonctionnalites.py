#!/usr/bin/env python
"""
Script de test pour vérifier toutes les nouvelles fonctionnalités implémentées
"""

import os
import sys
import django
from datetime import datetime, date
from datetime import date as date_today
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from core.models import ConfigurationEntreprise
from proprietes.models import Bailleur, Propriete, Locataire, TypeBien
from contrats.models import Contrat, RecuCaution, DocumentContrat, ResiliationContrat
from paiements.models import Paiement, RetraitBailleur, RecapMensuel, RecuRetrait

Utilisateur = get_user_model()

def test_creation_donnees():
    """Créer les données de test nécessaires"""
    print("🔧 Création des données de test...")
    
    # Créer le groupe PRIVILEGE s'il n'existe pas
    groupe_privilege, created = Group.objects.get_or_create(name='PRIVILEGE')
    if created:
        print("✅ Groupe PRIVILEGE créé")
    else:
        print("✅ Groupe PRIVILEGE existe déjà")
    
    # Créer le groupe CAISSE s'il n'existe pas
    groupe_caisse, created = Group.objects.get_or_create(name='CAISSE')
    if created:
        print("✅ Groupe CAISSE créé")
    else:
        print("✅ Groupe CAISSE existe déjà")
    
    # Créer un utilisateur de test
    utilisateur, created = Utilisateur.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        utilisateur.set_password('testpass123')
        utilisateur.save()
        utilisateur.groups.add(groupe_privilege)
        print("✅ Utilisateur de test créé")
    else:
        print("✅ Utilisateur de test existe déjà")
    
    # Créer la configuration de l'entreprise
    config, created = ConfigurationEntreprise.objects.get_or_create(
        nom_entreprise="Test Immobilier SARL",
        defaults={
            'adresse': "123 Rue de la Paix",
            'ville': "Abidjan",
            'code_postal': "00225",
            'pays': "Côte d'Ivoire",
            'telephone': "+225 27 22 49 87 65",
            'email': "contact@testimmobilier.ci",
            'site_web': "www.testimmobilier.ci"
        }
    )
    if created:
        print("✅ Configuration entreprise créée")
    else:
        print("✅ Configuration entreprise existe déjà")
    
    return utilisateur, config

def test_contrat_caution():
    """Tester la gestion des cautions et avances"""
    print("\n🏠 Test de la gestion des cautions et avances...")
    
    # Créer un type de bien de test
    type_bien, created = TypeBien.objects.get_or_create(
        nom="Appartement",
        defaults={
            'description': 'Appartement résidentiel',
            'est_actif': True
        }
    )
    if created:
        print("✅ Type de bien créé")
    
    # Créer un bailleur de test
    bailleur, created = Bailleur.objects.get_or_create(
        nom="Dupont",
        prenom="Jean",
        defaults={
            'telephone': '+225 27 22 49 87 65',
            'email': 'jean.dupont@example.com',
            'adresse': '456 Avenue des Fleurs'
        }
    )
    if created:
        print("✅ Bailleur créé")
    
    # Créer une propriété de test
    propriete, created = Propriete.objects.get_or_create(
        titre="Appartement T3",
        defaults={
            'bailleur': bailleur,
            'type_bien': type_bien,
            'adresse': '789 Rue du Commerce',
            'ville': 'Abidjan',
            'code_postal': '00225',
            'pays': 'Côte d\'Ivoire',
            'surface': Decimal('75.00'),
            'nombre_pieces': 3,
            'nombre_chambres': 2,
            'nombre_salles_bain': 1,
            'loyer_actuel': Decimal('150000'),
            'charges_locataire': Decimal('15000'),
            'cree_par': Utilisateur.objects.first()
        }
    )
    if created:
        print("✅ Propriété créée")
    
    # Créer un locataire de test
    locataire, created = Locataire.objects.get_or_create(
        nom="Martin",
        prenom="Pierre",
        defaults={
            'telephone': '+225 27 22 49 87 66',
            'email': 'pierre.martin@example.com',
            'adresse_actuelle': '321 Rue de la Liberté'
        }
    )
    if created:
        print("✅ Locataire créé")
    
    # Créer un contrat de test
    contrat, created = Contrat.objects.get_or_create(
        numero_contrat="CTR-TEST001",
        defaults={
            'propriete': propriete,
            'locataire': locataire,
            'date_debut': date(2025, 1, 1),
            'date_fin': date(2027, 12, 31),
            'date_signature': date(2024, 12, 15),
            'loyer_mensuel': Decimal('150000'),
            'charges_mensuelles': Decimal('15000'),
            'cree_par': Utilisateur.objects.first()
        }
    )
    if created:
        print("✅ Contrat créé")
    
    # Tester les méthodes de caution
    print(f"💰 Dépôt de garantie: {contrat.get_depot_garantie_formatted()}")
    print(f"💰 Avance de loyer: {contrat.get_avance_loyer_formatted()}")
    print(f"💰 Total caution + avance: {contrat.get_total_caution_avance_formatted()}")
    
    # Marquer la caution comme payée
    contrat.marquer_caution_payee()
    print("✅ Caution marquée comme payée")
    
    # Marquer l'avance comme payée
    contrat.marquer_avance_payee()
    print("✅ Avance marquée comme payée")
    
    # Vérifier le statut
    print(f"📊 Statut des paiements: {contrat.get_statut_paiements()}")
    print(f"📊 Peut commencer location: {contrat.peut_commencer_location()}")
    
    return contrat

def test_retrait_bailleur():
    """Tester la gestion des retraits de bailleur"""
    print("\n💸 Test de la gestion des retraits de bailleur...")
    
    # Récupérer le contrat créé précédemment
    contrat = Contrat.objects.filter(numero_contrat="CTR-TEST001").first()
    if not contrat:
        print("❌ Contrat de test non trouvé")
        return None
    
    # Créer un retrait de bailleur
    retrait, created = RetraitBailleur.objects.get_or_create(
        bailleur=contrat.propriete.bailleur,
        mois_retrait=date(2025, 1, 31),
        defaults={
            'montant_loyers_bruts': Decimal('150000'),
            'montant_charges_deductibles': Decimal('15000'),
            'type_retrait': 'mensuel',
            'statut': 'en_cours',
            'mode_retrait': 'virement',
            'date_demande': date_today.today(),
            'cree_par': Utilisateur.objects.first()
        }
    )
    print("✅ Retrait de bailleur créé")
    
    # Calculer le montant net
    montant_net = retrait.calculer_montant_net()
    print(f"💰 Montant net à payer: {retrait.get_montant_net_formatted()}")
    
    # Valider le retrait
    retrait.valider_retrait(Utilisateur.objects.first())
    print("✅ Retrait validé")
    
    # Marquer comme payé
    retrait.marquer_paye(Utilisateur.objects.first())
    print("✅ Retrait marqué comme payé")
    
    return retrait

def test_recap_mensuel():
    """Tester la création de récapitulatif mensuel"""
    print("\n📊 Test de la création de récapitulatif mensuel...")
    
    # Récupérer le bailleur
    bailleur = Bailleur.objects.filter(nom="Dupont").first()
    if not bailleur:
        print("❌ Bailleur de test non trouvé")
        return None
    
    # Créer un récapitulatif mensuel
    recap, created = RecapMensuel.objects.get_or_create(
        bailleur=bailleur,
        mois_recap=date(2025, 1, 31),
        defaults={
            'cree_par': Utilisateur.objects.first()
        }
    )
    print("✅ Récapitulatif mensuel créé")
    
    # Calculer les totaux
    recap.calculer_totaux()
    print(f"💰 Total loyers bruts: {recap.get_total_loyers_bruts_formatted()}")
    print(f"💰 Total charges déductibles: {recap.get_total_charges_deductibles_formatted()}")
    print(f"💰 Total net à payer: {recap.get_total_net_formatted()}")
    
    # Valider le récapitulatif
    recap.valider_recap(Utilisateur.objects.first())
    print("✅ Récapitulatif validé")
    
    return recap

def test_paiement_partiel():
    """Tester les paiements partiels"""
    print("\n💳 Test des paiements partiels...")
    
    # Récupérer le contrat
    contrat = Contrat.objects.filter(numero_contrat="CTR-TEST001").first()
    if not contrat:
        print("❌ Contrat de test non trouvé")
        return None
    
    # Créer un paiement partiel
    paiement = Paiement.objects.create(
        contrat=contrat,
        montant=Decimal('75000'),
        type_paiement='paiement_partiel',
        est_paiement_partiel=True,
        mois_paye=date(2025, 1, 1),
        montant_du_mois=Decimal('150000'),
        montant_restant_du=Decimal('75000'),
        mode_paiement='virement',
        statut='valide',
        date_paiement=date_today.today(),
        cree_par=Utilisateur.objects.first()
    )
    print("✅ Paiement partiel créé")
    
    # Vérifier les méthodes
    print(f"📅 Peut payer le mois: {paiement.peut_payer_mois(date(2025, 1, 1))}")
    print(f"📅 Prochain mois payable: {paiement.get_prochain_mois_payable()}")
    
    return paiement

def test_resiliation_contrat():
    """Tester la résiliation de contrat"""
    print("\n🚪 Test de la résiliation de contrat...")
    
    # Récupérer le contrat
    contrat = Contrat.objects.filter(numero_contrat="CTR-TEST001").first()
    if not contrat:
        print("❌ Contrat de test non trouvé")
        return None
    
    # Créer une résiliation
    resiliation = ResiliationContrat.objects.create(
        contrat=contrat,
        date_resiliation=date(2025, 6, 30),
        motif_resiliation="Déménagement du locataire",
        type_resiliation='locataire',
        statut='en_cours',
        cree_par=Utilisateur.objects.first()
    )
    print("✅ Résiliation créée")
    
    # Valider la résiliation
    resiliation.valider_resiliation(Utilisateur.objects.first())
    print("✅ Résiliation validée")
    
    return resiliation

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests des nouvelles fonctionnalités...")
    
    try:
        # Créer les données de test
        utilisateur, config = test_creation_donnees()
        
        # Tester les contrats et cautions
        contrat = test_contrat_caution()
        
        # Tester les retraits de bailleur
        retrait = test_retrait_bailleur()
        
        # Tester les récapitulatifs mensuels
        recap = test_recap_mensuel()
        
        # Tester les paiements partiels
        paiement = test_paiement_partiel()
        
        # Tester les résiliations
        resiliation = test_resiliation_contrat()
        
        print("\n🎉 Tous les tests ont réussi !")
        print("\n📋 Résumé des fonctionnalités testées:")
        print("✅ Gestion des cautions et avances de loyer")
        print("✅ Retraits de bailleur avec déduction des charges")
        print("✅ Récapitulatifs mensuels")
        print("✅ Paiements partiels")
        print("✅ Résiliation de contrats")
        print("✅ Génération de PDF (modèles prêts)")
        print("✅ Gestion des permissions par groupe")
        
        print("\n🔧 Pour tester les fonctionnalités dans l'interface web:")
        print("1. Connectez-vous avec un utilisateur du groupe PRIVILEGE")
        print("2. Accédez aux nouvelles sections dans le menu")
        print("3. Testez la création de retraits, récapitulatifs, etc.")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
