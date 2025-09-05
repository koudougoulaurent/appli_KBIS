#!/usr/bin/env python
"""
Script de test pour le système de reçus de récapitulatifs
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Bailleur, Propriete
from contrats.models import Contrat
from paiements.models import RecapitulatifMensuelBailleur, RecuRecapitulatif
from paiements.services_recus import service_recus
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

def test_creation_recu():
    """Test de création d'un reçu."""
    
    print("🔍 Test de création d'un reçu")
    print("=" * 50)
    
    # Récupérer un récapitulatif existant
    recapitulatif = RecapitulatifMensuelBailleur.objects.filter(
        bailleur__proprietes__contrats__est_actif=True
    ).first()
    
    if not recapitulatif:
        print("❌ Aucun récapitulatif trouvé pour le test")
        return False
    
    print(f"✅ Récapitulatif testé: {recapitulatif}")
    print(f"✅ Bailleur: {recapitulatif.bailleur.get_nom_complet()}")
    print(f"✅ Période: {recapitulatif.mois_recapitulatif.strftime('%B %Y')}")
    
    # Vérifier si un reçu existe déjà
    if hasattr(recapitulatif, 'recu'):
        print(f"ℹ️  Un reçu existe déjà: {recapitulatif.recu.numero_recu}")
        recu = recapitulatif.recu
    else:
        # Créer un nouveau reçu
        try:
            recu = service_recus.generer_recu_automatique(recapitulatif)
            print(f"✅ Reçu créé avec succès: {recu.numero_recu}")
        except Exception as e:
            print(f"❌ Erreur lors de la création du reçu: {e}")
            return False
    
    # Vérifier les propriétés du reçu
    print(f"\n📋 Propriétés du reçu:")
    print(f"   Numéro: {recu.numero_recu}")
    print(f"   Type: {recu.get_type_recu_display()}")
    print(f"   Template: {recu.get_template_utilise_display()}")
    print(f"   Format: {recu.get_format_impression_display()}")
    print(f"   Statut: {recu.get_statut_display()}")
    print(f"   Date de création: {recu.date_creation}")
    print(f"   Hash de sécurité: {recu.hash_securite[:16]}...")
    
    return True

def test_calcul_totaux():
    """Test du calcul des totaux."""
    
    print("\n🔍 Test du calcul des totaux")
    print("=" * 50)
    
    # Récupérer un récapitulatif avec reçu
    recapitulatif = RecapitulatifMensuelBailleur.objects.filter(
        recu__isnull=False
    ).first()
    
    if not recapitulatif:
        print("❌ Aucun récapitulatif avec reçu trouvé")
        return False
    
    recu = recapitulatif.recu
    print(f"✅ Reçu testé: {recu.numero_recu}")
    
    # Calculer les totaux
    totaux = recapitulatif.calculer_totaux_bailleur()
    
    print(f"\n📊 Totaux calculés:")
    print(f"   Nombre de propriétés: {totaux['nombre_proprietes']}")
    print(f"   Loyers attendus: {totaux['total_loyers_bruts']} F CFA")
    print(f"   Charges déductibles: {totaux['total_charges_deductibles']} F CFA")
    print(f"   Montant net: {totaux['total_net_a_payer']} F CFA")
    
    # Vérifier que les montants ne sont pas à 0
    if totaux['total_loyers_bruts'] > 0:
        print("✅ Les montants sont correctement calculés")
        return True
    else:
        print("❌ Les montants sont à 0")
        return False

def test_generation_lot():
    """Test de génération en lot."""
    
    print("\n🔍 Test de génération en lot")
    print("=" * 50)
    
    # Récupérer plusieurs récapitulatifs sans reçu
    recapitulatifs = RecapitulatifMensuelBailleur.objects.filter(
        recu__isnull=True,
        statut__in=['valide', 'envoye']
    )[:3]  # Limiter à 3 pour le test
    
    if not recapitulatifs:
        print("❌ Aucun récapitulatif sans reçu trouvé")
        return False
    
    print(f"✅ {recapitulatifs.count()} récapitulatifs trouvés pour le test")
    
    # Générer les reçus en lot
    try:
        recus_crees = service_recus.generer_recus_lot(recapitulatifs)
        print(f"✅ {len(recus_crees)} reçus créés en lot")
        
        for recu in recus_crees:
            print(f"   - {recu.numero_recu} pour {recu.recapitulatif.bailleur.get_nom_complet()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération en lot: {e}")
        return False

