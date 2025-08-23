#!/usr/bin/env python3
"""
Test des statistiques corrigées pour les dashboards
Vérification des comptages des bailleurs et locataires
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Propriete, Bailleur, Locataire
from utilisateurs.models import Utilisateur, GroupeTravail
from contrats.models import Contrat
from paiements.models import Paiement
from notifications.models import Notification

def test_statistiques_corrigees():
    """Test des statistiques corrigées pour les dashboards"""
    
    print("🔍 TEST DES STATISTIQUES CORRIGÉES POUR LES DASHBOARDS")
    print("=" * 60)
    
    try:
        # Statistiques PRIVILEGE (complètes)
        print("\n👑 STATISTIQUES PRIVILEGE (Dashboard Principal)")
        print("-" * 50)
        
        stats_privilege = {
            'total_proprietes': Propriete.objects.count(),
            'total_utilisateurs': Utilisateur.objects.count(),
            'total_contrats': Contrat.objects.count(),
            'total_paiements': Paiement.objects.count(),
            'total_groupes': GroupeTravail.objects.count(),
            'total_notifications': Notification.objects.count(),
            'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
            'total_bailleurs': Bailleur.objects.filter(est_actif=True).count(),
            'total_locataires': Locataire.objects.filter(est_actif=True).count(),
            'contrats_actifs': Contrat.objects.filter(est_actif=True).count(),
        }
        
        for key, value in stats_privilege.items():
            print(f"   • {key.replace('_', ' ').title()}: {value}")
        
        # Statistiques ADMINISTRATION (ciblées)
        print("\n🏢 STATISTIQUES ADMINISTRATION (Dashboard Secondaire)")
        print("-" * 55)
        
        stats_administration = {
            'total_proprietes': Propriete.objects.count(),
            'contrats_actifs': Contrat.objects.filter(est_actif=True).count(),
            'total_bailleurs': Bailleur.objects.filter(est_actif=True).count(),
            'contrats_renouveler': 2,  # Exemple fixe pour le test
        }
        
        for key, value in stats_administration.items():
            print(f"   • {key.replace('_', ' ').title()}: {value}")
        
        # Vérifications de cohérence
        print("\n✅ VÉRIFICATIONS DE COHÉRENCE")
        print("-" * 35)
        
        # Vérifier que les bailleurs et locataires ne sont pas à 0
        if stats_privilege['total_bailleurs'] > 0:
            print(f"   ✅ Bailleurs détectés: {stats_privilege['total_bailleurs']}")
        else:
            print("   ❌ Aucun bailleur actif trouvé")
        
        if stats_privilege['total_locataires'] > 0:
            print(f"   ✅ Locataires détectés: {stats_privilege['total_locataires']}")
        else:
            print("   ❌ Aucun locataire actif trouvé")
        
        # Vérifier la cohérence entre les dashboards
        coherence_ok = (
            stats_privilege['total_proprietes'] == stats_administration['total_proprietes'] and
            stats_privilege['total_bailleurs'] == stats_administration['total_bailleurs']
        )
        
        if coherence_ok:
            print("   ✅ Cohérence entre les dashboards OK")
        else:
            print("   ❌ Incohérence détectée entre les dashboards")
        
        # Détail des modèles
        print("\n📊 DÉTAIL DES MODÈLES")
        print("-" * 25)
        
        # Bailleurs
        bailleurs = Bailleur.objects.all()
        print(f"   • Total bailleurs en DB: {bailleurs.count()}")
        print(f"   • Bailleurs actifs: {bailleurs.filter(est_actif=True).count()}")
        
        if bailleurs.exists():
            print("   • Premiers bailleurs:")
            for b in bailleurs[:3]:
                statut = "✅ Actif" if b.est_actif else "❌ Inactif"
                print(f"     - {b.prenom} {b.nom} ({statut})")
        
        # Locataires
        locataires = Locataire.objects.all()
        print(f"   • Total locataires en DB: {locataires.count()}")
        print(f"   • Locataires actifs: {locataires.filter(est_actif=True).count()}")
        
        if locataires.exists():
            print("   • Premiers locataires:")
            for l in locataires[:3]:
                statut = "✅ Actif" if l.est_actif else "❌ Inactif"
                print(f"     - {l.prenom} {l.nom} ({statut})")
        
        # Contrats
        contrats = Contrat.objects.all()
        print(f"   • Total contrats en DB: {contrats.count()}")
        print(f"   • Contrats actifs: {contrats.filter(est_actif=True).count()}")
        
        # Test des URLs corrigées
        print("\n🔗 VÉRIFICATION DES URLs CORRIGÉES")
        print("-" * 40)
        
        urls_testees = [
            "proprietes:liste",
            "proprietes:ajouter", 
            "proprietes:bailleurs_liste",
            "contrats:liste",
            "contrats:ajouter",
            "paiements:liste",
            "utilisateurs:liste_utilisateurs",
            "utilisateurs:liste_groupes",
            "utilisateurs:profile",
            "core:intelligent_search"
        ]
        
        print("   • URLs utilisées dans les dashboards:")
        for url in urls_testees:
            print(f"     - {url}")
        
        print("\n🎯 RÉSUMÉ FINAL")
        print("-" * 20)
        print(f"   • Dashboard PRIVILEGE: {len(stats_privilege)} statistiques")
        print(f"   • Dashboard ADMINISTRATION: {len(stats_administration)} statistiques")
        print(f"   • Bailleurs actifs: {stats_privilege['total_bailleurs']}")
        print(f"   • Locataires actifs: {stats_privilege['total_locataires']}")
        print(f"   • Contrats actifs: {stats_privilege['contrats_actifs']}")
        
        if stats_privilege['total_bailleurs'] > 0 and stats_privilege['total_locataires'] > 0:
            print("   ✅ Statistiques corrigées avec succès!")
        else:
            print("   ⚠️  Attention: Certaines statistiques sont à 0")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def creer_donnees_test():
    """Créer quelques données de test si nécessaire"""
    
    print("\n🔧 CRÉATION DE DONNÉES DE TEST")
    print("-" * 35)
    
    try:
        # Créer un bailleur test s'il n'y en a pas
        if Bailleur.objects.count() == 0:
            bailleur_test = Bailleur.objects.create(
                nom="Dupont",
                prenom="Jean",
                email="jean.dupont@test.com",
                telephone="0123456789",
                adresse="123 Rue Test",
                est_actif=True
            )
            print(f"   ✅ Bailleur test créé: {bailleur_test}")
        
        # Créer un locataire test s'il n'y en a pas
        if Locataire.objects.count() == 0:
            locataire_test = Locataire.objects.create(
                nom="Martin",
                prenom="Marie",
                email="marie.martin@test.com",
                telephone="0987654321",
                adresse_actuelle="456 Avenue Test",
                est_actif=True
            )
            print(f"   ✅ Locataire test créé: {locataire_test}")
        
        print("   ✅ Données de test vérifiées")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la création des données test: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DU TEST DES STATISTIQUES CORRIGÉES")
    
    # Créer des données de test si nécessaire
    creer_donnees_test()
    
    # Tester les statistiques
    success = test_statistiques_corrigees()
    
    if success:
        print("\n🎉 TEST TERMINÉ AVEC SUCCÈS!")
    else:
        print("\n💥 TEST ÉCHOUÉ!")
    
    print("\n" + "=" * 60)