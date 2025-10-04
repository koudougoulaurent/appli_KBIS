"""
Script de test pour le système intelligent des charges bailleur.
"""

import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from proprietes.models import ChargesBailleur, Bailleur, Propriete
from paiements.models import RecapMensuel, RetraitBailleur
from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent


def test_creation_charges_bailleur():
    """Test de création de charges bailleur."""
    print("🧪 Test de création de charges bailleur...")
    
    try:
        # Récupérer un bailleur et une propriété existants
        bailleur = Bailleur.objects.first()
        if not bailleur:
            print("❌ Aucun bailleur trouvé")
            return False
        
        propriete = bailleur.proprietes.first()
        if not propriete:
            print("❌ Aucune propriété trouvée pour ce bailleur")
            return False
        
        # Créer une charge bailleur de test
        charge = ChargesBailleur.objects.create(
            propriete=propriete,
            titre="Test - Réparation chaudière",
            description="Réparation de la chaudière de l'appartement",
            type_charge="reparation",
            priorite="haute",
            montant=Decimal('150000'),
            date_charge=date.today(),
            cree_par=bailleur.user if hasattr(bailleur, 'user') else None
        )
        
        print(f"✅ Charge créée: {charge.numero_charge} - {charge.titre}")
        print(f"   Montant: {charge.montant} F CFA")
        print(f"   Statut: {charge.get_statut_display()}")
        print(f"   Peut être déduite: {charge.peut_etre_deduit()}")
        
        return charge
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la charge: {e}")
        return False


def test_calcul_charges_mois():
    """Test du calcul des charges pour un mois."""
    print("\n🧪 Test du calcul des charges pour un mois...")
    
    try:
        # Récupérer un bailleur
        bailleur = Bailleur.objects.first()
        if not bailleur:
            print("❌ Aucun bailleur trouvé")
            return False
        
        # Calculer les charges pour le mois actuel
        mois_actuel = date.today().replace(day=1)
        charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
            bailleur, mois_actuel
        )
        
        print(f"✅ Calcul des charges pour {mois_actuel.strftime('%B %Y')}")
        print(f"   Total charges: {charges_data['total_charges']} F CFA")
        print(f"   Nombre de charges: {charges_data['nombre_charges']}")
        print(f"   Charges par propriété: {len(charges_data['charges_par_propriete'])}")
        
        return charges_data
        
    except Exception as e:
        print(f"❌ Erreur lors du calcul des charges: {e}")
        return False


def test_integration_retrait():
    """Test de l'intégration des charges dans un retrait."""
    print("\n🧪 Test de l'intégration des charges dans un retrait...")
    
    try:
        # Récupérer un retrait existant ou en créer un
        retrait = RetraitBailleur.objects.filter(
            is_deleted=False
        ).first()
        
        if not retrait:
            print("❌ Aucun retrait trouvé")
            return False
        
        # Intégrer les charges
        resultat = ServiceChargesBailleurIntelligent.integrer_charges_dans_retrait(retrait)
        
        if resultat.get('success'):
            print(f"✅ Intégration réussie")
            print(f"   Montant initial: {resultat['montant_initial']} F CFA")
            print(f"   Total charges: {resultat['total_charges']} F CFA")
            print(f"   Montant net: {resultat['montant_net']} F CFA")
            print(f"   Charges déduites: {resultat['nombre_charges']}")
        else:
            print(f"❌ Échec de l'intégration: {resultat.get('erreur')}")
        
        return resultat
        
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration: {e}")
        return False


def test_integration_recap():
    """Test de l'intégration des charges dans un récapitulatif."""
    print("\n🧪 Test de l'intégration des charges dans un récapitulatif...")
    
    try:
        # Récupérer un récapitulatif existant ou en créer un
        recap = RecapMensuel.objects.filter(
            is_deleted=False
        ).first()
        
        if not recap:
            print("❌ Aucun récapitulatif trouvé")
            return False
        
        # Intégrer les charges
        resultat = ServiceChargesBailleurIntelligent.integrer_charges_dans_recap(recap)
        
        if resultat.get('success'):
            print(f"✅ Intégration réussie")
            print(f"   Montant initial: {resultat['montant_initial']} F CFA")
            print(f"   Total charges: {resultat['total_charges']} F CFA")
            print(f"   Montant net: {resultat['montant_net']} F CFA")
            print(f"   Nombre de charges: {resultat['nombre_charges']}")
        else:
            print(f"❌ Échec de l'intégration: {resultat.get('erreur')}")
        
        return resultat
        
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration: {e}")
        return False


