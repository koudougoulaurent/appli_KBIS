#!/usr/bin/env python
"""
Test des dashboards et vérification des vraies statistiques
"""

import os
import sys
import django
import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import Propriete, Bailleur
from contrats.models import Contrat
from paiements.models import Paiement, Retrait
from notifications.models import Notification
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q

def test_dashboards_statistiques():
    """Test de tous les dashboards et vérification des statistiques"""
    
    print("📊 TEST DES DASHBOARDS ET VÉRIFICATION DES STATISTIQUES")
    print("=" * 60)
    
    client = Client()
    
    # Connexion avec un utilisateur privilégié
    user = authenticate(username='privilege1', password='test123')
    if not user:
        print("❌ Échec de la connexion")
        return False
    
    client.force_login(user)
    print("✅ Connexion réussie")
    
    # Récupérer les vraies données de la base
    print("\n📈 RÉCUPÉRATION DES VRAIES DONNÉES DE LA BASE")
    print("-" * 40)
    
    # Données générales
    total_proprietes = Propriete.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_paiements = Paiement.objects.count()
    total_groupes = GroupeTravail.objects.count()
    total_notifications = Notification.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    
    print(f"🏠 Propriétés totales: {total_proprietes}")
    print(f"👥 Utilisateurs totaux: {total_utilisateurs}")
    print(f"💰 Paiements totaux: {total_paiements}")
    print(f"👨‍💼 Groupes totaux: {total_groupes}")
    print(f"🔔 Notifications totales: {total_notifications}")
    print(f"✅ Utilisateurs actifs: {utilisateurs_actifs}")
    
    # Données financières (mois courant)
    mois_courant = datetime.now().month
    annee_courante = datetime.now().year
    
    paiements_mois = Paiement.objects.filter(
        date_paiement__month=mois_courant,
        date_paiement__year=annee_courante
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    retraits_mois = Retrait.objects.filter(
        date_demande__month=mois_courant,
        date_demande__year=annee_courante
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    cautions_cours = Paiement.objects.filter(
        type_paiement='depot_garantie',
        statut='valide'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    paiements_attente = Paiement.objects.filter(statut='en_attente').count()
    
    print(f"\n💰 STATISTIQUES FINANCIÈRES (Mois {mois_courant}/{annee_courante})")
    print("-" * 40)
    print(f"💳 Paiements du mois: {paiements_mois} F CFA")
    print(f"💸 Retraits du mois: {retraits_mois} F CFA")
    print(f"🏦 Cautions en cours: {cautions_cours} F CFA")
    print(f"⏳ Paiements en attente: {paiements_attente}")
    
    # Données immobilières
    contrats_actifs = Contrat.objects.filter(est_actif=True).count()
    total_bailleurs = Bailleur.objects.count()
    contrats_renouveler = Contrat.objects.filter(
        date_fin__lte=datetime.now() + timedelta(days=30),
        est_actif=True
    ).count()
    
    print(f"\n🏠 STATISTIQUES IMMOBILIÈRES")
    print("-" * 40)
    print(f"📋 Contrats actifs: {contrats_actifs}")
    print(f"👨‍💼 Total bailleurs: {total_bailleurs}")
    print(f"🔄 Contrats à renouveler (30j): {contrats_renouveler}")
    
    # Test des dashboards
    print(f"\n🎯 TEST DES DASHBOARDS")
    print("-" * 40)
    
    dashboards_to_test = [
        ('CAISSE', '/utilisateurs/dashboard/CAISSE/'),
        ('ADMINISTRATION', '/utilisateurs/dashboard/ADMINISTRATION/'),
        ('CONTROLES', '/utilisateurs/dashboard/CONTROLES/'),
        ('PRIVILEGE', '/utilisateurs/dashboard/PRIVILEGE/'),
    ]
    
    for groupe_nom, url in dashboards_to_test:
        print(f"\n🔍 Test du dashboard {groupe_nom}")
        print("-" * 30)
        
        start_time = time.time()
        try:
            response = client.get(url)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Dashboard {groupe_nom} chargé en {load_time:.3f}s")
                
                # Vérifier les statistiques dans le contexte
                if hasattr(response, 'context') and response.context:
                    stats = response.context.get('stats', {})
                    print(f"📊 Statistiques trouvées: {len(stats)} éléments")
                    
                    # Vérifier les statistiques spécifiques selon le groupe
                    if groupe_nom == 'CAISSE':
                        verify_caisse_stats(stats, paiements_mois, retraits_mois, cautions_cours, paiements_attente)
                    elif groupe_nom == 'ADMINISTRATION':
                        verify_admin_stats(stats, total_proprietes, contrats_actifs, total_bailleurs, contrats_renouveler)
                    elif groupe_nom == 'CONTROLES':
                        verify_controles_stats(stats, paiements_attente, contrats_actifs)
                    elif groupe_nom == 'PRIVILEGE':
                        verify_privilege_stats(stats, total_proprietes, total_utilisateurs, total_paiements, total_groupes, total_notifications, utilisateurs_actifs)
                else:
                    print("⚠️ Aucun contexte trouvé dans la réponse")
            else:
                print(f"❌ Erreur dashboard {groupe_nom}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur accès dashboard {groupe_nom}: {e}")
    
    print(f"\n✅ Test des dashboards terminé !")
    return True

def verify_caisse_stats(stats, paiements_mois, retraits_mois, cautions_cours, paiements_attente):
    """Vérifier les statistiques du dashboard CAISSE"""
    print("💰 Vérification statistiques CAISSE:")
    
    expected_stats = {
        'paiements_mois': paiements_mois,
        'retraits_mois': retraits_mois,
        'cautions_cours': cautions_cours,
        'paiements_attente': paiements_attente,
    }
    
    for key, expected_value in expected_stats.items():
        actual_value = stats.get(key, 0)
        if actual_value == expected_value:
            print(f"  ✅ {key}: {actual_value} (correct)")
        else:
            print(f"  ❌ {key}: {actual_value} (attendu: {expected_value})")

def verify_admin_stats(stats, total_proprietes, contrats_actifs, total_bailleurs, contrats_renouveler):
    """Vérifier les statistiques du dashboard ADMINISTRATION"""
    print("🏠 Vérification statistiques ADMINISTRATION:")
    
    expected_stats = {
        'total_proprietes': total_proprietes,
        'contrats_actifs': contrats_actifs,
        'total_bailleurs': total_bailleurs,
        'contrats_renouveler': contrats_renouveler,
    }
    
    for key, expected_value in expected_stats.items():
        actual_value = stats.get(key, 0)
        if actual_value == expected_value:
            print(f"  ✅ {key}: {actual_value} (correct)")
        else:
            print(f"  ❌ {key}: {actual_value} (attendu: {expected_value})")

def verify_controles_stats(stats, paiements_attente, contrats_actifs):
    """Vérifier les statistiques du dashboard CONTROLES"""
    print("🔍 Vérification statistiques CONTROLES:")
    
    expected_stats = {
        'paiements_a_valider': paiements_attente,
        'contrats_a_verifier': contrats_actifs,
    }
    
    for key, expected_value in expected_stats.items():
        actual_value = stats.get(key, 0)
        if actual_value == expected_value:
            print(f"  ✅ {key}: {actual_value} (correct)")
        else:
            print(f"  ❌ {key}: {actual_value} (attendu: {expected_value})")

def verify_privilege_stats(stats, total_proprietes, total_utilisateurs, total_paiements, total_groupes, total_notifications, utilisateurs_actifs):
    """Vérifier les statistiques du dashboard PRIVILEGE"""
    print("👑 Vérification statistiques PRIVILEGE:")
    
    expected_stats = {
        'total_proprietes': total_proprietes,
        'total_utilisateurs': total_utilisateurs,
        'total_paiements': total_paiements,
        'total_groupes': total_groupes,
        'total_notifications': total_notifications,
        'utilisateurs_actifs': utilisateurs_actifs,
    }
    
    for key, expected_value in expected_stats.items():
        actual_value = stats.get(key, 0)
        if actual_value == expected_value:
            print(f"  ✅ {key}: {actual_value} (correct)")
        else:
            print(f"  ❌ {key}: {actual_value} (attendu: {expected_value})")

if __name__ == "__main__":
    test_dashboards_statistiques() 