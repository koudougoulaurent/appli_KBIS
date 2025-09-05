#!/usr/bin/env python
"""
Script de test pour le système de récapitulatif mensuel complet
Teste toutes les fonctionnalités du système automatisé
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.models import Group
from django.db import transaction
from paiements.models import RecapMensuel, Paiement, ChargeDeductible
from proprietes.models import Bailleur, Propriete
from contrats.models import Contrat
from utilisateurs.models import Utilisateur

def test_creation_donnees_test():
    """Crée des données de test pour tester le système."""
    print("🔧 Création des données de test...")
    
    try:
        with transaction.atomic():
            # Créer un utilisateur de test
            user, created = Utilisateur.objects.get_or_create(
                username='test_recap',
                defaults={
                    'email': 'test@recap.com',
                    'first_name': 'Test',
                    'last_name': 'Récapitulatif'
                }
            )
            
            # Créer un groupe PRIVILEGE s'il n'existe pas
            groupe_privilege, created = Group.objects.get_or_create(name='PRIVILEGE')
            user.groups.add(groupe_privilege)
            
            # Créer des bailleurs de test
            bailleur1, created = Bailleur.objects.get_or_create(
                nom='Dupont',
                prenom='Jean',
                defaults={
                    'telephone': '0123456789',
                    'email': 'jean.dupont@email.com'
                }
            )
            
            bailleur2, created = Bailleur.objects.get_or_create(
                nom='Martin',
                prenom='Marie',
                defaults={
                    'telephone': '0987654321',
                    'email': 'marie.martin@email.com'
                }
            )
            
            # Créer des locataires de test
            locataire1, created = Utilisateur.objects.get_or_create(
                username='pierre.durand',
                defaults={
                    'first_name': 'Pierre',
                    'last_name': 'Durand',
                    'email': 'pierre.durand@email.com',
                    'telephone': '0555666777'
                }
            )
            
            locataire2, created = Utilisateur.objects.get_or_create(
                username='sophie.leroy',
                defaults={
                    'first_name': 'Sophie',
                    'last_name': 'Leroy',
                    'email': 'sophie.leroy@email.com',
                    'telephone': '0444333222'
                }
            )
            
            # Créer des propriétés de test
            propriete1, created = Propriete.objects.get_or_create(
                adresse='123 Rue de la Paix',
                defaults={
                    'bailleur': bailleur1,
                    'type_bien_id': 1,  # Assurez-vous que ce type existe
                    'prix_location': 50000,
                    'charges': 5000
                }
            )
            
            propriete2, created = Propriete.objects.get_or_create(
                adresse='456 Avenue des Champs',
                defaults={
                    'bailleur': bailleur2,
                    'type_bien_id': 1,  # Assurez-vous que ce type existe
                    'prix_location': 75000,
                    'charges': 7500
                }
            )
            
            # Créer des contrats de test
            contrat1, created = Contrat.objects.get_or_create(
                propriete=propriete1,
                locataire=locataire1,
                defaults={
                    'date_debut': datetime.now().date() - timedelta(days=90),
                    'date_fin': datetime.now().date() + timedelta(days=275),
                    'loyer_mensuel': 50000,
                    'charges_mensuelles': 5000,
                    'est_actif': True,
                    'est_resilie': False
                }
            )
            
            contrat2, created = Contrat.objects.get_or_create(
                propriete=propriete2,
                locataire=locataire2,
                defaults={
                    'date_debut': datetime.now().date() - timedelta(days=60),
                    'date_fin': datetime.now().date() + timedelta(days=305),
                    'loyer_mensuel': 75000,
                    'charges_mensuelles': 7500,
                    'est_actif': True,
                    'est_resilie': False
                }
            )
            
            # Créer des paiements de test pour le mois en cours
            mois_courant = datetime.now().replace(day=1)
            
            paiement1, created = Paiement.objects.get_or_create(
                contrat=contrat1,
                date_paiement=mois_courant + timedelta(days=5),
                defaults={
                    'montant': 50000,
                    'type_paiement': 'loyer',
                    'methode_paiement': 'especes',
                    'statut': 'valide'
                }
            )
            
            paiement2, created = Paiement.objects.get_or_create(
                contrat=contrat2,
                date_paiement=mois_courant + timedelta(days=10),
                defaults={
                    'montant': 75000,
                    'type_paiement': 'loyer',
                    'methode_paiement': 'virement',
                    'statut': 'valide'
                }
            )
            
            # Créer des charges déductibles de test
            charge1, created = ChargeDeductible.objects.get_or_create(
                contrat=contrat1,
                date_charge=mois_courant + timedelta(days=15),
                defaults={
                    'montant': 3000,
                    'description': 'Réparation électricité',
                    'statut': 'validee'
                }
            )
            
            charge2, created = ChargeDeductible.objects.get_or_create(
                contrat=contrat2,
                date_charge=mois_courant + timedelta(days=20),
                defaults={
                    'montant': 4500,
                    'description': 'Entretien jardin',
                    'statut': 'validee'
                }
            )
            
            print("✅ Données de test créées avec succès")
            print(f"   - Bailleurs: {Bailleur.objects.count()}")
            print(f"   - Propriétés: {Propriete.objects.count()}")
            print(f"   - Contrats: {Contrat.objects.count()}")
            print(f"   - Paiements: {Paiement.objects.count()}")
            print(f"   - Charges: {ChargeDeductible.objects.count()}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création des données de test: {e}")
        return False

def test_generation_recap_automatique():
    """Teste la génération automatique des récapitulatifs."""
    print("\n🔍 Test de la génération automatique des récapitulatifs...")
    
    try:
        # Récupérer le mois en cours
        mois_courant = datetime.now().replace(day=1)
        
        # Vérifier s'il existe déjà des récapitulatifs pour ce mois
        recaps_existants = RecapMensuel.objects.filter(
            mois_recap__year=mois_courant.year,
            mois_recap__month=mois_courant.month
        )
        
        if recaps_existants.exists():
            print(f"⚠️  Des récapitulatifs existent déjà pour {mois_courant.strftime('%B %Y')}")
            print("   Suppression des anciens récapitulatifs...")
            recaps_existants.delete()
        
        # Récupérer tous les bailleurs actifs
        bailleurs = Bailleur.objects.filter(is_deleted=False)
        print(f"📊 Traitement de {bailleurs.count()} bailleurs...")
        
        recaps_crees = []
        
        for bailleur in bailleurs:
            try:
                # Vérifier si le bailleur a des propriétés louées
                proprietes_louees = bailleur.proprietes.filter(
                    contrats__est_actif=True,
                    contrats__est_resilie=False
                ).distinct()
                
                if not proprietes_louees.exists():
                    print(f"   ⚠️  {bailleur.get_nom_complet()}: Aucune propriété louée")
                    continue
                
                print(f"   ✅ {bailleur.get_nom_complet()}: {proprietes_louees.count()} propriété(s)")
                
                # Créer le récapitulatif
                recap = RecapMensuel.objects.create(
                    bailleur=bailleur,
                    mois_recap=mois_courant,
                    cree_par=Utilisateur.objects.get(username='test_recap')
                )
                
                # Calculer et associer les paiements
                for propriete in proprietes_louees:
                    contrat_actif = propriete.contrats.filter(est_actif=True).first()
                    if contrat_actif:
                        # Paiements du mois
                        paiements_mois = Paiement.objects.filter(
                            contrat=contrat_actif,
                            date_paiement__year=mois_courant.year,
                            date_paiement__month=mois_courant.month,
                            statut='valide'
                        )
                        recap.paiements_concernes.add(*paiements_mois)
                        
                        # Charges déductibles du mois
                        charges_mois = ChargeDeductible.objects.filter(
                            contrat=contrat_actif,
                            date_charge__year=mois_courant.year,
                            date_charge__month=mois_courant.month,
                            statut='validee'
                        )
                        recap.charges_deductibles.add(*charges_mois)
                
                # Calculer les totaux
                recap.calculer_totaux()
                recaps_crees.append(recap)
                
                print(f"      💰 Récapitulatif créé: {recap.total_net_a_payer} F CFA")
                
            except Exception as e:
                print(f"   ❌ Erreur pour {bailleur.get_nom_complet()}: {str(e)}")
        
        print(f"\n✅ {len(recaps_crees)} récapitulatifs créés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {str(e)}")
        return False

def test_verification_recaps():
    """Vérifie que les récapitulatifs ont été créés correctement."""
    print("\n🔍 Vérification des récapitulatifs créés...")
    
    try:
        mois_courant = datetime.now().replace(day=1)
        recaps = RecapMensuel.objects.filter(
            mois_recap__year=mois_courant.year,
            mois_recap__month=mois_courant.month
        )
        
        if not recaps.exists():
            print("❌ Aucun récapitulatif trouvé pour le mois en cours")
            return False
        
        print(f"📊 {recaps.count()} récapitulatifs trouvés pour {mois_courant.strftime('%B %Y')}")
        
        total_loyers = 0
        total_charges = 0
        total_net = 0
        
        for recap in recaps:
            print(f"\n📋 {recap.bailleur.get_nom_complet()}:")
            print(f"   - Loyers bruts: {recap.total_loyers_bruts} F CFA")
            print(f"   - Charges déductibles: {recap.total_charges_deductibles} F CFA")
            print(f"   - Net à payer: {recap.total_net_a_payer} F CFA")
            print(f"   - Propriétés: {recap.nombre_proprietes}")
            print(f"   - Contrats actifs: {recap.nombre_contrats_actifs}")
            print(f"   - Paiements reçus: {recap.nombre_paiements_recus}")
            
            total_loyers += recap.total_loyers_bruts
            total_charges += recap.total_charges_deductibles
            total_net += recap.total_net_a_payer
        
        print(f"\n💰 TOTAUX GLOBAUX:")
        print(f"   - Total loyers: {total_loyers} F CFA")
        print(f"   - Total charges: {total_charges} F CFA")
        print(f"   - Total net: {total_net} F CFA")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {str(e)}")
        return False

def nettoyer_donnees_test():
    """Nettoie les données de test créées."""
    print("\n🧹 Nettoyage des données de test...")
    
    try:
        with transaction.atomic():
            # Supprimer les récapitulatifs de test
            mois_courant = datetime.now().replace(day=1)
            recaps_test = RecapMensuel.objects.filter(
                mois_recap__year=mois_courant.year,
                mois_recap__month=mois_courant.month
            )
            recaps_test.delete()
            
            # Supprimer les paiements de test
            Paiement.objects.filter(
                date_paiement__year=mois_courant.year,
                date_paiement__month=mois_courant.month
            ).delete()
            
            # Supprimer les charges de test
            ChargeDeductible.objects.filter(
                date_charge__year=mois_courant.year,
                date_charge__month=mois_courant.month
            ).delete()
            
            # Supprimer les contrats de test
            Contrat.objects.filter(
                propriete__adresse__in=['123 Rue de la Paix', '456 Avenue des Champs']
            ).delete()
            
            # Supprimer les propriétés de test
            Propriete.objects.filter(
                adresse__in=['123 Rue de la Paix', '456 Avenue des Champs']
            ).delete()
            
            # Supprimer les locataires de test
            Utilisateur.objects.filter(
                username__in=['pierre.durand', 'sophie.leroy']
            ).delete()
            
            # Supprimer les bailleurs de test
            Bailleur.objects.filter(
                nom__in=['Dupont', 'Martin']
            ).delete()
            
            # Supprimer l'utilisateur de test
            Utilisateur.objects.filter(username='test_recap').delete()
            
            print("✅ Données de test nettoyées avec succès")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {str(e)}")
        return False

def main():
    """Fonction principale de test."""
    print("🚀 TEST DU SYSTÈME DE RÉCAPITULATIF MENSUEL COMPLET")
    print("=" * 60)
    
    try:
        # Test 1: Création des données de test
        if not test_creation_donnees_test():
            print("❌ Échec de la création des données de test")
            return
        
        # Test 2: Génération automatique des récapitulatifs
        if not test_generation_recap_automatique():
            print("❌ Échec de la génération automatique")
            return
        
        # Test 3: Vérification des récapitulatifs
        if not test_verification_recaps():
            print("❌ Échec de la vérification")
            return
        
        print("\n🎉 TOUS LES TESTS ONT RÉUSSI !")
        print("✅ Le système de récapitulatif mensuel fonctionne correctement")
        
        # Demander si l'utilisateur veut nettoyer les données de test
        reponse = input("\n🧹 Voulez-vous nettoyer les données de test ? (o/n): ")
        if reponse.lower() in ['o', 'oui', 'y', 'yes']:
            nettoyer_donnees_test()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {str(e)}")
    finally:
        print("\n🏁 Fin des tests")

if __name__ == '__main__':
    main()
