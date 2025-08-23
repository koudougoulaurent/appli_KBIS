#!/usr/bin/env python
"""
Script pour vérifier les champs décimaux dans la base de données
et identifier les valeurs invalides qui causent l'erreur InvalidOperation.
"""

import os
import sys
import django
from decimal import Decimal, InvalidOperation

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.models import Contrat
from proprietes.models import Propriete
from paiements.models import Paiement
from utilisateurs.models import Utilisateur

def verifier_champs_decimaux():
    """Vérifie tous les champs décimaux pour identifier les valeurs invalides."""
    
    print("=== VÉRIFICATION DES CHAMPS DÉCIMAUX ===\n")
    
    # Vérification des contrats
    print("1. Vérification des contrats...")
    contrats_problematiques = []
    
    try:
        contrats = Contrat.objects.all()
        print(f"   Total des contrats: {contrats.count()}")
        
        for contrat in contrats:
            try:
                # Vérification des champs décimaux
                loyer = contrat.loyer_mensuel
                charges = contrat.charges_mensuelles
                depot = contrat.depot_garantie
                avance = contrat.avance_loyer
                
                # Test de conversion
                float(loyer)
                float(charges)
                float(depot)
                float(avance)
                
            except (ValueError, TypeError, InvalidOperation) as e:
                contrats_problematiques.append({
                    'id': contrat.id,
                    'numero': contrat.numero_contrat,
                    'erreur': str(e),
                    'loyer': contrat.loyer_mensuel,
                    'charges': contrat.charges_mensuelles,
                    'depot': contrat.depot_garantie,
                    'avance': contrat.avance_loyer
                })
                
    except Exception as e:
        print(f"   Erreur lors de la vérification des contrats: {e}")
    
    if contrats_problematiques:
        print(f"   ❌ {len(contrats_problematiques)} contrats avec des valeurs décimales invalides:")
        for c in contrats_problematiques:
            print(f"      - Contrat {c['numero']} (ID: {c['id']}): {c['erreur']}")
            print(f"        Loyer: {c['loyer']}, Charges: {c['charges']}, Dépôt: {c['depot']}, Avance: {c['avance']}")
    else:
        print("   ✅ Tous les contrats ont des valeurs décimales valides")
    
    # Vérification des propriétés
    print("\n2. Vérification des propriétés...")
    proprietes_problematiques = []
    
    try:
        proprietes = Propriete.objects.all()
        print(f"   Total des propriétés: {proprietes.count()}")
        
        for propriete in proprietes:
            try:
                # Vérification des champs décimaux
                prix = propriete.prix_vente
                loyer = propriete.loyer_mensuel
                charges = propriete.charges_mensuelles
                
                # Test de conversion
                if prix:
                    float(prix)
                if loyer:
                    float(loyer)
                if charges:
                    float(charges)
                    
            except (ValueError, TypeError, InvalidOperation) as e:
                proprietes_problematiques.append({
                    'id': propriete.id,
                    'titre': propriete.titre,
                    'erreur': str(e),
                    'prix': propriete.prix_vente,
                    'loyer': propriete.loyer_mensuel,
                    'charges': propriete.charges_mensuelles
                })
                
    except Exception as e:
        print(f"   Erreur lors de la vérification des propriétés: {e}")
    
    if proprietes_problematiques:
        print(f"   ❌ {len(proprietes_problematiques)} propriétés avec des valeurs décimales invalides:")
        for p in proprietes_problematiques:
            print(f"      - Propriété {p['titre']} (ID: {p['id']}): {p['erreur']}")
            print(f"        Prix: {p['prix']}, Loyer: {p['loyer']}, Charges: {p['charges']}")
    else:
        print("   ✅ Toutes les propriétés ont des valeurs décimales valides")
    
    # Vérification des paiements
    print("\n3. Vérification des paiements...")
    paiements_problematiques = []
    
    try:
        paiements = Paiement.objects.all()
        print(f"   Total des paiements: {paiements.count()}")
        
        for paiement in paiements:
            try:
                # Vérification des champs décimaux
                montant = paiement.montant
                
                # Test de conversion
                float(montant)
                    
            except (ValueError, TypeError, InvalidOperation) as e:
                paiements_problematiques.append({
                    'id': paiement.id,
                    'contrat': paiement.contrat.numero_contrat if paiement.contrat else 'N/A',
                    'erreur': str(e),
                    'montant': paiement.montant
                })
                
    except Exception as e:
        print(f"   Erreur lors de la vérification des paiements: {e}")
    
    if paiements_problematiques:
        print(f"   ❌ {len(paiements_problematiques)} paiements avec des valeurs décimales invalides:")
        for p in paiements_problematiques:
            print(f"      - Paiement {p['id']} (Contrat: {p['contrat']}): {p['erreur']}")
            print(f"        Montant: {p['montant']}")
    else:
        print("   ✅ Tous les paiements ont des valeurs décimales valides")
    
    # Résumé
    print("\n=== RÉSUMÉ ===")
    total_problemes = len(contrats_problematiques) + len(proprietes_problematiques) + len(paiements_problematiques)
    
    if total_problemes > 0:
        print(f"❌ {total_problemes} enregistrements avec des valeurs décimales invalides détectés.")
        print("Ces valeurs doivent être corrigées pour résoudre l'erreur InvalidOperation.")
    else:
        print("✅ Aucun problème de valeurs décimales détecté.")
        print("L'erreur InvalidOperation pourrait venir d'ailleurs.")

