#!/usr/bin/env python
"""
Script de démonstration des fonctionnalités avancées des reçus de paiement
Montre toutes les nouvelles fonctionnalités : validation, templates multiples, statistiques, etc.
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
from django.db import transaction
from django.utils import timezone

from paiements.models import Paiement, Recu
from contrats.models import Contrat
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien

Utilisateur = get_user_model()

def creer_donnees_demo():
    """Crée des données de démonstration complètes"""
    print("🎭 Création des données de démonstration...")
    
    # Créer un utilisateur admin
    user, created = Utilisateur.objects.get_or_create(
        username='admin_demo',
        defaults={
            'email': 'admin@gestimmob.fr',
            'first_name': 'Admin',
            'last_name': 'Demo',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
        print("✅ Utilisateur admin créé")
    
    # Créer plusieurs bailleurs
    bailleurs = []
    for i in range(3):
        bailleur, created = Bailleur.objects.get_or_create(
            nom=f'Bailleur{i+1}',
            prenom=f'Prénom{i+1}',
            defaults={
                'email': f'bailleur{i+1}@email.com',
                'telephone': f'012345678{i}',
                'adresse': f'{100+i} Rue de la Paix, 7500{i} Paris'
            }
        )
        if created:
            print(f"✅ Bailleur {i+1} créé")
        bailleurs.append(bailleur)
    
    # Créer plusieurs locataires
    locataires = []
    for i in range(5):
        locataire, created = Locataire.objects.get_or_create(
            nom=f'Locataire{i+1}',
            prenom=f'Prénom{i+1}',
            defaults={
                'email': f'locataire{i+1}@email.com',
                'telephone': f'098765432{i}',
                'adresse_actuelle': f'{200+i} Avenue des Champs, 7500{i} Paris'
            }
        )
        if created:
            print(f"✅ Locataire {i+1} créé")
        locataires.append(locataire)
    
    # Créer des types de biens
    types_bien = []
    for type_nom in ['Appartement', 'Maison', 'Studio']:
        type_bien, created = TypeBien.objects.get_or_create(
            nom=type_nom,
            defaults={'description': f'Type de bien: {type_nom}'}
        )
        if created:
            print(f"✅ Type de bien '{type_nom}' créé")
        types_bien.append(type_bien)
    
    # Créer plusieurs propriétés
    proprietes = []
    for i in range(5):
        propriete, created = Propriete.objects.get_or_create(
            adresse=f'{300+i} Boulevard Saint-Germain',
            defaults={
                'titre': f'Propriété {i+1}',
                'ville': 'Paris',
                'code_postal': f'7500{i}',
                'surface': 80 + i * 10,
                'nombre_pieces': 3 + i,
                'nombre_chambres': 2 + i,
                'nombre_salles_bain': 1 + (i % 2),
                'prix_achat': 400000 + i * 50000,
                'type_bien': types_bien[i % len(types_bien)],
                'bailleur': bailleurs[i % len(bailleurs)]
            }
        )
        if created:
            print(f"✅ Propriété {i+1} créée")
        proprietes.append(propriete)
    
    # Créer plusieurs contrats
    contrats = []
    for i in range(5):
        contrat, created = Contrat.objects.get_or_create(
            numero_contrat=f'CONTR-DEMO-{i+1:03d}',
            defaults={
                'propriete': proprietes[i],
                'locataire': locataires[i],
                'date_debut': datetime.now().date() - timedelta(days=30*i),
                'date_fin': datetime.now().date() + timedelta(days=365 - 30*i),
                'date_signature': datetime.now().date() - timedelta(days=30*i + 5),
                'loyer_mensuel': 1200 + i * 100,
                'charges_mensuelles': 100 + i * 20,
                'depot_garantie': 2400 + i * 200,
                'est_actif': True
            }
        )
        if created:
            print(f"✅ Contrat {i+1} créé")
        contrats.append(contrat)
    
    return user, bailleurs, locataires, proprietes, contrats

def creer_paiements_et_recus(contrats, user):
    """Crée des paiements et reçus de démonstration"""
    print("\n💰 Création des paiements et reçus...")
    
    types_paiement = ['loyer', 'charges', 'depot_garantie', 'regularisation']
    modes_paiement = ['virement', 'cheque', 'especes', 'prelevement']
    templates = ['standard', 'professionnel', 'simplifie', 'luxe', 'entreprise']
    
    paiements_crees = []
    
    for i, contrat in enumerate(contrats):
        # Créer plusieurs paiements par contrat
        for j in range(3):
            paiement = Paiement.objects.create(
                contrat=contrat,
                montant=contrat.loyer_mensuel + (j * 50),
                type_paiement=types_paiement[j % len(types_paiement)],
                mode_paiement=modes_paiement[j % len(modes_paiement)],
                date_paiement=datetime.now().date() - timedelta(days=j*30),
                statut='valide',
                cree_par=user,
                valide_par=user
            )
            paiements_crees.append(paiement)
            print(f"✅ Paiement {i+1}-{j+1} créé: {paiement.montant} XOF")
    
    # Attendre un peu pour que les reçus soient créés automatiquement
    import time
    time.sleep(1)
    
    # Récupérer tous les reçus créés
    recus = Recu.objects.filter(paiement__in=paiements_crees)
    print(f"✅ {recus.count()} reçus créés automatiquement")
    
    return paiements_crees, recus

def demontrer_fonctionnalites_avancees(recus, user):
    """Démontre toutes les fonctionnalités avancées"""
    print("\n🎯 Démonstration des fonctionnalités avancées...")
    
    if not recus.exists():
        print("❌ Aucun reçu disponible pour la démonstration")
        return
    
    # Prendre le premier reçu pour les démonstrations
    recu = recus.first()
    print(f"\n📋 Reçu de démonstration: {recu.numero_recu}")
    
    # 1. Démonstration de la validation
    print("\n1️⃣ Validation du reçu:")
    recu.valider_recu(user)
    print(f"   ✅ Reçu validé par {user.username}")
    print(f"   📅 Date de validation: {recu.date_validation}")
    print(f"   🎯 Statut: {recu.get_statut_display()}")
    print(f"   🎨 Couleur: {recu.get_statut_color()}")
    
    # 2. Démonstration de l'impression
    print("\n2️⃣ Simulation d'impression:")
    recu.marquer_imprime(user)
    print(f"   ✅ Reçu marqué comme imprimé")
    print(f"   🖨️ Nombre d'impressions: {recu.nombre_impressions}")
    print(f"   📅 Date d'impression: {recu.date_impression}")
    
    # 3. Démonstration de l'envoi par email
    print("\n3️⃣ Simulation d'envoi par email:")
    recu.marquer_envoye_email("demo@example.com")
    print(f"   ✅ Reçu marqué comme envoyé par email")
    print(f"   📧 Email destinataire: {recu.email_destinataire}")
    print(f"   📅 Date d'envoi: {recu.date_envoi_email}")
    print(f"   📊 Nombre d'emails: {recu.nombre_emails}")
    
    # 4. Démonstration du changement de template
    print("\n4️⃣ Changement de template:")
    ancien_template = recu.template_utilise
    recu.template_utilise = 'professionnel'
    recu.save()
    print(f"   ✅ Template changé de '{ancien_template}' vers '{recu.template_utilise}'")
    print(f"   🎨 Nouveau template: {recu.get_template_utilise_display()}")
    
    # 5. Démonstration des méthodes avancées
    print("\n5️⃣ Méthodes avancées:")
    infos = recu.get_informations_paiement()
    print(f"   💰 Montant: {infos['montant']} XOF")
    print(f"   📝 Montant en lettres: {infos['montant_lettres']}")
    print(f"   👤 Locataire: {infos['locataire_nom']} {infos['locataire_prenom']}")
    print(f"   🏠 Propriété: {infos['propriete_adresse']}")
    print(f"   🏢 Bailleur: {infos['bailleur_nom']} {infos['bailleur_prenom']}")
    
    # 6. Démonstration de l'invalidation
    print("\n6️⃣ Invalidation du reçu:")
    recu.invalider_recu(user, "Démonstration d'invalidation")
    print(f"   ⚠️ Reçu invalidé")
    print(f"   📝 Notes: {recu.notes_internes}")
    print(f"   ❌ Peut être imprimé: {recu.peut_etre_imprime()}")
    
    # 7. Re-validation pour continuer les tests
    print("\n7️⃣ Re-validation:")
    recu.valider_recu(user)
    print(f"   ✅ Reçu re-validé")

def afficher_statistiques_avancees():
    """Affiche des statistiques avancées"""
    print("\n📊 Statistiques avancées des reçus:")
    print("=" * 50)
    
    # Statistiques générales
    total_recus = Recu.objects.count()
    recus_valides = Recu.objects.filter(valide=True).count()
    recus_imprimes = Recu.objects.filter(imprime=True).count()
    recus_envoyes_email = Recu.objects.filter(envoye_email=True).count()
    
    print(f"📈 Statistiques générales:")
    print(f"   • Total reçus: {total_recus}")
    print(f"   • Reçus validés: {recus_valides} ({recus_valides/total_recus*100:.1f}%)")
    print(f"   • Reçus imprimés: {recus_imprimes} ({recus_imprimes/total_recus*100:.1f}%)")
    print(f"   • Reçus envoyés par email: {recus_envoyes_email} ({recus_envoyes_email/total_recus*100:.1f}%)")
    
    # Statistiques par template
    print(f"\n🎨 Répartition par template:")
    stats_templates = Recu.objects.values('template_utilise').annotate(
        count=django.db.models.Count('id')
    ).order_by('-count')
    
    for stat in stats_templates:
        template = stat['template_utilise']
        count = stat['count']
        percentage = count / total_recus * 100
        print(f"   • {template.title()}: {count} ({percentage:.1f}%)")
    
    # Top des reçus les plus utilisés
    print(f"\n🏆 Top des reçus les plus utilisés:")
    top_recus = Recu.objects.order_by('-nombre_impressions', '-nombre_emails')[:5]
    
    for i, recu in enumerate(top_recus, 1):
        print(f"   {i}. {recu.numero_recu} - {recu.paiement.montant} XOF")
        print(f"      Impressions: {recu.nombre_impressions}, Emails: {recu.nombre_emails}")
    
    # Montant total des reçus
    montant_total = Recu.objects.aggregate(
        total=django.db.models.Sum('paiement__montant')
    )['total'] or 0
    print(f"\n💰 Montant total des reçus: {montant_total:,.2f} XOF")

def nettoyer_donnees_demo():
    """Nettoie les données de démonstration"""
    print("\n🧹 Nettoyage des données de démonstration...")
    
    # Supprimer les reçus de démo
    recus_demo = Recu.objects.filter(
        paiement__contrat__numero_contrat__startswith='CONTR-DEMO-'
    )
    count_recus = recus_demo.count()
    recus_demo.delete()
    print(f"✅ {count_recus} reçus de démo supprimés")
    
    # Supprimer les paiements de démo
    paiements_demo = Paiement.objects.filter(
        contrat__numero_contrat__startswith='CONTR-DEMO-'
    )
    count_paiements = paiements_demo.count()
    paiements_demo.delete()
    print(f"✅ {count_paiements} paiements de démo supprimés")
    
    # Supprimer les contrats de démo
    contrats_demo = Contrat.objects.filter(
        numero_contrat__startswith='CONTR-DEMO-'
    )
    count_contrats = contrats_demo.count()
    contrats_demo.delete()
    print(f"✅ {count_contrats} contrats de démo supprimés")

def main():
    """Fonction principale de démonstration"""
    print("🎭 DÉMONSTRATION DES FONCTIONNALITÉS AVANCÉES DES REÇUS")
    print("=" * 60)
    
    try:
        # Créer les données de démonstration
        user, bailleurs, locataires, proprietes, contrats = creer_donnees_demo()
        
        # Créer des paiements et reçus
        paiements, recus = creer_paiements_et_recus(contrats, user)
        
        # Démontrer les fonctionnalités
        demontrer_fonctionnalites_avancees(recus, user)
        
        # Afficher les statistiques
        afficher_statistiques_avancees()
        
        print("\n" + "=" * 60)
        print("🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS!")
        print("\n✨ Fonctionnalités démontrées:")
        print("   • Génération automatique de reçus")
        print("   • Validation et invalidation de reçus")
        print("   • Impression et suivi des impressions")
        print("   • Envoi par email et suivi")
        print("   • Changement de templates")
        print("   • Méthodes avancées de récupération d'informations")
        print("   • Statistiques détaillées")
        print("   • Gestion des formats d'impression")
        print("   • Suivi des versions de templates")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer les données de démonstration
        nettoyer_donnees_demo()
        print("\n🎭 Démonstration terminée!")

if __name__ == '__main__':
    main() 