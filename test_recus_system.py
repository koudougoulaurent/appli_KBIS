#!/usr/bin/env python
"""
Script de test pour le système de reçus automatiques
Teste la génération, l'impression et la gestion des reçus
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from paiements.models import Paiement, Recu
from contrats.models import Contrat
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien

Utilisateur = get_user_model()

def test_systeme_recus():
    """Test complet du système de reçus"""
    print("🧪 TEST DU SYSTÈME DE REÇUS AUTOMATIQUES")
    print("=" * 50)
    
    # 1. Vérifier les données existantes
    print("\n1. 📊 Vérification des données existantes...")
    
    paiements = Paiement.objects.all()
    recus = Recu.objects.all()
    
    print(f"   - Paiements totaux: {paiements.count()}")
    print(f"   - Reçus existants: {recus.count()}")
    print(f"   - Paiements validés: {paiements.filter(statut='valide').count()}")
    print(f"   - Paiements sans reçu: {paiements.filter(statut='valide').exclude(recu__isnull=False).count()}")
    
    # 2. Créer des données de test si nécessaire
    print("\n2. 🏗️ Création de données de test...")
    
    # Créer un utilisateur de test
    utilisateur, created = Utilisateur.objects.get_or_create(
        username='test_recus',
        defaults={
            'email': 'test@recus.com',
            'first_name': 'Test',
            'last_name': 'Reçus',
            'is_staff': True
        }
    )
    
    if created:
        utilisateur.set_password('test123')
        utilisateur.save()
        print(f"   ✅ Utilisateur de test créé: {utilisateur.username}")
    else:
        print(f"   ℹ️ Utilisateur de test existant: {utilisateur.username}")
    
    # Créer des données de test si pas assez de paiements
    if paiements.count() < 5:
        print("   🔧 Création de paiements de test...")
        create_paiements_test(utilisateur)
        paiements = Paiement.objects.all()
        print(f"   ✅ {paiements.count()} paiements créés")
    
    # 3. Tester la génération automatique
    print("\n3. 🔄 Test de la génération automatique...")
    
    # Sélectionner des paiements validés sans reçu
    paiements_sans_recu = paiements.filter(statut='valide').exclude(recu__isnull=False)
    
    if paiements_sans_recu.exists():
        print(f"   📝 Génération de {paiements_sans_recu.count()} reçus...")
        
        for paiement in paiements_sans_recu[:3]:  # Limiter à 3 pour le test
            recu = paiement.generer_recu_automatique()
            print(f"   ✅ Reçu généré: {recu.numero_recu} pour paiement {paiement.id}")
    else:
        print("   ℹ️ Aucun paiement sans reçu à traiter")
    
    # 4. Vérifier les reçus générés
    print("\n4. 📋 Vérification des reçus générés...")
    
    recus = Recu.objects.all()
    print(f"   - Total reçus: {recus.count()}")
    print(f"   - Reçus imprimés: {recus.filter(imprime=True).count()}")
    print(f"   - Reçus non imprimés: {recus.filter(imprime=False).count()}")
    print(f"   - Reçus générés automatiquement: {recus.filter(genere_automatiquement=True).count()}")
    
    # 5. Tester les fonctionnalités des reçus
    print("\n5. 🧪 Test des fonctionnalités des reçus...")
    
    if recus.exists():
        recu_test = recus.first()
        
        # Test des méthodes
        print(f"   📄 Test reçu: {recu_test.numero_recu}")
        print(f"   💰 Montant: {recu_test.paiement.montant} F CFA")
        print(f"   📝 Montant en lettres: {recu_test.get_montant_en_lettres()}")
        
        # Test des informations
        infos = recu_test.get_informations_paiement()
        print(f"   👤 Locataire: {infos['locataire']}")
        print(f"   🏠 Propriété: {infos['propriete'].titre}")
        print(f"   📅 Date émission: {recu_test.date_emission}")
        
        # Test du marquage comme imprimé
        if not recu_test.imprime:
            recu_test.marquer_imprime(utilisateur)
            print(f"   ✅ Reçu marqué comme imprimé par {utilisateur.username}")
        
        # Test du marquage comme envoyé par email
        if not recu_test.envoye_email:
            recu_test.marquer_envoye_email()
            print(f"   ✅ Reçu marqué comme envoyé par email")
    
    # 6. Statistiques finales
    print("\n6. 📊 Statistiques finales...")
    
    recus_finaux = Recu.objects.all()
    paiements_finaux = Paiement.objects.all()
    
    print(f"   - Paiements totaux: {paiements_finaux.count()}")
    print(f"   - Reçus totaux: {recus_finaux.count()}")
    print(f"   - Taux de couverture: {(recus_finaux.count() / paiements_finaux.filter(statut='valide').count() * 100):.1f}%")
    
    # 7. Test des URLs
    print("\n7. 🔗 Test des URLs...")
    
    urls_a_tester = [
        'paiements:recus_liste',
        'paiements:recus_generer_automatiques',
        'paiements:api_recus_stats',
    ]
    
    for url_name in urls_a_tester:
        try:
            from django.urls import reverse
            url = reverse(url_name)
            print(f"   ✅ URL {url_name}: {url}")
        except Exception as e:
            print(f"   ❌ URL {url_name}: Erreur - {e}")
    
    print("\n🎉 TEST TERMINÉ AVEC SUCCÈS!")
    print("=" * 50)
    
    return True

def create_paiements_test(utilisateur):
    """Crée des paiements de test pour les tests"""
    
    # Créer des données de base si nécessaire
    type_bien, _ = TypeBien.objects.get_or_create(nom='Appartement')
    
    bailleur, _ = Bailleur.objects.get_or_create(
        nom='Dupont',
        prenom='Jean',
        defaults={'email': 'jean.dupont@email.com'}
    )
    
    locataire, _ = Locataire.objects.get_or_create(
        nom='Martin',
        prenom='Marie',
        defaults={'email': 'marie.martin@email.com'}
    )
    
    propriete, _ = Propriete.objects.get_or_create(
        titre='Appartement Test',
        defaults={
            'bailleur': bailleur,
            'type_bien': type_bien,
            'adresse': '123 Rue Test',
            'ville': 'Paris',
            'code_postal': '75001',
            'surface': 50,
            'loyer_actuel': 800,
            'disponible': False
        }
    )
    
    contrat, _ = Contrat.objects.get_or_create(
        numero_contrat='CTR-TEST-001',
        defaults={
            'propriete': propriete,
            'bailleur': bailleur,
            'locataire': locataire,
            'loyer_mensuel': 800,
            'charges_mensuelles': 100,
            'date_debut': datetime.now().date(),
            'date_fin': datetime.now().date() + timedelta(days=365),
            'est_actif': True,
            'cree_par': utilisateur
        }
    )
    
    # Créer des paiements de test
    paiements_data = [
        {'montant': 800, 'type_paiement': 'loyer', 'statut': 'valide'},
        {'montant': 100, 'type_paiement': 'charges', 'statut': 'valide'},
        {'montant': 800, 'type_paiement': 'loyer', 'statut': 'en_attente'},
        {'montant': 100, 'type_paiement': 'charges', 'statut': 'valide'},
        {'montant': 800, 'type_paiement': 'loyer', 'statut': 'valide'},
    ]
    
    for i, data in enumerate(paiements_data):
        Paiement.objects.get_or_create(
            contrat=contrat,
            montant=data['montant'],
            type_paiement=data['type_paiement'],
            statut=data['statut'],
            mode_paiement='virement',
            date_paiement=datetime.now().date() - timedelta(days=30*i),
            defaults={
                'cree_par': utilisateur,
                'valide_par': utilisateur if data['statut'] == 'valide' else None,
                'date_encaissement': datetime.now().date() - timedelta(days=30*i) if data['statut'] == 'valide' else None,
                'notes': f'Paiement de test {i+1}'
            }
        )

if __name__ == "__main__":
    try:
        test_systeme_recus()
        print("\n✅ Tous les tests sont passés avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 