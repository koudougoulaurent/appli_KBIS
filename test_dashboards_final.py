#!/usr/bin/env python
"""
Script de test final pour vérifier tous les dashboards
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
from proprietes.models import Propriete, Bailleur
from contrats.models import Contrat
from paiements.models import Paiement, Retrait
from notifications.models import Notification

def calculer_statistiques_reelles():
    """Calculer les vraies statistiques depuis la base de données"""
    print("📊 Calcul des vraies statistiques:")
    print("-" * 40)
    
    # Statistiques CAISSE
    mois_courant = datetime.now().month
    annee_courante = datetime.now().year
    
    stats_caisse = {
        'paiements_mois': Paiement.objects.filter(
            date_paiement__month=mois_courant,
            date_paiement__year=annee_courante
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'retraits_mois': Retrait.objects.filter(
            date_demande__month=mois_courant,
            date_demande__year=annee_courante
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'cautions_cours': Paiement.objects.filter(
            type_paiement='depot_garantie',
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'paiements_attente': Paiement.objects.filter(statut='en_attente').count(),
    }
    
    # Statistiques ADMINISTRATION
    stats_admin = {
        'total_proprietes': Propriete.objects.count(),
        'contrats_actifs': Contrat.objects.filter(est_actif=True).count(),
        'total_bailleurs': Bailleur.objects.count(),
        'contrats_renouveler': Contrat.objects.filter(
            date_fin__lte=datetime.now() + timedelta(days=30),
            est_actif=True
        ).count(),
    }
    
    # Statistiques CONTROLES
    stats_controles = {
        'paiements_a_valider': Paiement.objects.filter(statut='en_attente').count(),
        'contrats_a_verifier': Contrat.objects.filter(est_actif=True).count(),
        'anomalies': 0,
        'rapports_generes': 0,
    }
    
    # Statistiques PRIVILEGE
    stats_privilege = {
        'total_proprietes': Propriete.objects.count(),
        'total_utilisateurs': Utilisateur.objects.count(),
        'total_contrats': Contrat.objects.count(),
        'total_paiements': Paiement.objects.count(),
        'total_groupes': GroupeTravail.objects.count(),
        'total_notifications': Notification.objects.count(),
        'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
    }
    
    print(f"💰 CAISSE:")
    print(f"   - Paiements du mois: {stats_caisse['paiements_mois']} F CFA")
    print(f"   - Retraits du mois: {stats_caisse['retraits_mois']} F CFA")
    print(f"   - Cautions en cours: {stats_caisse['cautions_cours']} F CFA")
    print(f"   - Paiements en attente: {stats_caisse['paiements_attente']}")
    
    print(f"\n🏠 ADMINISTRATION:")
    print(f"   - Total propriétés: {stats_admin['total_proprietes']}")
    print(f"   - Contrats actifs: {stats_admin['contrats_actifs']}")
    print(f"   - Total bailleurs: {stats_admin['total_bailleurs']}")
    print(f"   - Contrats à renouveler: {stats_admin['contrats_renouveler']}")
    
    print(f"\n🔍 CONTROLES:")
    print(f"   - Paiements à valider: {stats_controles['paiements_a_valider']}")
    print(f"   - Contrats à vérifier: {stats_controles['contrats_a_verifier']}")
    
    print(f"\n👑 PRIVILEGE:")
    print(f"   - Total propriétés: {stats_privilege['total_proprietes']}")
    print(f"   - Total utilisateurs: {stats_privilege['total_utilisateurs']}")
    print(f"   - Total contrats: {stats_privilege['total_contrats']}")
    print(f"   - Total paiements: {stats_privilege['total_paiements']}")
    print(f"   - Total groupes: {stats_privilege['total_groupes']}")
    print(f"   - Total notifications: {stats_privilege['total_notifications']}")
    print(f"   - Utilisateurs actifs: {stats_privilege['utilisateurs_actifs']}")
    
    return {
        'CAISSE': stats_caisse,
        'ADMINISTRATION': stats_admin,
        'CONTROLES': stats_controles,
        'PRIVILEGE': stats_privilege,
    }

def test_dashboard_groupe(groupe_nom, username, password, stats_attendues):
    """Test d'un dashboard spécifique"""
    print(f"\n🔍 Test du dashboard {groupe_nom}")
    print("-" * 40)
    
    # Créer un client de test
    client = Client()
    
    # Authentifier l'utilisateur
    user = authenticate(username=username, password=password)
    if not user:
        print(f"❌ Impossible de s'authentifier avec {username}")
        return False
    
    # Connecter l'utilisateur
    client.force_login(user)
    
    # Accéder au dashboard
    response = client.get(f'/utilisateurs/dashboard/{groupe_nom}/')
    
    if response.status_code == 200:
        print(f"✅ Dashboard {groupe_nom} accessible")
        
        # Vérifier que les statistiques sont présentes dans le contexte
        if hasattr(response, 'context') and response.context and 'stats' in response.context:
            stats_affichées = response.context['stats']
            print(f"✅ Statistiques trouvées dans le contexte")
            
            # Comparer avec les statistiques attendues
            erreurs = []
            for key, valeur_attendue in stats_attendues.items():
                valeur_affichée = stats_affichées.get(key, 0)
                if valeur_affichée != valeur_attendue:
                    erreurs.append(f"   - {key}: attendu {valeur_attendue}, affiché {valeur_affichée}")
                else:
                    print(f"✅ {key}: {valeur_affichée} (correct)")
            
            if erreurs:
                print("❌ Erreurs détectées:")
                for erreur in erreurs:
                    print(erreur)
                return False
            else:
                print("✅ Toutes les statistiques sont correctes !")
                return True
        else:
            print("❌ Aucune statistique trouvée dans le contexte")
            return False
    else:
        print(f"❌ Erreur {response.status_code} pour le dashboard {groupe_nom}")
        return False

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION FINALE DES DASHBOARDS")
    print("=" * 60)
    
    # Calculer les vraies statistiques
    stats_reelles = calculer_statistiques_reelles()
    
    # Configuration des tests par groupe
    tests_config = [
        ('CAISSE', 'test_caisse', 'test123', stats_reelles['CAISSE']),
        ('ADMINISTRATION', 'test_administration', 'test123', stats_reelles['ADMINISTRATION']),
        ('CONTROLES', 'test_controles', 'test123', stats_reelles['CONTROLES']),
        ('PRIVILEGE', 'test_privilege', 'test123', stats_reelles['PRIVILEGE']),
    ]
    
    # Exécuter les tests
    results = []
    for groupe_nom, username, password, stats_attendues in tests_config:
        result = test_dashboard_groupe(groupe_nom, username, password, stats_attendues)
        results.append((groupe_nom, result))
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    for groupe_nom, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"   - Dashboard {groupe_nom}: {status}")
    
    if all(result for _, result in results):
        print("\n🎉 TOUS LES DASHBOARDS AFFICHENT LES VRAIES STATISTIQUES !")
        print("   ✅ Les statistiques sont correctes et à jour")
        print("   ✅ Les données sont synchronisées avec la base")
        print("   ✅ Tous les groupes fonctionnent parfaitement")
    else:
        print("\n⚠️  CERTAINS DASHBOARDS ONT DES PROBLÈMES")
        print("   Vérifiez les erreurs ci-dessus.")

if __name__ == '__main__':
    main() 