def test_validation_recus():
    """Test de validation des reçus."""
    
    print("\n🔍 Test de validation des reçus")
    print("=" * 50)
    
    # Récupérer des reçus en brouillon
    recus_brouillons = RecuRecapitulatif.objects.filter(statut='brouillon')[:2]
    
    if not recus_brouillons:
        print("❌ Aucun reçu en brouillon trouvé")
        return False
    
    print(f"✅ {recus_brouillons.count()} reçus en brouillon trouvés")
    
    # Valider les reçus
    try:
        count = service_recus.valider_recus_lot(recus_brouillons, None)
        print(f"✅ {count} reçus validés")
        
        # Vérifier le statut
        for recu in recus_brouillons:
            recu.refresh_from_db()
            print(f"   - {recu.numero_recu}: {recu.get_statut_display()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        return False

def test_rapport_recus():
    """Test de génération de rapport."""
    
    print("\n🔍 Test de génération de rapport")
    print("=" * 50)
    
    # Période de test (30 derniers jours)
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=30)
    
    try:
        rapport = service_recus.generer_rapport_recus(date_debut, date_fin)
        
        print(f"✅ Rapport généré pour la période {date_debut} à {date_fin}")
        print(f"\n📊 Statistiques:")
        print(f"   Total: {rapport['statistiques']['total']}")
        print(f"   Brouillons: {rapport['statistiques']['brouillons']}")
        print(f"   Validés: {rapport['statistiques']['valides']}")
        print(f"   Imprimés: {rapport['statistiques']['imprimes']}")
        print(f"   Envoyés: {rapport['statistiques']['envoyes']}")
        print(f"   Archivés: {rapport['statistiques']['archives']}")
        
        print(f"\n📋 Par type:")
        for type_recu, count in rapport['par_type'].items():
            print(f"   {type_recu}: {count}")
        
        print(f"\n📋 Par template:")
        for template, count in rapport['par_template'].items():
            print(f"   {template}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return False

def test_nettoyage():
    """Test de nettoyage des reçus."""
    
    print("\n🔍 Test de nettoyage des reçus")
    print("=" * 50)
    
    # Compter les reçus avant nettoyage
    recus_avant = RecuRecapitulatif.objects.count()
    print(f"✅ Reçus avant nettoyage: {recus_avant}")
    
    # Nettoyer les reçus brouillons anciens (plus de 1 jour pour le test)
    try:
        count_supprimes = service_recus.nettoyer_recus_brouillons(jours=1)
        print(f"✅ {count_supprimes} reçus brouillons supprimés")
        
        # Compter les reçus après nettoyage
        recus_apres = RecuRecapitulatif.objects.count()
        print(f"✅ Reçus après nettoyage: {recus_apres}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

def main():
    """Fonction principale de test."""
    
    print("🚀 Démarrage des tests du système de reçus")
    print("=" * 60)
    
    tests = [
        ("Création de reçu", test_creation_recu),
        ("Calcul des totaux", test_calcul_totaux),
        ("Génération en lot", test_generation_lot),
        ("Validation des reçus", test_validation_recus),
        ("Génération de rapport", test_rapport_recus),
        ("Nettoyage des reçus", test_nettoyage),
    ]
    
    resultats = []
    
    for nom_test, fonction_test in tests:
        try:
            resultat = fonction_test()
            resultats.append((nom_test, resultat))
        except Exception as e:
            print(f"❌ Erreur lors du test '{nom_test}': {e}")
            resultats.append((nom_test, False))
    
    # Affichage des résultats
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    for nom_test, resultat in resultats:
        status = "✅ RÉUSSI" if resultat else "❌ ÉCHOUÉ"
        print(f"{nom_test}: {status}")
    
    # Résumé
    reussis = sum(1 for _, resultat in resultats if resultat)
    total = len(resultats)
    
    print(f"\n📈 Résumé: {reussis}/{total} tests réussis")
    
    if reussis == total:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ Le système de reçus fonctionne correctement")
    else:
        print(f"\n⚠️  {total - reussis} TEST(S) ONT ÉCHOUÉ")
        print("❌ Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
