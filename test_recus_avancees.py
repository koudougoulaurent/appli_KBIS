#!/usr/bin/env python
"""
Script de test pour les fonctionnalités avancées des reçus de paiement
Teste la validation, invalidation, envoi par email, changement de template, et statistiques
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.db import transaction

from paiements.models import Paiement, Recu
from contrats.models import Contrat
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien
from utilisateurs.models import Utilisateur

Utilisateur = get_user_model()

def creer_donnees_test():
    """Crée les données de test nécessaires"""
    print("🔧 Création des données de test...")
    
    # Créer un utilisateur de test
    user, created = Utilisateur.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("✅ Utilisateur de test créé")
    
    # Créer un bailleur
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Dupont',
        prenom='Jean',
        defaults={
            'email': 'jean.dupont@email.com',
            'telephone': '0123456789',
            'adresse': '123 Rue de la Paix, 75001 Paris'
        }
    )
    if created:
        print("✅ Bailleur créé")
    
    # Créer un locataire
    locataire, created = Locataire.objects.get_or_create(
        nom='Martin',
        prenom='Marie',
        defaults={
            'email': 'marie.martin@email.com',
            'telephone': '0987654321',
            'adresse_actuelle': '456 Avenue des Champs, 75008 Paris'
        }
    )
    if created:
        print("✅ Locataire créé")
    
    # Créer un type de bien
    type_bien, created = TypeBien.objects.get_or_create(
        nom='Appartement',
        defaults={
            'description': 'Appartement résidentiel'
        }
    )
    if created:
        print("✅ Type de bien créé")
    
    # Créer une propriété
    propriete, created = Propriete.objects.get_or_create(
        adresse='789 Boulevard Saint-Germain',
        defaults={
            'titre': 'Appartement de luxe',
            'ville': 'Paris',
            'code_postal': '75006',
            'surface': 85.5,
            'nombre_pieces': 4,
            'nombre_chambres': 2,
            'nombre_salles_bain': 1,
            'prix_achat': 450000,
            'type_bien': type_bien,
            'bailleur': bailleur
        }
    )
    if created:
        print("✅ Propriété créée")
    
    # Créer un contrat
    contrat, created = Contrat.objects.get_or_create(
        numero_contrat='CONTR-2024-001',
        defaults={
            'propriete': propriete,
            'locataire': locataire,
            'date_debut': datetime.now().date(),
            'date_fin': datetime.now().date() + timedelta(days=365),
            'date_signature': datetime.now().date(),
            'loyer_mensuel': 1500.00,
            'charges_mensuelles': 150.00,
            'depot_garantie': 3000.00,
            'est_actif': True
        }
    )
    if created:
        print("✅ Contrat créé")
    
    return user, bailleur, locataire, propriete, contrat

def test_creation_recu_automatique(contrat, user):
    """Teste la création automatique d'un reçu"""
    print("\n🧪 Test de création automatique de reçu...")
    
    # Créer un paiement validé
    paiement = Paiement.objects.create(
        contrat=contrat,
        montant=1500.00,
        type_paiement='loyer',
        mode_paiement='virement',
        date_paiement=datetime.now().date(),
        statut='valide',
        cree_par=user,
        valide_par=user
    )
    print(f"✅ Paiement créé: {paiement.id}")
    
    # Vérifier que le reçu a été créé automatiquement
    try:
        recu = paiement.recu
        print(f"✅ Reçu créé automatiquement: {recu.numero_recu}")
        print(f"   - Généré automatiquement: {recu.genere_automatiquement}")
        print(f"   - Template: {recu.template_utilise}")
        print(f"   - Valide: {recu.valide}")
        return recu
    except Recu.DoesNotExist:
        print("❌ Reçu non créé automatiquement")
        return None

def test_validation_recu(recu, user):
    """Teste la validation d'un reçu"""
    print("\n🧪 Test de validation de reçu...")
    
    # Valider le reçu
    recu.valider_recu(user)
    print(f"✅ Reçu validé par {user.username}")
    print(f"   - Date de validation: {recu.date_validation}")
    print(f"   - Validé par: {recu.valide_par}")
    
    # Vérifier les méthodes
    print(f"   - Peut être imprimé: {recu.peut_etre_imprime()}")
    print(f"   - Peut être envoyé par email: {recu.peut_etre_envoye_email()}")
    print(f"   - Statut d'affichage: {recu.get_statut_display()}")
    print(f"   - Couleur du statut: {recu.get_statut_color()}")

def test_invalidation_recu(recu, user):
    """Teste l'invalidation d'un reçu"""
    print("\n🧪 Test d'invalidation de reçu...")
    
    # Invalider le reçu
    motif = "Test d'invalidation"
    recu.invalider_recu(user, motif)
    print(f"✅ Reçu invalidé par {user.username}")
    print(f"   - Motif: {motif}")
    print(f"   - Notes internes: {recu.notes_internes}")
    print(f"   - Peut être imprimé: {recu.peut_etre_imprime()}")

