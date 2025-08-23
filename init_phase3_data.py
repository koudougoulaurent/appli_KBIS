#!/usr/bin/env python
"""
Script d'initialisation des données pour la Phase 3
Gestion des contrats et paiements
"""
import os
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien
from contrats.models import Contrat, Quittance, EtatLieux
from paiements.models import Paiement, Retrait, CompteBancaire

Utilisateur = get_user_model()


def create_contrats():
    """Crée des contrats de test."""
    print("🏠 Création des contrats...")
    
    # Récupérer les données existantes
    proprietes = list(Propriete.objects.filter(disponible=True)[:10])
    locataires = list(Locataire.objects.all()[:10])
    utilisateurs = list(Utilisateur.objects.filter(is_staff=True)[:3])
    
    if not proprietes or not locataires:
        print("❌ Pas assez de propriétés ou locataires pour créer des contrats")
        return
    
    # Types de contrats
    modes_paiement = ['virement', 'cheque', 'especes', 'prelevement']
    
    contrats_crees = []
    
    for i, propriete in enumerate(proprietes):
        if i >= len(locataires):
            break
            
        locataire = locataires[i]
        utilisateur = random.choice(utilisateurs)
        
        # Dates du contrat
        date_debut = date.today() - timedelta(days=random.randint(30, 365))
        date_fin = date_debut + timedelta(days=random.randint(365, 1095))  # 1-3 ans
        date_signature = date_debut - timedelta(days=random.randint(1, 30))
        
        # Montants
        loyer_mensuel = Decimal(str(random.randint(500, 2000)))
        charges_mensuelles = Decimal(str(random.randint(50, 200)))
        depot_garantie = loyer_mensuel + charges_mensuelles
        
        # Créer le contrat
        contrat = Contrat.objects.create(
            propriete=propriete,
            locataire=locataire,
            date_debut=date_debut,
            date_fin=date_fin,
            date_signature=date_signature,
            loyer_mensuel=loyer_mensuel,
            charges_mensuelles=charges_mensuelles,
            depot_garantie=depot_garantie,
            jour_paiement=random.randint(1, 28),
            mode_paiement=random.choice(modes_paiement),
            est_actif=random.choice([True, True, True, False]),  # 75% actifs
            est_resilie=random.choice([False, False, False, True]),  # 25% résiliés
            notes=f"Contrat de test {i+1}",
            cree_par=utilisateur
        )
        
        # Marquer la propriété comme louée
        propriete.disponible = False
        propriete.save()
        
        contrats_crees.append(contrat)
        print(f"✅ Contrat créé: {contrat.numero_contrat} - {propriete.titre}")
    
    print(f"🎉 {len(contrats_crees)} contrats créés")
    return contrats_crees


def create_quittances(contrats):
    """Crée des quittances pour les contrats."""
    print("📄 Création des quittances...")
    
    quittances_crees = 0
    
    for contrat in contrats:
        if not contrat.est_actif or contrat.est_resilie:
            continue
            
        # Créer des quittances pour les 6 derniers mois
        for i in range(6):
            mois = date.today() - timedelta(days=30 * i)
            mois = mois.replace(day=1)
            
            # Vérifier si la quittance existe déjà
            if Quittance.objects.filter(contrat=contrat, mois=mois).exists():
                continue
                
            montant_loyer = contrat.loyer_mensuel
            montant_charges = contrat.charges_mensuelles
            
            quittance = Quittance.objects.create(
                contrat=contrat,
                mois=mois,
                montant_loyer=montant_loyer,
                montant_charges=montant_charges,
                montant_total=montant_loyer + montant_charges
            )
            
            quittances_crees += 1
            print(f"✅ Quittance créée: {quittance.numero_quittance}")
    
    print(f"🎉 {quittances_crees} quittances créées")