def corriger_valeurs_invalides():
    """Tente de corriger les valeurs décimales invalides."""
    
    print("\n=== CORRECTION DES VALEURS INVALIDES ===\n")
    
    # Correction des contrats
    print("1. Correction des contrats...")
    contrats_corriges = 0
    
    try:
        contrats = Contrat.objects.all()
        
        for contrat in contrats:
            try:
                # Vérification et correction des champs décimaux
                if not isinstance(contrat.loyer_mensuel, Decimal):
                    try:
                        contrat.loyer_mensuel = Decimal(str(contrat.loyer_mensuel))
                        contrats_corriges += 1
                    except:
                        contrat.loyer_mensuel = Decimal('0.00')
                        contrats_corriges += 1
                
                if not isinstance(contrat.charges_mensuelles, Decimal):
                    try:
                        contrat.charges_mensuelles = Decimal(str(contrat.charges_mensuelles))
                        contrats_corriges += 1
                    except:
                        contrat.charges_mensuelles = Decimal('0.00')
                        contrats_corriges += 1
                
                if not isinstance(contrat.depot_garantie, Decimal):
                    try:
                        contrat.depot_garantie = Decimal(str(contrat.depot_garantie))
                        contrats_corriges += 1
                    except:
                        contrat.depot_garantie = Decimal('0.00')
                        contrats_corriges += 1
                
                if not isinstance(contrat.avance_loyer, Decimal):
                    try:
                        contrat.avance_loyer = Decimal(str(contrat.avance_loyer))
                        contrats_corriges += 1
                    except:
                        contrat.avance_loyer = Decimal('0.00')
                        contrats_corriges += 1
                
                contrat.save()
                
            except Exception as e:
                print(f"   Erreur lors de la correction du contrat {contrat.id}: {e}")
                
    except Exception as e:
        print(f"   Erreur lors de la correction des contrats: {e}")
    
    print(f"   {contrats_corriges} contrats corrigés")
    
    # Correction des propriétés
    print("\n2. Correction des propriétés...")
    proprietes_corrigees = 0
    
    try:
        proprietes = Propriete.objects.all()
        
        for propriete in proprietes:
            try:
                # Vérification et correction des champs décimaux
                if propriete.prix_vente and not isinstance(propriete.prix_vente, Decimal):
                    try:
                        propriete.prix_vente = Decimal(str(propriete.prix_vente))
                        proprietes_corrigees += 1
                    except:
                        propriete.prix_vente = Decimal('0.00')
                        proprietes_corrigees += 1
                
                if propriete.loyer_mensuel and not isinstance(propriete.loyer_mensuel, Decimal):
                    try:
                        propriete.loyer_mensuel = Decimal(str(propriete.loyer_mensuel))
                        proprietes_corrigees += 1
                    except:
                        propriete.loyer_mensuel = Decimal('0.00')
                        proprietes_corrigees += 1
                
                if propriete.charges_mensuelles and not isinstance(propriete.charges_mensuelles, Decimal):
                    try:
                        propriete.charges_mensuelles = Decimal(str(propriete.charges_mensuelles))
                        proprietes_corrigees += 1
                    except:
                        propriete.charges_mensuelles = Decimal('0.00')
                        proprietes_corrigees += 1
                
                propriete.save()
                
            except Exception as e:
                print(f"   Erreur lors de la correction de la propriété {propriete.id}: {e}")
                
    except Exception as e:
        print(f"   Erreur lors de la correction des propriétés: {e}")
    
    print(f"   {proprietes_corrigees} propriétés corrigées")
    
    # Correction des paiements
    print("\n3. Correction des paiements...")
    paiements_corriges = 0
    
    try:
        paiements = Paiement.objects.all()
        
        for paiement in paiements:
            try:
                # Vérification et correction des champs décimaux
                if not isinstance(paiement.montant, Decimal):
                    try:
                        paiement.montant = Decimal(str(paiement.montant))
                        paiements_corriges += 1
                    except:
                        paiement.montant = Decimal('0.00')
                        paiements_corriges += 1
                
                paiement.save()
                
            except Exception as e:
                print(f"   Erreur lors de la correction du paiement {paiement.id}: {e}")
                
    except Exception as e:
        print(f"   Erreur lors de la correction des paiements: {e}")
    
    print(f"   {paiements_corriges} paiements corrigés")
    
    total_corriges = contrats_corriges + proprietes_corrigees + paiements_corriges
    print(f"\n✅ Total: {total_corriges} enregistrements corrigés")

if __name__ == "__main__":
    print("Script de vérification et correction des champs décimaux")
    print("=" * 60)
    
    # Première étape: vérification
    verifier_champs_decimaux()
    
    # Deuxième étape: correction (optionnelle)
    reponse = input("\nVoulez-vous tenter de corriger automatiquement les valeurs invalides? (o/n): ")
    if reponse.lower() in ['o', 'oui', 'y', 'yes']:
        corriger_valeurs_invalides()
        print("\n✅ Correction terminée. Vérifiez maintenant si l'erreur persiste.")
    else:
        print("\n❌ Aucune correction effectuée. Corrigez manuellement les valeurs invalides.")
    
    print("\nFin du script.")
