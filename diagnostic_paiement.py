"""
Script de diagnostic pour comprendre pourquoi le prochain paiement est en février
au lieu de décembre après une avance de novembre.
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat
from datetime import date
from dateutil.relativedelta import relativedelta


def diagnostic_contrat():
    """Diagnostic du contrat avec le problème de paiement"""
    
    # Trouver tous les derniers paiements récents
    print("🔍 Recherche des derniers paiements...")
    
    tous_paiements = Paiement.objects.filter(
        statut='valide',
        is_deleted=False
    ).order_by('-date_paiement')[:20]
    
    print(f"   Trouvé {len(tous_paiements)} paiements récents\n")
    
    if not tous_paiements:
        print("❌ Aucun paiement trouvé dans le système")
        return
    
    # Afficher les derniers paiements
    print("📋 DERNIERS PAIEMENTS:")
    for p in tous_paiements:
        print(f"   {p.date_paiement} - {p.montant:,.0f} F - {p.type_paiement} - {p.mois_paye or 'N/A'} - Contrat: {p.contrat.id}")
    
    # Chercher spécifiquement les paiements pour le contrat qui pose problème
    # D'après la capture, on cherche un contrat avec une avance de novembre
    print("\n🔍 Analyse des avances de novembre...")
    
    paiements_novembre = [p for p in tous_paiements if p.mois_paye and 'novembre' in p.mois_paye.lower()]
    
    if not paiements_novembre:
        print("❌ Aucun paiement trouvé pour novembre")
        # Prendre le premier paiement partiel récent
        dernier_paiement_nov = tous_paiements[0]
    else:
        dernier_paiement_nov = paiements_novembre[0]
    
    contrat = dernier_paiement_nov.contrat
    
    print("=" * 80)
    print("📋 DIAGNOSTIC DU PROBLÈME DE PAIEMENT")
    print("=" * 80)
    print(f"\n📍 Contrat: {contrat}")
    print(f"📍 Locataire: {contrat.locataire.get_nom_complet()}")
    print(f"📍 Propriété: {contrat.unite_locative}")
    
    loyer_total = contrat.get_loyer_total()
    if isinstance(loyer_total, str):
        loyer_total = float(loyer_total.replace(',', '').replace(' ', ''))
    print(f"📍 Loyer mensuel du contrat: {loyer_total:,.0f} F CFA")
    
    print(f"\n💰 Dernier paiement trouvé:")
    print(f"   - Date: {dernier_paiement_nov.date_paiement}")
    print(f"   - Montant: {dernier_paiement_nov.montant:,.0f} F CFA")
    print(f"   - Type: {dernier_paiement_nov.type_paiement}")
    print(f"   - Mois payé: {dernier_paiement_nov.mois_paye}")
    print(f"   - Statut: {dernier_paiement_nov.statut}")
    
    # Chercher les avances actives
    avances = AvanceLoyer.objects.filter(
        contrat=contrat,
        statut='active'
    ).order_by('-date_avance')
    
    print(f"\n🏦 Avances de loyer actives: {avances.count()}")
    for i, avance in enumerate(avances, 1):
        print(f"\n   Avance #{i}:")
        print(f"   - Date: {avance.date_avance}")
        print(f"   - Montant: {avance.montant_avance:,.0f} F CFA")
        print(f"   - Loyer mensuel utilisé: {avance.loyer_mensuel:,.0f} F CFA")
        print(f"   - Nombre de mois couverts: {avance.nombre_mois_couverts}")
        print(f"   - Montant restant: {avance.montant_restant:,.0f} F CFA")
        print(f"   - Début couverture: {avance.mois_debut_couverture}")
        print(f"   - Fin couverture: {avance.mois_fin_couverture}")
        print(f"   - Mode sélection: {avance.mode_selection_mois}")
        
        # Liste des mois couverts
        mois_couverts = avance.get_mois_couverts_liste()
        print(f"   - Mois couverts:")
        for mois in mois_couverts:
            print(f"     • {mois.strftime('%B %Y')}")
    
    # Calculer le prochain mois de paiement selon le système actuel
    print(f"\n🔍 CALCUL DU PROCHAIN MOIS DE PAIEMENT:")
    try:
        prochain_mois = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
        print(f"   ✅ Prochain mois calculé: {prochain_mois.strftime('%B %Y')}")
        print(f"   📅 Date complète: {prochain_mois}")
    except Exception as e:
        print(f"   ❌ Erreur lors du calcul: {e}")
        import traceback
        traceback.print_exc()
    
    # Analyse du problème
    print(f"\n🔎 ANALYSE DU PROBLÈME:")
    print(f"   Dernier paiement: Novembre 2025")
    print(f"   Prochain paiement attendu logiquement: Décembre 2025")
    print(f"   Prochain paiement calculé par le système: Février 2026")
    print(f"\n   ⚠️ DÉCALAGE DÉTECTÉ: {(prochain_mois - date(2025, 12, 1)).days // 30} mois de différence")
    
    # Vérification manuelle mois par mois
    print(f"\n📊 VÉRIFICATION MOIS PAR MOIS:")
    mois_actuel = date(2025, 11, 1)  # Novembre 2025
    for i in range(6):  # Vérifier 6 mois
        mois_test = mois_actuel + relativedelta(months=i+1)
        est_couvert = False
        
        for avance in avances:
            if avance.mois_debut_couverture <= mois_test <= avance.mois_fin_couverture:
                est_couvert = True
                break
        
        statut = "✅ COUVERT par avance" if est_couvert else "❌ NON COUVERT (paiement requis)"
        print(f"   {mois_test.strftime('%B %Y')}: {statut}")
    
    # Recommandation
    print(f"\n💡 RECOMMANDATION:")
    if avances.exists():
        avance = avances.first()
        montant_par_mois = avance.montant_avance / avance.nombre_mois_couverts if avance.nombre_mois_couverts > 0 else 0
        
        if montant_par_mois != contrat.get_loyer_total():
            print(f"   ⚠️ PROBLÈME DÉTECTÉ:")
            print(f"   Le loyer mensuel utilisé dans l'avance ({avance.loyer_mensuel:,.0f} F CFA)")
            print(f"   ne correspond pas au loyer réel du contrat ({contrat.get_loyer_total():,.0f} F CFA)")
            print(f"\n   🔧 SOLUTION:")
            print(f"   1. Vérifier le montant de l'avance: {avance.montant_avance:,.0f} F CFA")
            print(f"   2. Si c'est une avance pour UN SEUL MOIS (novembre), le montant devrait être")
            print(f"      égal au loyer mensuel: {contrat.get_loyer_total():,.0f} F CFA")
            print(f"   3. Si l'avance est bien de {avance.montant_avance:,.0f} F CFA et couvre")
            print(f"      {avance.nombre_mois_couverts} mois, alors le prochain paiement est correct.")
        else:
            print(f"   ✅ Le calcul semble correct selon les données enregistrées.")
            print(f"   L'avance couvre {avance.nombre_mois_couverts} mois.")


if __name__ == "__main__":
    diagnostic_contrat()