def create_etats_lieux(contrats):
    """Crée des états des lieux pour les contrats."""
    print("🏠 Création des états des lieux...")
    
    etats_crees = 0
    utilisateurs = list(Utilisateur.objects.filter(is_staff=True)[:3])
    
    for contrat in contrats:
        utilisateur = random.choice(utilisateurs)
        
        # État des lieux d'entrée
        etat_entree = EtatLieux.objects.create(
            contrat=contrat,
            type_etat='entree',
            date_etat=contrat.date_debut,
            observations_generales=f"État des lieux d'entrée pour {contrat.propriete.titre}",
            etat_murs=random.choice(['excellent', 'bon', 'moyen']),
            etat_sol=random.choice(['excellent', 'bon', 'moyen']),
            etat_plomberie=random.choice(['excellent', 'bon', 'moyen']),
            etat_electricite=random.choice(['excellent', 'bon', 'moyen']),
            notes="État des lieux d'entrée",
            cree_par=utilisateur
        )
        
        etats_crees += 1
        print(f"✅ État des lieux créé: Entrée - {contrat.numero_contrat}")
        
        # État des lieux de sortie (si contrat résilié)
        if contrat.est_resilie:
            etat_sortie = EtatLieux.objects.create(
                contrat=contrat,
                type_etat='sortie',
                date_etat=contrat.date_resiliation or contrat.date_fin,
                observations_generales=f"État des lieux de sortie pour {contrat.propriete.titre}",
                etat_murs=random.choice(['excellent', 'bon', 'moyen']),
                etat_sol=random.choice(['excellent', 'bon', 'moyen']),
                etat_plomberie=random.choice(['excellent', 'bon', 'moyen']),
                etat_electricite=random.choice(['excellent', 'bon', 'moyen']),
                notes="État des lieux de sortie",
                cree_par=utilisateur
            )
            
            etats_crees += 1
            print(f"✅ État des lieux créé: Sortie - {contrat.numero_contrat}")
    
    print(f"🎉 {etats_crees} états des lieux créés")


def create_paiements(contrats):
    """Crée des paiements pour les contrats."""
    print("💰 Création des paiements...")
    
    paiements_crees = 0
    utilisateurs = list(Utilisateur.objects.filter(is_staff=True)[:3])
    
    types_paiement = ['loyer', 'charges', 'depot_garantie', 'regularisation']
    modes_paiement = ['virement', 'cheque', 'especes', 'prelevement', 'carte']
    statuts = ['valide', 'valide', 'valide', 'en_attente', 'refuse']  # 60% validés
    
    for contrat in contrats:
        if not contrat.est_actif:
            continue
            
        utilisateur = random.choice(utilisateurs)
        
        # Créer des paiements pour les 6 derniers mois
        for i in range(6):
            date_paiement = date.today() - timedelta(days=30 * i)
            
            # Paiement de loyer
            paiement_loyer = Paiement.objects.create(
                contrat=contrat,
                montant=contrat.loyer_mensuel,
                type_paiement='loyer',
                statut=random.choice(statuts),
                mode_paiement=random.choice(modes_paiement),
                date_paiement=date_paiement,
                date_encaissement=date_paiement if random.choice(statuts) == 'valide' else None,
                numero_cheque=f"CHQ{random.randint(100000, 999999)}" if random.choice(modes_paiement) == 'cheque' else "",
                reference_virement=f"VIR{random.randint(100000, 999999)}" if random.choice(modes_paiement) == 'virement' else "",
                notes=f"Paiement loyer {date_paiement.strftime('%B %Y')}",
                cree_par=utilisateur,
                valide_par=utilisateur if random.choice(statuts) == 'valide' else None
            )
            
            paiements_crees += 1
            
            # Paiement de charges (occasionnel)
            if random.choice([True, False]):
                paiement_charges = Paiement.objects.create(
                    contrat=contrat,
                    montant=contrat.charges_mensuelles,
                    type_paiement='charges',
                    statut=random.choice(statuts),
                    mode_paiement=random.choice(modes_paiement),
                    date_paiement=date_paiement,
                    date_encaissement=date_paiement if random.choice(statuts) == 'valide' else None,
                    numero_cheque=f"CHQ{random.randint(100000, 999999)}" if random.choice(modes_paiement) == 'cheque' else "",
                    reference_virement=f"VIR{random.randint(100000, 999999)}" if random.choice(modes_paiement) == 'virement' else "",
                    notes=f"Paiement charges {date_paiement.strftime('%B %Y')}",
                    cree_par=utilisateur,
                    valide_par=utilisateur if random.choice(statuts) == 'valide' else None
                )
                
                paiements_crees += 1
    
    print(f"🎉 {paiements_crees} paiements créés")