def test_rapport_charges():
    """Test de génération de rapport des charges."""
    print("\n🧪 Test de génération de rapport des charges...")
    
    try:
        # Récupérer un bailleur
        bailleur = Bailleur.objects.first()
        if not bailleur:
            print("❌ Aucun bailleur trouvé")
            return False
        
        # Générer le rapport pour le mois actuel
        mois_actuel = date.today().replace(day=1)
        rapport = ServiceChargesBailleurIntelligent.generer_rapport_charges_bailleur(
            bailleur, mois_actuel
        )
        
        if not rapport.get('erreur'):
            print(f"✅ Rapport généré pour {bailleur.get_nom_complet()}")
            print(f"   Mois: {rapport['mois'].strftime('%B %Y')}")
            print(f"   Total charges: {rapport['resume']['total_charges']} F CFA")
            print(f"   Nombre de charges: {rapport['resume']['nombre_charges']}")
            print(f"   Montant net final: {rapport['resume']['montant_net_final']} F CFA")
            print(f"   Impact sur retrait: {rapport['resume']['impact_sur_retrait']} F CFA")
            print(f"   Pourcentage d'impact: {rapport['resume']['pourcentage_impact']:.2f}%")
        else:
            print(f"❌ Erreur lors de la génération du rapport: {rapport['erreur']}")
        
        return rapport
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return False


def test_impact_paiements():
    """Test du calcul de l'impact sur les paiements."""
    print("\n🧪 Test du calcul de l'impact sur les paiements...")
    
    try:
        # Récupérer un bailleur
        bailleur = Bailleur.objects.first()
        if not bailleur:
            print("❌ Aucun bailleur trouvé")
            return False
        
        # Calculer l'impact pour le mois actuel
        mois_actuel = date.today().replace(day=1)
        impact = ServiceChargesBailleurIntelligent.calculer_impact_charges_sur_paiements(
            bailleur, mois_actuel
        )
        
        if not impact.get('erreur'):
            print(f"✅ Impact calculé pour {bailleur.get_nom_complet()}")
            print(f"   Mois: {impact['mois'].strftime('%B %Y')}")
            print(f"   Total loyers bruts: {impact['total_loyers_bruts']} F CFA")
            print(f"   Total charges déductibles: {impact['total_charges_deductibles']} F CFA")
            print(f"   Total charges bailleur: {impact['total_charges_bailleur']} F CFA")
            print(f"   Montant net final: {impact['montant_net_final']} F CFA")
            print(f"   Propriétés analysées: {len(impact['proprietes_analysees'])}")
        else:
            print(f"❌ Erreur lors du calcul de l'impact: {impact['erreur']}")
        
        return impact
        
    except Exception as e:
        print(f"❌ Erreur lors du calcul de l'impact: {e}")
        return False


def main():
    """Fonction principale de test."""
    print("🚀 DÉMARRAGE DES TESTS DU SYSTÈME DE CHARGES BAILLEUR")
    print("=" * 60)
    
    # Tests
    tests = [
        test_creation_charges_bailleur,
        test_calcul_charges_mois,
        test_integration_retrait,
        test_integration_recap,
        test_rapport_charges,
        test_impact_paiements,
    ]
    
    resultats = []
    for test in tests:
        try:
            resultat = test()
            resultats.append(resultat is not False)
        except Exception as e:
            print(f"❌ Erreur critique dans le test: {e}")
            resultats.append(False)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    tests_reussis = sum(resultats)
    total_tests = len(tests)
    
    print(f"Tests réussis: {tests_reussis}/{total_tests}")
    print(f"Taux de réussite: {(tests_reussis/total_tests)*100:.1f}%")
    
    if tests_reussis == total_tests:
        print("🎉 Tous les tests sont passés avec succès!")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return tests_reussis == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
