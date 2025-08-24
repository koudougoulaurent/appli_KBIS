#!/usr/bin/env python
"""
Script de test pour vérifier la génération automatique des reçus
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement, Recu
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

Utilisateur = get_user_model()

def test_generation_automatique_recus():
    """Teste la génération automatique des reçus"""
    
    print("🧪 TEST DE LA GÉNÉRATION AUTOMATIQUE DES REÇUS")
    print("=" * 60)
    
    # 1. Vérifier l'état initial
    print("\n1. 📊 ÉTAT INITIAL")
    nb_paiements = Paiement.objects.count()
    nb_recus = Recu.objects.count()
    print(f"   • Paiements totaux: {nb_paiements}")
    print(f"   • Reçus existants: {nb_recus}")
    
    # 2. Créer un utilisateur de test
    print("\n2. 👤 Création d'un utilisateur de test...")
    try:
        utilisateur = Utilisateur.objects.get(username='test_user')
        print(f"   ✅ Utilisateur existant: {utilisateur.username}")
    except Utilisateur.DoesNotExist:
        utilisateur = Utilisateur.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"   ✅ Utilisateur créé: {utilisateur.username}")
    
    # 3. Créer des données de test si nécessaire
    print("\n3. 🏠 Création des données de test...")
    
    # Créer un bailleur
    try:
        bailleur = Bailleur.objects.get(nom='Test Bailleur')
        print(f"   ✅ Bailleur existant: {bailleur.nom}")
    except Bailleur.DoesNotExist:
        bailleur = Bailleur.objects.create(
            nom='Test Bailleur',
            prenom='Jean',
            email='bailleur@test.com',
            telephone='0123456789'
        )
        print(f"   ✅ Bailleur créé: {bailleur.nom}")
    
    # Créer un locataire
    try:
        locataire = Locataire.objects.get(nom='Test Locataire')
        print(f"   ✅ Locataire existant: {locataire.nom}")
    except Locataire.DoesNotExist:
        locataire = Locataire.objects.create(
            nom='Test Locataire',
            prenom='Marie',
            email='locataire@test.com',
            telephone='0987654321'
        )
        print(f"   ✅ Locataire créé: {locataire.nom}")
    
    # Créer une propriété
    try:
        propriete = Propriete.objects.get(titre='Test Propriété')
        print(f"   ✅ Propriété existante: {propriete.titre}")
    except Propriete.DoesNotExist:
        propriete = Propriete.objects.create(
            titre='Test Propriété',
            adresse='123 Rue Test',
            ville='Test Ville',
            code_postal='12345',
            loyer_mensuel=1000.00,
            charges_mensuelles=100.00,
            bailleur=bailleur
        )
        print(f"   ✅ Propriété créée: {propriete.titre}")
    
    # Créer un contrat
    try:
        contrat = Contrat.objects.get(numero_contrat='TEST-001')
        print(f"   ✅ Contrat existant: {contrat.numero_contrat}")
    except Contrat.DoesNotExist:
        contrat = Contrat.objects.create(
            numero_contrat='TEST-001',
            propriete=propriete,
            locataire=locataire,
            bailleur=bailleur,
            date_debut=timezone.now().date(),
            date_fin=timezone.now().date() + timedelta(days=365),
            loyer_mensuel=1000.00,
            charges_mensuelles=100.00,
            depot_garantie=1000.00,
            statut='actif'
        )
        print(f"   ✅ Contrat créé: {contrat.numero_contrat}")
    
    # 4. Test de création d'un paiement avec statut "valide"
    print("\n4. 💰 Test de création d'un paiement avec statut 'valide'...")
    
    # Supprimer les anciens paiements de test
    Paiement.objects.filter(contrat=contrat, notes__icontains='Test automatique').delete()
    
    # Créer un nouveau paiement avec statut "valide"
    paiement_valide = Paiement.objects.create(
        contrat=contrat,
        montant=1100.00,
        type_paiement='loyer',
        mode_paiement='virement',
        date_paiement=timezone.now().date(),
        statut='valide',
        cree_par=utilisateur,
        valide_par=utilisateur,
        notes='Test automatique - Paiement validé'
    )
    print(f"   ✅ Paiement créé avec statut 'valide': {paiement_valide.id}")
    
    # Attendre un peu pour que les signaux se déclenchent
    import time
    time.sleep(1)
    
    # Vérifier si un reçu a été créé automatiquement
    try:
        recu_auto = paiement_valide.recu
        print(f"   ✅ Reçu créé automatiquement: {recu_auto.numero_recu}")
        print(f"      - Généré automatiquement: {recu_auto.genere_automatiquement}")
        print(f"      - Valide: {recu_auto.valide}")
        print(f"      - Template: {recu_auto.template_utilise}")
    except Recu.DoesNotExist:
        print("   ❌ Reçu non créé automatiquement")
        return False
    
    # 5. Test de création d'un paiement avec statut "en_attente"
    print("\n5. ⏳ Test de création d'un paiement avec statut 'en_attente'...")
    
    paiement_attente = Paiement.objects.create(
        contrat=contrat,
        montant=500.00,
        type_paiement='charges',
        mode_paiement='cheque',
        date_paiement=timezone.now().date(),
        statut='en_attente',
        cree_par=utilisateur,
        notes='Test automatique - Paiement en attente'
    )
    print(f"   ✅ Paiement créé avec statut 'en_attente': {paiement_attente.id}")
    
    # Vérifier qu'aucun reçu n'a été créé
    try:
        recu_attente = paiement_attente.recu
        print(f"   ❌ Reçu créé par erreur: {recu_attente.numero_recu}")
        return False
    except Recu.DoesNotExist:
        print("   ✅ Aucun reçu créé (comportement attendu)")
    
    # 6. Test de validation d'un paiement
    print("\n6. ✅ Test de validation d'un paiement...")
    
    # Valider le paiement en attente
    if paiement_attente.valider_paiement(utilisateur):
        print(f"   ✅ Paiement validé avec succès")
        
        # Attendre un peu pour que les signaux se déclenchent
        time.sleep(1)
        
        # Vérifier si un reçu a été créé
        try:
            recu_valide = paiement_attente.recu
            print(f"   ✅ Reçu créé après validation: {recu_valide.numero_recu}")
            print(f"      - Généré automatiquement: {recu_valide.genere_automatiquement}")
            print(f"      - Valide: {recu_valide.valide}")
        except Recu.DoesNotExist:
            print("   ❌ Reçu non créé après validation")
            return False
    else:
        print("   ❌ Échec de la validation du paiement")
        return False
    
    # 7. Test de modification du statut
    print("\n7. 🔄 Test de modification du statut...")
    
    # Créer un autre paiement en attente
    paiement_modif = Paiement.objects.create(
        contrat=contrat,
        montant=750.00,
        type_paiement='loyer',
        mode_paiement='especes',
        date_paiement=timezone.now().date(),
        statut='en_attente',
        cree_par=utilisateur,
        notes='Test automatique - Paiement à modifier'
    )
    print(f"   ✅ Paiement créé: {paiement_modif.id}")
    
    # Modifier le statut vers "valide"
    paiement_modif.statut = 'valide'
    paiement_modif.valide_par = utilisateur
    paiement_modif.date_encaissement = timezone.now().date()
    paiement_modif.save()
    
    # Appeler la méthode de génération automatique
    paiement_modif.generer_recu_automatique(utilisateur)
    
    # Vérifier si un reçu a été créé
    try:
        recu_modif = paiement_modif.recu
        print(f"   ✅ Reçu créé après modification: {recu_modif.numero_recu}")
    except Recu.DoesNotExist:
        print("   ❌ Reçu non créé après modification")
        return False
    
    # 8. Vérification finale
    print("\n8. 📊 VÉRIFICATION FINALE")
    
    nb_paiements_final = Paiement.objects.count()
    nb_recus_final = Recu.objects.count()
    nb_recus_auto = Recu.objects.filter(genere_automatiquement=True).count()
    
    print(f"   • Paiements totaux: {nb_paiements_final}")
    print(f"   • Reçus totaux: {nb_recus_final}")
    print(f"   • Reçus générés automatiquement: {nb_recus_auto}")
    
    # 9. Nettoyage des données de test
    print("\n9. 🧹 Nettoyage des données de test...")
    
    # Supprimer les paiements de test
    Paiement.objects.filter(notes__icontains='Test automatique').delete()
    
    # Supprimer les reçus de test
    Recu.objects.filter(paiement__notes__icontains='Test automatique').delete()
    
    print("   ✅ Données de test supprimées")
    
    # 10. Résumé du test
    print("\n" + "=" * 60)
    print("🎯 RÉSULTATS DU TEST")
    print("=" * 60)
    
    if nb_recus_auto >= 3:  # Au moins 3 reçus générés automatiquement
        print("✅ SUCCÈS: La génération automatique des reçus fonctionne correctement!")
        print(f"   • Reçus générés automatiquement: {nb_recus_auto}")
        print(f"   • Processus de création: ✅")
        print(f"   • Processus de validation: ✅")
        print(f"   • Processus de modification: ✅")
        return True
    else:
        print("❌ ÉCHEC: La génération automatique des reçus ne fonctionne pas correctement")
        print(f"   • Reçus générés automatiquement: {nb_recus_auto}")
        print(f"   • Reçus attendus: 3")
        return False

if __name__ == "__main__":
    try:
        succes = test_generation_automatique_recus()
        
        if succes:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
            print("La génération automatique des reçus est opérationnelle.")
        else:
            print("\n💥 CERTAINS TESTS ONT ÉCHOUÉ!")
            print("Vérifiez la configuration et les logs d'erreur.")
            
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU TEST: {e}")
        import traceback
        traceback.print_exc()
