#!/usr/bin/env python
"""
Script pour nettoyer les paiements orphelins (paiements sans contrat valide)
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat

def nettoyer_paiements_orphelins():
    """Nettoie les paiements orphelins"""
    print("NETTOYAGE DES PAIEMENTS ORPHELINS")
    print("=" * 40)
    
    # 1. Identifier les paiements orphelins
    print("\n1. IDENTIFICATION DES PAIEMENTS ORPHELINS:")
    paiements_orphelins = []
    
    for paiement in Paiement.objects.all():
        try:
            # Vérifier si le contrat existe et n'est pas supprimé
            contrat = Contrat.objects.get(id=paiement.contrat_id, is_deleted=False)
        except Contrat.DoesNotExist:
            paiements_orphelins.append(paiement)
    
    print(f"   Nombre de paiements orphelins: {len(paiements_orphelins)}")
    
    for paiement in paiements_orphelins:
        print(f"   - Paiement {paiement.id}: Contrat {paiement.contrat_id} - Type: {paiement.type_paiement} - Montant: {paiement.montant} F CFA")
    
    if not paiements_orphelins:
        print("   Aucun paiement orphelin trouvé.")
        return
    
    # 2. Proposer des solutions
    print("\n2. SOLUTIONS PROPOSEES:")
    print("   a) Supprimer les paiements orphelins")
    print("   b) Les associer à un contrat existant")
    print("   c) Créer des contrats temporaires")
    
    # 3. Solution automatique : supprimer les paiements orphelins
    print("\n3. SUPPRESSION AUTOMATIQUE DES PAIEMENTS ORPHELINS:")
    
    paiements_supprimes = 0
    for paiement in paiements_orphelins:
        try:
            print(f"   Suppression du paiement {paiement.id} (Contrat {paiement.contrat_id})...")
            paiement.delete()
            paiements_supprimes += 1
        except Exception as e:
            print(f"   ERREUR lors de la suppression du paiement {paiement.id}: {str(e)}")
    
    print(f"\n   RESULTAT: {paiements_supprimes} paiements orphelins supprimés")

def verifier_etat_apres_nettoyage():
    """Vérifie l'état après nettoyage"""
    print("\n4. VERIFICATION APRES NETTOYAGE:")
    print("=" * 40)
    
    # Vérifier les paiements d'avance restants
    paiements_avance = Paiement.objects.filter(
        type_paiement__in=['avance_loyer', 'avance'],
        statut='valide'
    )
    
    print(f"   Paiements d'avance restants: {paiements_avance.count()}")
    
    for paiement in paiements_avance:
        try:
            contrat = Contrat.objects.get(id=paiement.contrat_id, is_deleted=False)
            nom = contrat.locataire.get_nom_complet() if contrat.locataire else 'N/A'
            print(f"   - Paiement {paiement.id}: Contrat {paiement.contrat_id} ({nom}) - {paiement.montant} F CFA")
        except Contrat.DoesNotExist:
            print(f"   - Paiement {paiement.id}: Contrat {paiement.contrat_id} (ORPHELIN) - {paiement.montant} F CFA")
    
    # Vérifier les avances de loyer
    avances_loyer = AvanceLoyer.objects.all()
    print(f"\n   Avances de loyer existantes: {avances_loyer.count()}")
    
    for avance in avances_loyer:
        try:
            contrat = Contrat.objects.get(id=avance.contrat_id, is_deleted=False)
            nom = contrat.locataire.get_nom_complet() if contrat.locataire else 'N/A'
            print(f"   - Avance {avance.id}: Contrat {avance.contrat_id} ({nom}) - {avance.montant_avance} F CFA")
        except Contrat.DoesNotExist:
            print(f"   - Avance {avance.id}: Contrat {avance.contrat_id} (ORPHELIN) - {avance.montant_avance} F CFA")

if __name__ == "__main__":
    try:
        nettoyer_paiements_orphelins()
        verifier_etat_apres_nettoyage()
    except Exception as e:
        print(f"ERREUR lors du nettoyage: {str(e)}")
        import traceback
        traceback.print_exc()