def test_impression_recu(recu, user):
    """Teste l'impression d'un reçu"""
    print("\n🧪 Test d'impression de reçu...")
    
    # Re-valider le reçu pour pouvoir l'imprimer
    recu.valider_recu(user)
    
    # Marquer comme imprimé
    recu.marquer_imprime(user)
    print(f"✅ Reçu marqué comme imprimé")
    print(f"   - Nombre d'impressions: {recu.nombre_impressions}")
    print(f"   - Date d'impression: {recu.date_impression}")
    print(f"   - Imprimé par: {recu.imprime_par}")

def test_envoi_email_recu(recu):
    """Teste l'envoi par email d'un reçu"""
    print("\n🧪 Test d'envoi par email...")
    
    # Marquer comme envoyé par email
    email_destinataire = "test@example.com"
    recu.marquer_envoye_email(email_destinataire)
    print(f"✅ Reçu marqué comme envoyé par email")
    print(f"   - Email destinataire: {recu.email_destinataire}")
    print(f"   - Date d'envoi: {recu.date_envoi_email}")
    print(f"   - Nombre d'emails: {recu.nombre_emails}")

def test_changement_template(recu):
    """Teste le changement de template"""
    print("\n🧪 Test de changement de template...")
    
    # Changer le template
    ancien_template = recu.template_utilise
    recu.template_utilise = 'professionnel'
    recu.save()
    
    print(f"✅ Template changé de '{ancien_template}' vers '{recu.template_utilise}'")
    print(f"   - Nouveau template: {recu.get_template_utilise_display()}")

def test_methodes_avancees(recu):
    """Teste les méthodes avancées du reçu"""
    print("\n🧪 Test des méthodes avancées...")
    
    # Test des informations de paiement
    infos = recu.get_informations_paiement()
    print(f"✅ Informations de paiement récupérées:")
    print(f"   - Montant: {infos['montant']} F CFA")
    print(f"   - Montant en lettres: {infos['montant_lettres']}")
    print(f"   - Locataire: {infos['locataire_nom']} {infos['locataire_prenom']}")
    print(f"   - Propriété: {infos['propriete_adresse']}")
    
    # Test du contexte de template
    context = recu.get_template_context()
    print(f"✅ Contexte de template récupéré avec {len(context)} éléments")

def test_urls_recus():
    """Teste la résolution des URLs des reçus"""
    print("\n🧪 Test de résolution des URLs...")
    
    client = Client()
    
    # URLs à tester
    urls_a_tester = [
        'paiements:recus_liste',
        'paiements:statistiques_recus',
        'paiements:export_recus',
        'paiements:api_recus_avancees',
    ]
    
    for url_name in urls_a_tester:
        try:
            url = reverse(url_name)
            print(f"✅ URL '{url_name}' résolue: {url}")
        except Exception as e:
            print(f"❌ Erreur pour URL '{url_name}': {e}")

def test_statistiques():
    """Teste les statistiques des reçus"""
    print("\n🧪 Test des statistiques...")
    
    # Compter les reçus
    total_recus = Recu.objects.count()
    recus_valides = Recu.objects.filter(valide=True).count()
    recus_imprimes = Recu.objects.filter(imprime=True).count()
    recus_envoyes_email = Recu.objects.filter(envoye_email=True).count()
    
    print(f"✅ Statistiques des reçus:")
    print(f"   - Total: {total_recus}")
    print(f"   - Validés: {recus_valides}")
    print(f"   - Imprimés: {recus_imprimes}")
    print(f"   - Envoyés par email: {recus_envoyes_email}")
    
    # Statistiques par template
    stats_templates = Recu.objects.values('template_utilise').annotate(
        count=django.db.models.Count('id')
    )
    print(f"   - Répartition par template:")
    for stat in stats_templates:
        print(f"     * {stat['template_utilise']}: {stat['count']}")

def nettoyer_donnees_test():
    """Nettoie les données de test"""
    print("\n🧹 Nettoyage des données de test...")
    
    # Supprimer les reçus de test
    Recu.objects.filter(paiement__contrat__numero_contrat='CONTR-2024-001').delete()
    print("✅ Reçus de test supprimés")
    
    # Supprimer les paiements de test
    Paiement.objects.filter(contrat__numero_contrat='CONTR-2024-001').delete()
    print("✅ Paiements de test supprimés")
    
    # Supprimer le contrat de test
    Contrat.objects.filter(numero_contrat='CONTR-2024-001').delete()
    print("✅ Contrat de test supprimé")

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests des fonctionnalités avancées des reçus")
    print("=" * 60)
    
    try:
        # Créer les données de test
        user, bailleur, locataire, propriete, contrat = creer_donnees_test()
        
        # Tests des fonctionnalités
        recu = test_creation_recu_automatique(contrat, user)
        if recu:
            test_validation_recu(recu, user)
            test_impression_recu(recu, user)
            test_envoi_email_recu(recu)
            test_changement_template(recu)
            test_invalidation_recu(recu, user)
            test_methodes_avancees(recu)
        
        test_urls_recus()
        test_statistiques()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests des fonctionnalités avancées ont réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer les données de test
        nettoyer_donnees_test()
        print("\n🎉 Tests terminés avec succès!")

if __name__ == '__main__':
    main() 