#!/usr/bin/env python
"""
Script de test pour le module paiements partiels
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur, TypeBien
from paiements.models import PlanPaiementPartiel, PaiementPartiel
from decimal import Decimal
from datetime import date, timedelta

def test_paiements_partiels():
    """Test complet du module paiements partiels"""
    print("🧪 Test du module paiements partiels...")
    
    try:
        # 1. Vérifier que les modèles existent
        print("\n1. Vérification des modèles...")
        print(f"✅ PlanPaiementPartiel: {PlanPaiementPartiel}")
        print(f"✅ PaiementPartiel: {PaiementPartiel}")
        
        # 2. Créer des données de test si elles n'existent pas
        print("\n2. Création des données de test...")
        
        # Créer un type de bien
        type_bien, created = TypeBien.objects.get_or_create(
            nom='Appartement Test',
            defaults={'description': 'Type de bien pour test'}
        )
        if created:
            print("✅ Type de bien créé")
        
        # Créer un bailleur
        bailleur, created = Bailleur.objects.get_or_create(
            nom='Test Bailleur',
            defaults={
                'prenom': 'Test',
                'email': 'test@example.com',
                'telephone': '0123456789'
            }
        )
        if created:
            print("✅ Bailleur créé")
        
        # Utiliser des données existantes ou créer des données minimales
        try:
            propriete = Propriete.objects.first()
            if not propriete:
                print("❌ Aucune propriété trouvée. Veuillez créer des données de base d'abord.")
                return
            print(f"✅ Propriété utilisée: {propriete}")
            
            locataire = Locataire.objects.first()
            if not locataire:
                print("❌ Aucun locataire trouvé. Veuillez créer des données de base d'abord.")
                return
            print(f"✅ Locataire utilisé: {locataire}")
            
            contrat = Contrat.objects.first()
            if not contrat:
                print("❌ Aucun contrat trouvé. Veuillez créer des données de base d'abord.")
                return
            print(f"✅ Contrat utilisé: {contrat}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des données: {e}")
            return
        
        # 3. Créer un plan de paiement partiel
        print("\n3. Création d'un plan de paiement partiel...")
        plan, created = PlanPaiementPartiel.objects.get_or_create(
            contrat=contrat,
            nom_plan='Test Plan Paiement Partiel',
            defaults={
                'description': 'Plan de test pour paiements partiels',
                'montant_total': Decimal('1000.00'),
                'date_debut': date.today(),
                'date_fin_prevue': date.today() + timedelta(days=30),
                'statut': 'actif'
            }
        )
        if created:
            print("✅ Plan de paiement partiel créé")
        else:
            print("ℹ️  Plan de paiement partiel existe déjà")
        
        # 4. Créer un paiement partiel
        print("\n4. Création d'un paiement partiel...")
        paiement_partiel, created = PaiementPartiel.objects.get_or_create(
            plan=plan,
            montant=Decimal('250.00'),
            defaults={
                'date_paiement': date.today(),
                'mode_paiement': 'especes',
                'statut': 'valide'
            }
        )
        if created:
            print("✅ Paiement partiel créé")
        else:
            print("ℹ️  Paiement partiel existe déjà")
        
        # 5. Tester les relations
        print("\n5. Test des relations...")
        print(f"✅ Plan -> Contrat: {plan.contrat}")
        print(f"✅ Plan -> Paiements: {plan.paiements_partiels.count()}")
        print(f"✅ Paiement -> Plan: {paiement_partiel.plan}")
        
        # 6. Tester les méthodes du modèle
        print("\n6. Test des méthodes du modèle...")
        print(f"✅ Montant payé: {plan.montant_paye}")
        print(f"✅ Montant restant: {plan.montant_restant}")
        print(f"✅ Pourcentage payé: {plan.pourcentage_paye}%")
        print(f"✅ Est terminé: {plan.est_termine}")
        
        print("\n🎉 Tous les tests du module paiements partiels ont réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_paiements_partiels()
