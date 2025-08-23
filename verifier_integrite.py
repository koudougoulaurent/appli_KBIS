#!/usr/bin/env python
"""
Script pour vérifier et corriger les problèmes d'intégrité de la base de données
avant d'appliquer la migration du modèle Photo.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection
from proprietes.models import Propriete, Bailleur, Locataire
from contrats.models import Contrat
from paiements.models import Paiement, Recu, ChargeDeductible
from contrats.models import Quittance
from utilisateurs.models import Utilisateur

def verifier_integrite():
    """Vérifie l'intégrité de la base de données"""
    print("🔍 Vérification de l'intégrité de la base de données...")
    
    # Vérifier les propriétés orphelines
    proprietes_orphelines = Propriete.objects.filter(bailleur__isnull=True)
    if proprietes_orphelines.exists():
        print(f"⚠️  {proprietes_orphelines.count()} propriété(s) sans bailleur")
        for prop in proprietes_orphelines:
            print(f"   - ID {prop.id}: {prop.adresse}")
    
    # Vérifier les propriétés avec des bailleurs invalides
    proprietes_invalides = []
    for prop in Propriete.objects.all():
        try:
            if prop.bailleur and not Bailleur.objects.filter(id=prop.bailleur.id).exists():
                proprietes_invalides.append(prop)
        except:
            proprietes_invalides.append(prop)
    
    if proprietes_invalides:
        print(f"⚠️  {len(proprietes_invalides)} propriété(s) avec des bailleurs invalides")
        for prop in proprietes_invalides:
            print(f"   - ID {prop.id}: {prop.adresse} (bailleur_id: {prop.bailleur_id if hasattr(prop, 'bailleur_id') else 'N/A'})")
    
    # Vérifier les contrats orphelins
    contrats_orphelins = Contrat.objects.filter(propriete__isnull=True)
    if contrats_orphelins.exists():
        print(f"⚠️  {contrats_orphelins.count()} contrat(s) sans propriété")
    
    # Vérifier les paiements orphelins
    paiements_orphelins = Paiement.objects.filter(contrat__isnull=True)
    if paiements_orphelins.exists():
        print(f"⚠️  {paiements_orphelins.count()} paiement(s) sans contrat")
    
    return len(proprietes_orphelines) + len(proprietes_invalides) + contrats_orphelins.count() + paiements_orphelins.count()

def corriger_integrite():
    """Corrige les problèmes d'intégrité"""
    print("\n🔧 Correction des problèmes d'intégrité...")
    
    # Supprimer les propriétés orphelines
    proprietes_orphelines = Propriete.objects.filter(bailleur__isnull=True)
    if proprietes_orphelines.exists():
        print(f"🗑️  Suppression de {proprietes_orphelines.count()} propriété(s) orpheline(s)")
        proprietes_orphelines.delete()
    
    # Supprimer les propriétés avec des bailleurs invalides
    proprietes_invalides = []
    for prop in Propriete.objects.all():
        try:
            if prop.bailleur and not Bailleur.objects.filter(id=prop.bailleur.id).exists():
                proprietes_invalides.append(prop)
        except:
            proprietes_invalides.append(prop)
    
    if proprietes_invalides:
        print(f"🗑️  Suppression de {len(proprietes_invalides)} propriété(s) avec des bailleurs invalides")
        for prop in proprietes_invalides:
            try:
                # Supprimer d'abord les objets dépendants
                Contrat.objects.filter(propriete=prop).delete()
                Paiement.objects.filter(contrat__propriete=prop).delete()
                Recu.objects.filter(contrat__propriete=prop).delete()
                Quittance.objects.filter(contrat__propriete=prop).delete()
                ChargeDeductible.objects.filter(contrat__propriete=prop).delete()
                
                # Puis supprimer la propriété
                prop.delete()
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la suppression de la propriété {prop.id}: {e}")
    
    # Supprimer les contrats orphelins
    contrats_orphelins = Contrat.objects.filter(propriete__isnull=True)
    if contrats_orphelins.exists():
        print(f"🗑️  Suppression de {contrats_orphelins.count()} contrat(s) orphelin(s)")
        contrats_orphelins.delete()
    
    # Supprimer les paiements orphelins
    paiements_orphelins = Paiement.objects.filter(contrat__isnull=True)
    if paiements_orphelins.exists():
        print(f"🗑️  Suppression de {paiements_orphelins.count()} paiement(s) orphelin(s)")
        paiements_orphelins.delete()
    
    print("✅ Correction terminée")

def nettoyer_donnees_test():
    """Nettoie les données de test restantes"""
    print("\n🧹 Nettoyage des données de test...")
    
    # Supprimer les propriétés de test
    proprietes_test = Propriete.objects.filter(
        adresse__icontains='test'
    )
    if proprietes_test.exists():
        print(f"🗑️  Suppression de {proprietes_test.count()} propriété(s) de test")
        proprietes_test.delete()
    
    # Supprimer les bailleurs de test
    bailleurs_test = Bailleur.objects.filter(
        nom__icontains='test'
    )
    if bailleurs_test.exists():
        print(f"🗑️  Suppression de {bailleurs_test.count()} bailleur(s) de test")
        bailleurs_test.delete()
    
    # Supprimer les utilisateurs de test
    utilisateurs_test = Utilisateur.objects.filter(
        username__icontains='test'
    )
    if utilisateurs_test.exists():
        print(f"🗑️  Suppression de {utilisateurs_test.count()} utilisateur(s) de test")
        utilisateurs_test.delete()
    
    print("✅ Nettoyage terminé")

def afficher_statistiques():
    """Affiche les statistiques de la base de données"""
    print("\n📊 Statistiques de la base de données:")
    print(f"   - Propriétés: {Propriete.objects.count()}")
    print(f"   - Bailleurs: {Bailleur.objects.count()}")
    print(f"   - Locataires: {Locataire.objects.count()}")
    print(f"   - Contrats: {Contrat.objects.count()}")
    print(f"   - Paiements: {Paiement.objects.count()}")
    print(f"   - Utilisateurs: {Utilisateur.objects.count()}")

def main():
    """Fonction principale"""
    print("🚀 Script de vérification et correction de l'intégrité de la base de données")
    print("=" * 70)
    
    try:
        # Vérifier l'intégrité
        problemes = verifier_integrite()
        
        if problemes > 0:
            print(f"\n⚠️  {problemes} problème(s) d'intégrité détecté(s)")
            
            # Demander confirmation pour la correction
            reponse = input("\nVoulez-vous corriger ces problèmes ? (o/n): ").lower().strip()
            
            if reponse in ['o', 'oui', 'y', 'yes']:
                corriger_integrite()
                nettoyer_donnees_test()
                
                # Vérifier à nouveau
                print("\n🔍 Vérification après correction...")
                problemes_apres = verifier_integrite()
                
                if problemes_apres == 0:
                    print("✅ Tous les problèmes d'intégrité ont été résolus !")
                else:
                    print(f"⚠️  {problemes_apres} problème(s) persistent")
            else:
                print("❌ Correction annulée")
        else:
            print("✅ Aucun problème d'intégrité détecté")
            nettoyer_donnees_test()
        
        # Afficher les statistiques finales
        afficher_statistiques()
        
        print("\n🎯 La base de données est maintenant prête pour la migration du modèle Photo !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
