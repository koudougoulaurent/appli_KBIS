#!/usr/bin/env python
"""
Test complet des dashboards avec les bons utilisateurs
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

def test_dashboards_complet():
    """Test complet de tous les dashboards"""
    
    print("📊 TEST COMPLET DES DASHBOARDS")
    print("=" * 50)
    
    # Récupérer les vraies données de la base
    print("\n📈 DONNÉES RÉELLES DE LA BASE")
    print("-" * 30)
    
    # Données générales
    total_proprietes = Propriete.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_paiements = Paiement.objects.count()
    total_groupes = GroupeTravail.objects.count()
    total_notifications = Notification.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    
    print(f"🏠 Propriétés: {total_proprietes}")
    print(f"👥 Utilisateurs: {total_utilisateurs}")
    print(f"💰 Paiements: {total_paiements}")
    print(f"👨‍💼 Groupes: {total_groupes}")
    print(f"🔔 Notifications: {total_notifications}")
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
    
    print(f"\n💰 FINANCES (Mois {mois_courant}/{annee_courante})")
    print("-" * 30)
    print(f"💳 Paiements: {paiements_mois} XOF")
    print(f"💸 Retraits: {retraits_mois} XOF")
    print(f"🏦 Cautions: {cautions_cours} XOF")
    print(f"⏳ En attente: {paiements_attente}")
    
    # Données immobilières
    contrats_actifs = Contrat.objects.filter(est_actif=True).count()
    total_bailleurs = Bailleur.objects.count()
    contrats_renouveler = Contrat.objects.filter(
        date_fin__lte=datetime.now() + timedelta(days=30),
        est_actif=True
    ).count()
    
    print(f"\n🏠 IMMOBILIER")
    print("-" * 30)
    print(f"📋 Contrats actifs: {contrats_actifs}")
    print(f"👨‍💼 Bailleurs: {total_bailleurs}")
    print(f"🔄 À renouveler: {contrats_renouveler}")
    
    # Test des dashboards avec les bons utilisateurs
    print(f"\n🎯 TEST DES DASHBOARDS")
    print("-" * 30)
    
    # Créer ou récupérer des utilisateurs pour chaque groupe
    utilisateurs_groupes = create_test_users()
    
    for groupe_nom, username in utilisateurs_groupes.items():
        print(f"\n🔍 Test dashboard {groupe_nom}")
        print("-" * 25)
        
        # Connexion avec l'utilisateur du groupe
        user = authenticate(username=username, password='test123')
        if not user:
            print(f"❌ Échec connexion {username}")
            continue
        
        client = Client()
        client.force_login(user)
        
        # Test du dashboard
        url = f'/utilisateurs/dashboard/{groupe_nom}/'
        start_time = time.time()
        
        try:
            response = client.get(url)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Dashboard chargé en {load_time:.3f}s")
                
                # Vérifier les statistiques
                if hasattr(response, 'context') and response.context:
                    stats = response.context.get('stats', {})
                    print(f"📊 Statistiques: {len(stats)} éléments")
                    
                    # Vérifier selon le groupe
                    if groupe_nom == 'CAISSE':
                        verify_stats_caisse(stats, paiements_mois, retraits_mois, cautions_cours, paiements_attente)
                    elif groupe_nom == 'ADMINISTRATION':
                        verify_stats_admin(stats, total_proprietes, contrats_actifs, total_bailleurs, contrats_renouveler)
                    elif groupe_nom == 'CONTROLES':
                        verify_stats_controles(stats, paiements_attente, contrats_actifs)
                    elif groupe_nom == 'PRIVILEGE':
                        verify_stats_privilege(stats, total_proprietes, total_utilisateurs, total_paiements, total_groupes, total_notifications, utilisateurs_actifs)
                else:
                    print("⚠️ Pas de contexte dans la réponse")
            else:
                print(f"❌ Erreur {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    print(f"\n✅ Test complet terminé !")
    return True

def create_test_users():
    """Créer ou récupérer des utilisateurs de test pour chaque groupe"""
    utilisateurs = {}
    
    # Groupes à tester
    groupes = ['CAISSE', 'ADMINISTRATION', 'CONTROLES', 'PRIVILEGE']
    
    for groupe_nom in groupes:
        username = f"test_{groupe_nom.lower()}"
        
        # Récupérer ou créer l'utilisateur
        user, created = Utilisateur.objects.get_or_create(
            username=username,
            defaults={
                'first_name': f'Test {groupe_nom}',
                'last_name': 'Utilisateur',
                'email': f'{username}@test.com',
                'actif': True,
            }
        )
        
        # Récupérer le groupe
        try:
            groupe = GroupeTravail.objects.get(nom=groupe_nom)
            user.groupe_travail = groupe
            user.set_password('test123')
            user.save()
            
            if created:
                print(f"✅ Utilisateur {username} créé pour {groupe_nom}")
            else:
                print(f"✅ Utilisateur {username} récupéré pour {groupe_nom}")
                
            utilisateurs[groupe_nom] = username
            
        except GroupeTravail.DoesNotExist:
            print(f"❌ Groupe {groupe_nom} non trouvé")
    
    return utilisateurs

def verify_stats_caisse(stats, paiements_mois, retraits_mois, cautions_cours, paiements_attente):
    """Vérifier les statistiques CAISSE"""
    print("💰 Vérification CAISSE:")
    
    expected = {
        'paiements_mois': paiements_mois,
        'retraits_mois': retraits_mois,
        'cautions_cours': cautions_cours,
        'paiements_attente': paiements_attente,
    }
    
    for key, expected_value in expected.items():
        actual_value = stats.get(key, 0)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"  {status} {key}: {actual_value} (attendu: {expected_value})")

def verify_stats_admin(stats, total_proprietes, contrats_actifs, total_bailleurs, contrats_renouveler):
    """Vérifier les statistiques ADMINISTRATION"""
    print("🏠 Vérification ADMINISTRATION:")
    
    expected = {
        'total_proprietes': total_proprietes,
        'contrats_actifs': contrats_actifs,
        'total_bailleurs': total_bailleurs,
        'contrats_renouveler': contrats_renouveler,
    }
    
    for key, expected_value in expected.items():
        actual_value = stats.get(key, 0)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"  {status} {key}: {actual_value} (attendu: {expected_value})")

def verify_stats_controles(stats, paiements_attente, contrats_actifs):
    """Vérifier les statistiques CONTROLES"""
    print("🔍 Vérification CONTROLES:")
    
    expected = {
        'paiements_a_valider': paiements_attente,
        'contrats_a_verifier': contrats_actifs,
    }
    
    for key, expected_value in expected.items():
        actual_value = stats.get(key, 0)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"  {status} {key}: {actual_value} (attendu: {expected_value})")

def verify_stats_privilege(stats, total_proprietes, total_utilisateurs, total_paiements, total_groupes, total_notifications, utilisateurs_actifs):
    """Vérifier les statistiques PRIVILEGE"""
    print("👑 Vérification PRIVILEGE:")
    
    expected = {
        'total_proprietes': total_proprietes,
        'total_utilisateurs': total_utilisateurs,
        'total_paiements': total_paiements,
        'total_groupes': total_groupes,
        'total_notifications': total_notifications,
        'utilisateurs_actifs': utilisateurs_actifs,
    }
    
    for key, expected_value in expected.items():
        actual_value = stats.get(key, 0)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"  {status} {key}: {actual_value} (attendu: {expected_value})")

if __name__ == "__main__":
    test_dashboards_complet() 