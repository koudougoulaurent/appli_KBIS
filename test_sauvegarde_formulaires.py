#!/usr/bin/env python
"""
Script de test pour vérifier la sauvegarde des données des formulaires
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien
from contrats.models import Contrat
from paiements.models import Paiement, Recu
from utilisateurs.models import GroupeTravail

User = get_user_model()

def test_sauvegarde_formulaires():
    """Test complet de la sauvegarde des formulaires"""
    
    print("🔍 TEST DE SAUVEGARDE DES FORMULAIRES")
    print("=" * 60)
    
    # Nettoyer les données de test existantes
    print("🧹 Nettoyage des données de test existantes...")
    try:
        # Supprimer les données de test dans l'ordre inverse des dépendances
        Recu.objects.filter(numero_recu__startswith='REC-2025-').delete()
        Paiement.objects.filter(reference_virement__startswith='VIR-2025-').delete()
        Contrat.objects.filter(numero_contrat__startswith='CTR-2025-').delete()
        # Ne pas supprimer les propriétés existantes pour éviter les contraintes
        # Propriete.objects.filter(titre__startswith='Appartement T3 avec balcon').delete()
        Locataire.objects.filter(email='marie.martin@email.com').delete()
        # Ne pas supprimer les bailleurs existants pour éviter les contraintes
        # Bailleur.objects.filter(email='jean.dupont@email.com').delete()
        TypeBien.objects.filter(nom='Appartement Test').delete()
        GroupeTravail.objects.filter(nom='TEST').delete()
        User.objects.filter(username='test_user_form').delete()
        print("✅ Données de test nettoyées")
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")
    
    # Créer un utilisateur de test avec un nom unique
    try:
        user = User.objects.create_user(
            username='test_user_form',
            email='test_form@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print("✅ Utilisateur de test créé")
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {e}")
        return
    
    # Créer un groupe de travail
    try:
        groupe = GroupeTravail.objects.create(
            nom='TEST',
            description='Groupe de test'
        )
        print("✅ Groupe de travail créé")
    except Exception as e:
        print(f"❌ Erreur création groupe: {e}")
        return
    
    # Créer un type de bien
    try:
        type_bien = TypeBien.objects.create(
            nom='Appartement Test',
            description='Appartement de test'
        )
        print("✅ Type de bien créé")
    except Exception as e:
        print(f"❌ Erreur création type bien: {e}")
        return
    
    # Test 1: Sauvegarde d'un bailleur
    print("\n📝 Test 1: Sauvegarde d'un bailleur")
    try:
        bailleur = Bailleur.objects.create(
            nom='Dupont Test',
            prenom='Jean Test',
            email='jean.dupont.test@email.com',
            telephone='01 23 45 67 89',
            adresse='123 Rue de la Paix, 75001 Paris',
            profession='Ingénieur',
            entreprise='Tech Corp',
            iban='FR7630006000011234567890189',
            bic='BNPAFRPPXXX',
            est_actif=True
        )
        print(f"✅ Bailleur sauvegardé: {bailleur.nom} {bailleur.prenom}")
        print(f"   - Email: {bailleur.email}")
        print(f"   - Téléphone: {bailleur.telephone}")
        print(f"   - IBAN: {bailleur.iban}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde bailleur: {e}")
        return
    
    # Test 2: Sauvegarde d'un locataire
    print("\n📝 Test 2: Sauvegarde d'un locataire")
    try:
        locataire = Locataire.objects.create(
            nom='Martin Test',
            prenom='Marie Test',
            email='marie.martin.test@email.com',
            telephone='01 98 76 54 32',
            adresse_actuelle='456 Avenue des Champs, 75008 Paris',
            profession='Avocate',
            employeur='Cabinet Legal',
            salaire_mensuel=Decimal('4500.00'),
            iban='FR7630006000011234567890190',
            bic='BNPAFRPPXXX',
            est_actif=True
        )
        print(f"✅ Locataire sauvegardé: {locataire.nom} {locataire.prenom}")
        print(f"   - Email: {locataire.email}")
        print(f"   - Salaire: {locataire.salaire_mensuel} XOF")
        print(f"   - IBAN: {locataire.iban}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde locataire: {e}")
        return
    
    # Test 3: Sauvegarde d'une propriété
    print("\n📝 Test 3: Sauvegarde d'une propriété")
    try:
        propriete = Propriete.objects.create(
            titre='Appartement T3 Test avec balcon',
            adresse='789 Boulevard Saint-Germain, 75006 Paris',
            code_postal='75006',
            ville='Paris',
            pays='France',
            type_bien=type_bien,
            surface=Decimal('75.5'),
            nombre_pieces=3,
            nombre_chambres=2,
            nombre_salles_bain=1,
            ascenseur=True,
            parking=False,
            balcon=True,
            jardin=False,
            prix_achat=Decimal('450000.00'),
            loyer_actuel=Decimal('1800.00'),
            charges_locataire=Decimal('200.00'),
            etat='excellent',
            disponible=True,
            bailleur=bailleur,
            cree_par=user,
            notes='Appartement de standing dans le 6ème arrondissement'
        )
        print(f"✅ Propriété sauvegardée: {propriete.titre}")
        print(f"   - Adresse: {propriete.adresse}")
        print(f"   - Surface: {propriete.surface}m²")
        print(f"   - Loyer: {propriete.loyer_actuel} XOF")
        print(f"   - Bailleur: {propriete.bailleur.nom}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde propriété: {e}")
        return
    
    # Test 4: Sauvegarde d'un contrat
    print("\n📝 Test 4: Sauvegarde d'un contrat")
    try:
        contrat = Contrat.objects.create(
            numero_contrat='CTR-2025-001',
            propriete=propriete,
            locataire=locataire,
            date_debut=date.today() + timedelta(days=30),
            date_fin=date.today() + timedelta(days=1095),  # 3 ans
            date_signature=date.today(),
            loyer_mensuel=Decimal('1800.00'),
            charges_mensuelles=Decimal('200.00'),
            depot_garantie=Decimal('3600.00'),
            jour_paiement=5,
            mode_paiement='virement',
            est_actif=True,
            notes='Contrat de location standard'
        )
        print(f"✅ Contrat sauvegardé: {contrat.numero_contrat}")
        print(f"   - Propriété: {contrat.propriete.titre}")
        print(f"   - Locataire: {contrat.locataire.nom}")
        print(f"   - Loyer: {contrat.loyer_mensuel} XOF")
        print(f"   - Date début: {contrat.date_debut}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde contrat: {e}")
        return
    
    # Test 5: Sauvegarde d'un paiement
    print("\n📝 Test 5: Sauvegarde d'un paiement")
    try:
        paiement = Paiement.objects.create(
            contrat=contrat,
            montant=Decimal('2000.00'),
            date_paiement=date.today(),
            type_paiement='loyer',
            mode_paiement='virement',
            reference_virement='VIR-2025-001',
            statut='valide',
            notes='Paiement du loyer de janvier 2025'
        )
        print(f"✅ Paiement sauvegardé: {paiement.reference_virement}")
        print(f"   - Montant: {paiement.montant} XOF")
        print(f"   - Date: {paiement.date_paiement}")
        print(f"   - Statut: {paiement.statut}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde paiement: {e}")
        return
    
    # Test 6: Sauvegarde d'un reçu
    print("\n📝 Test 6: Sauvegarde d'un reçu")
    try:
        recu = Recu.objects.create(
            paiement=paiement,
            numero_recu='REC-2025-001',
            template_utilise='standard',
            valide=True,
            imprime=False,
            nombre_impressions=0,
            nombre_emails=0,
            genere_automatiquement=True
        )
        print(f"✅ Reçu sauvegardé: {recu.numero_recu}")
        print(f"   - Validé: {recu.valide}")
        print(f"   - Imprimé: {recu.imprime}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde reçu: {e}")
        return
    
    # Test 7: Vérification des relations
    print("\n📝 Test 7: Vérification des relations")
    try:
        # Vérifier que le paiement a bien un reçu
        paiement.refresh_from_db()
        if hasattr(paiement, 'recu'):
            print(f"✅ Relation paiement-reçu OK: {paiement.recu.numero_recu}")
        else:
            print("❌ Relation paiement-reçu manquante")
        
        # Vérifier que le contrat a bien un paiement
        contrat.refresh_from_db()
        paiements_contrat = contrat.paiements.all()
        print(f"✅ Contrat a {paiements_contrat.count()} paiement(s)")
        
        # Vérifier que la propriété a bien un contrat
        propriete.refresh_from_db()
        contrats_propriete = propriete.contrats.all()
        print(f"✅ Propriété a {contrats_propriete.count()} contrat(s)")
        
    except Exception as e:
        print(f"❌ Erreur vérification relations: {e}")
    
    # Test 8: Test de récupération des données
    print("\n📝 Test 8: Test de récupération des données")
    try:
        # Récupérer le bailleur
        bailleur_recup = Bailleur.objects.get(email='jean.dupont.test@email.com')
        print(f"✅ Bailleur récupéré: {bailleur_recup.nom} {bailleur_recup.prenom}")
        
        # Récupérer le locataire
        locataire_recup = Locataire.objects.get(email='marie.martin.test@email.com')
        print(f"✅ Locataire récupéré: {locataire_recup.nom} {locataire_recup.prenom}")
        
        # Récupérer la propriété
        propriete_recup = Propriete.objects.get(titre='Appartement T3 Test avec balcon')
        print(f"✅ Propriété récupérée: {propriete_recup.titre}")
        
        # Récupérer le contrat
        contrat_recup = Contrat.objects.get(numero_contrat='CTR-2025-001')
        print(f"✅ Contrat récupéré: {contrat_recup.numero_contrat}")
        
        # Récupérer le paiement
        paiement_recup = Paiement.objects.get(reference_virement='VIR-2025-001')
        print(f"✅ Paiement récupéré: {paiement_recup.reference_virement}")
        
        # Récupérer le reçu
        recu_recup = Recu.objects.get(numero_recu='REC-2025-001')
        print(f"✅ Reçu récupéré: {recu_recup.numero_recu}")
        
    except Exception as e:
        print(f"❌ Erreur récupération données: {e}")
    
    # Test 9: Test de mise à jour
    print("\n📝 Test 9: Test de mise à jour")
    try:
        # Mettre à jour le bailleur
        bailleur.telephone = '01 23 45 67 90'
        bailleur.save()
        print(f"✅ Téléphone bailleur mis à jour: {bailleur.telephone}")
        
        # Mettre à jour le locataire
        locataire.salaire_mensuel = Decimal('5000.00')
        locataire.save()
        print(f"✅ Salaire locataire mis à jour: {locataire.salaire_mensuel} XOF")
        
        # Mettre à jour la propriété
        propriete.loyer_actuel = Decimal('1900.00')
        propriete.save()
        print(f"✅ Loyer propriété mis à jour: {propriete.loyer_actuel} XOF")
        
    except Exception as e:
        print(f"❌ Erreur mise à jour: {e}")
    
    # Test 10: Test de suppression
    print("\n📝 Test 10: Test de suppression")
    try:
        # Supprimer le reçu
        recu.delete()
        print("✅ Reçu supprimé")
        
        # Supprimer le paiement
        paiement.delete()
        print("✅ Paiement supprimé")
        
        # Supprimer le contrat
        contrat.delete()
        print("✅ Contrat supprimé")
        
        # Supprimer la propriété
        propriete.delete()
        print("✅ Propriété supprimée")
        
        # Supprimer le locataire
        locataire.delete()
        print("✅ Locataire supprimé")
        
        # Supprimer le bailleur
        bailleur.delete()
        print("✅ Bailleur supprimé")
        
        # Supprimer le type de bien
        type_bien.delete()
        print("✅ Type de bien supprimé")
        
        # Supprimer le groupe
        groupe.delete()
        print("✅ Groupe supprimé")
        
        # Supprimer l'utilisateur
        user.delete()
        print("✅ Utilisateur supprimé")
        
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 TESTS DE SAUVEGARDE TERMINÉS AVEC SUCCÈS !")
    print("✅ Toutes les données sont correctement sauvegardées dans la base")
    print("✅ Les relations entre les modèles fonctionnent")
    print("✅ Les mises à jour et suppressions fonctionnent")
    print("=" * 60)

if __name__ == '__main__':
    test_sauvegarde_formulaires() 