def create_retraits():
    """Crée des retraits pour les bailleurs."""
    print("💸 Création des retraits...")
    
    retraits_crees = 0
    bailleurs = list(Bailleur.objects.all()[:10])
    utilisateurs = list(Utilisateur.objects.filter(is_staff=True)[:3])
    
    if not bailleurs:
        print("❌ Pas de bailleurs pour créer des retraits")
        return
    
    types_retrait = ['loyers', 'charges', 'depot_garantie', 'frais_agence']
    modes_retrait = ['virement', 'cheque', 'especes']
    statuts = ['valide', 'valide', 'en_attente']  # 66% validés
    
    for i, bailleur in enumerate(bailleurs):
        utilisateur = random.choice(utilisateurs)
        
        # Créer 2-4 retraits par bailleur
        for j in range(random.randint(2, 4)):
            date_demande = date.today() - timedelta(days=random.randint(30, 180))
            
            retrait = Retrait.objects.create(
                bailleur=bailleur,
                montant=Decimal(str(random.randint(500, 3000))),
                type_retrait=random.choice(types_retrait),
                statut=random.choice(statuts),
                mode_retrait=random.choice(modes_retrait),
                date_demande=date_demande,
                date_versement=date_demande if random.choice(statuts) == 'valide' else None,
                numero_cheque=f"CHQ{random.randint(100000, 999999)}" if random.choice(modes_retrait) == 'cheque' else "",
                reference_virement=f"VIR{random.randint(100000, 999999)}" if random.choice(modes_retrait) == 'virement' else "",
                notes=f"Retrait {j+1} pour {bailleur.nom}",
                cree_par=utilisateur,
                valide_par=utilisateur if random.choice(statuts) == 'valide' else None
            )
            
            retraits_crees += 1
            print(f"✅ Retrait créé: {retrait.id} - {bailleur.nom}")
    
    print(f"🎉 {retraits_crees} retraits créés")


def create_comptes_bancaires():
    """Crée des comptes bancaires de test."""
    print("🏦 Création des comptes bancaires...")
    
    comptes_data = [
        {
            'nom': 'Compte Principal',
            'banque': 'Banque Populaire',
            'iban': 'FR7630001007941234567890185',
            'bic': 'BPPBFRPP',
            'solde_actuel': Decimal('15000.00'),
            'devise': 'EUR',
            'est_actif': True,
            'notes': 'Compte principal de l\'agence'
        },
        {
            'nom': 'Compte Épargne',
            'banque': 'Crédit Agricole',
            'iban': 'FR1420041010050500013M02606',
            'bic': 'CRLYFRPP',
            'solde_actuel': Decimal('25000.00'),
            'devise': 'EUR',
            'est_actif': True,
            'notes': 'Compte épargne pour les dépôts de garantie'
        },
        {
            'nom': 'Compte Opérationnel',
            'banque': 'BNP Paribas',
            'iban': 'FR7630006000011234567890189',
            'bic': 'BNPAFRPP',
            'solde_actuel': Decimal('5000.00'),
            'devise': 'EUR',
            'est_actif': True,
            'notes': 'Compte pour les opérations courantes'
        }
    ]
    
    comptes_crees = 0
    
    for compte_data in comptes_data:
        # Vérifier si le compte existe déjà
        if CompteBancaire.objects.filter(iban=compte_data['iban']).exists():
            print(f"⚠️ Compte {compte_data['nom']} existe déjà")
            continue
            
        compte = CompteBancaire.objects.create(**compte_data)
        comptes_crees += 1
        print(f"✅ Compte créé: {compte.nom} - {compte.iban}")
    
    print(f"🎉 {comptes_crees} comptes bancaires créés")


def main():
    """Fonction principale."""
    print("🚀 INITIALISATION PHASE 3 - CONTRATS ET PAIEMENTS")
    print("=" * 60)
    
    try:
        # 1. Créer les contrats
        contrats = create_contrats()
        
        if contrats:
            # 2. Créer les quittances
            create_quittances(contrats)
            
            # 3. Créer les états des lieux
            create_etats_lieux(contrats)
            
            # 4. Créer les paiements
            create_paiements(contrats)
        
        # 5. Créer les retraits
        create_retraits()
        
        # 6. Créer les comptes bancaires
        create_comptes_bancaires()
        
        print("\n🎉 INITIALISATION PHASE 3 TERMINÉE AVEC SUCCÈS !")
        print("\n📊 Statistiques créées:")
        print(f"   - Contrats: {Contrat.objects.count()}")
        print(f"   - Quittances: {Quittance.objects.count()}")
        print(f"   - États des lieux: {EtatLieux.objects.count()}")
        print(f"   - Paiements: {Paiement.objects.count()}")
        print(f"   - Retraits: {Retrait.objects.count()}")
        print(f"   - Comptes bancaires: {CompteBancaire.objects.count()}")
        
        print("\n🌐 Accès:")
        print("   - Dashboard: http://127.0.0.1:8000/")
        print("   - Admin: http://127.0.0.1:8000/admin/")
        print("   - API Interface: http://127.0.0.1:8000/api/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main() 