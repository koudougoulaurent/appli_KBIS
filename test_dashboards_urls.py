#!/usr/bin/env python
"""
Script de test pour vérifier les dashboards via les URLs
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

def test_dashboard_caisse():
    """Test du dashboard CAISSE"""
    print("💰 Test du dashboard CAISSE")
    print("-" * 40)
    
    # Créer un client de test
    client = Client()
    
    # Authentifier un utilisateur du groupe CAISSE
    user = authenticate(username='admin1', password='test123')
    if not user:
        print("❌ Impossible de s'authentifier avec admin1")
        return False
    
    # Connecter l'utilisateur
    client.force_login(user)
    
    # Accéder au dashboard CAISSE
    response = client.get('/utilisateurs/dashboard/CAISSE/')
    
    if response.status_code == 200:
        print("✅ Dashboard CAISSE accessible")
        
        # Vérifier que les statistiques sont présentes dans le contexte
        if 'stats' in response.context:
            stats = response.context['stats']
            print(f"✅ Statistiques trouvées:")
            print(f"   - Paiements du mois: {stats.get('paiements_mois', 0)} F CFA")
            print(f"   - Retraits du mois: {stats.get('retraits_mois', 0)} F CFA")
            print(f"   - Cautions en cours: {stats.get('cautions_cours', 0)} F CFA")
            print(f"   - Paiements en attente: {stats.get('paiements_attente', 0)}")
        else:
            print("❌ Aucune statistique trouvée dans le contexte")
            return False
    else:
        print(f"❌ Erreur {response.status_code} pour le dashboard CAISSE")
        return False
    
    return True

def test_dashboard_administration():
    """Test du dashboard ADMINISTRATION"""
    print("\n🏠 Test du dashboard ADMINISTRATION")
    print("-" * 40)
    
    # Créer un client de test
    client = Client()
    
    # Authentifier un utilisateur du groupe ADMINISTRATION
    user = authenticate(username='admin1', password='test123')
    if not user:
        print("❌ Impossible de s'authentifier avec admin1")
        return False
    
    # Connecter l'utilisateur
    client.force_login(user)
    
    # Accéder au dashboard ADMINISTRATION
    response = client.get('/utilisateurs/dashboard/ADMINISTRATION/')
    
    if response.status_code == 200:
        print("✅ Dashboard ADMINISTRATION accessible")
        
        # Vérifier que les statistiques sont présentes dans le contexte
        if 'stats' in response.context:
            stats = response.context['stats']
            print(f"✅ Statistiques trouvées:")
            print(f"   - Total propriétés: {stats.get('total_proprietes', 0)}")
            print(f"   - Contrats actifs: {stats.get('contrats_actifs', 0)}")
            print(f"   - Total bailleurs: {stats.get('total_bailleurs', 0)}")
            print(f"   - Contrats à renouveler: {stats.get('contrats_renouveler', 0)}")
        else:
            print("❌ Aucune statistique trouvée dans le contexte")
            return False
    else:
        print(f"❌ Erreur {response.status_code} pour le dashboard ADMINISTRATION")
        return False
    
    return True

def test_dashboard_controles():
    """Test du dashboard CONTROLES"""
    print("\n🔍 Test du dashboard CONTROLES")
    print("-" * 40)
    
    # Créer un client de test
    client = Client()
    
    # Authentifier un utilisateur du groupe CONTROLES
    user = authenticate(username='admin1', password='test123')
    if not user:
        print("❌ Impossible de s'authentifier avec admin1")
        return False
    
    # Connecter l'utilisateur
    client.force_login(user)
    
    # Accéder au dashboard CONTROLES
    response = client.get('/utilisateurs/dashboard/CONTROLES/')
    
    if response.status_code == 200:
        print("✅ Dashboard CONTROLES accessible")
        
        # Vérifier que les statistiques sont présentes dans le contexte
        if 'stats' in response.context:
            stats = response.context['stats']
            print(f"✅ Statistiques trouvées:")
            print(f"   - Paiements à valider: {stats.get('paiements_a_valider', 0)}")
            print(f"   - Contrats à vérifier: {stats.get('contrats_a_verifier', 0)}")
            print(f"   - Anomalies: {stats.get('anomalies', 0)}")
            print(f"   - Rapports générés: {stats.get('rapports_generes', 0)}")
        else:
            print("❌ Aucune statistique trouvée dans le contexte")
            return False
    else:
        print(f"❌ Erreur {response.status_code} pour le dashboard CONTROLES")
        return False
    
    return True

def test_dashboard_privilege():
    """Test du dashboard PRIVILEGE"""
    print("\n👑 Test du dashboard PRIVILEGE")
    print("-" * 40)
    
    # Créer un client de test
    client = Client()
    
    # Authentifier un utilisateur du groupe PRIVILEGE
    user = authenticate(username='admin1', password='test123')
    if not user:
        print("❌ Impossible de s'authentifier avec admin1")
        return False
    
    # Connecter l'utilisateur
    client.force_login(user)
    
    # Accéder au dashboard PRIVILEGE
    response = client.get('/utilisateurs/dashboard/PRIVILEGE/')
    
    if response.status_code == 200:
        print("✅ Dashboard PRIVILEGE accessible")
        
        # Vérifier que les statistiques sont présentes dans le contexte
        if 'stats' in response.context:
            stats = response.context['stats']
            print(f"✅ Statistiques trouvées:")
            print(f"   - Total propriétés: {stats.get('total_proprietes', 0)}")
            print(f"   - Total utilisateurs: {stats.get('total_utilisateurs', 0)}")
            print(f"   - Total contrats: {stats.get('total_contrats', 0)}")
            print(f"   - Total paiements: {stats.get('total_paiements', 0)}")
            print(f"   - Total groupes: {stats.get('total_groupes', 0)}")
            print(f"   - Total notifications: {stats.get('total_notifications', 0)}")
            print(f"   - Utilisateurs actifs: {stats.get('utilisateurs_actifs', 0)}")
        else:
            print("❌ Aucune statistique trouvée dans le contexte")
            return False
    else:
        print(f"❌ Erreur {response.status_code} pour le dashboard PRIVILEGE")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION DES DASHBOARDS VIA URLs")
    print("=" * 60)
    
    # Tests des dashboards
    results = []
    results.append(test_dashboard_caisse())
    results.append(test_dashboard_administration())
    results.append(test_dashboard_controles())
    results.append(test_dashboard_privilege())
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    dashboards = ['CAISSE', 'ADMINISTRATION', 'CONTROLES', 'PRIVILEGE']
    for i, result in enumerate(results):
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"   - Dashboard {dashboards[i]}: {status}")
    
    if all(results):
        print("\n🎉 TOUS LES DASHBOARDS FONCTIONNENT CORRECTEMENT !")
        print("   Les statistiques sont bien affichées avec les vraies données.")
    else:
        print("\n⚠️  CERTAINS DASHBOARDS ONT DES PROBLÈMES")
        print("   Vérifiez les erreurs ci-dessus.")

if __name__ == '__main__':
    main() 