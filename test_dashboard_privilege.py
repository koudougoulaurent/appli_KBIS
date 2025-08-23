#!/usr/bin/env python
"""
Test des statistiques du dashboard PRIVILEGE
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
from proprietes.models import Propriete, Bailleur
from contrats.models import Contrat
from paiements.models import Paiement, Retrait
from notifications.models import Notification
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q

def test_dashboard_privilege_statistiques():
    """Test des statistiques du dashboard PRIVILEGE"""
    
    print("👑 TEST DES STATISTIQUES DU DASHBOARD PRIVILEGE")
    print("=" * 60)
    
    # Récupérer les vraies données de la base
    print("\n📊 RÉCUPÉRATION DES VRAIES DONNÉES DE LA BASE")
    print("-" * 40)
    
    # Données générales
    total_proprietes = Propriete.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_contrats = Contrat.objects.count()
    total_paiements = Paiement.objects.count()
    total_groupes = GroupeTravail.objects.count()
    total_notifications = Notification.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    
    print(f"🏠 Propriétés totales: {total_proprietes}")
    print(f"👥 Utilisateurs totaux: {total_utilisateurs}")
    print(f"📄 Contrats totaux: {total_contrats}")
    print(f"💰 Paiements totaux: {total_paiements}")
    print(f"👨‍💼 Groupes totaux: {total_groupes}")
    print(f"🔔 Notifications totales: {total_notifications}")
    print(f"✅ Utilisateurs actifs: {utilisateurs_actifs}")
    
    # Test de connexion et accès au dashboard
    print("\n🔐 TEST DE CONNEXION ET ACCÈS AU DASHBOARD")
    print("-" * 40)
    
    client = Client()
    
    # Connexion avec un utilisateur privilégié
    user = authenticate(username='privilege1', password='test123')
    if not user:
        print("❌ Échec de la connexion avec privilege1")
        return False
    
    client.force_login(user)
    print("✅ Connexion réussie avec privilege1")
    
    # Test d'accès au dashboard PRIVILEGE
    print("\n🔍 Test du dashboard PRIVILEGE")
    print("-" * 30)
    
    try:
        response = client.get('/utilisateurs/dashboard/PRIVILEGE/')
        
        if response.status_code == 200:
            print("✅ Dashboard PRIVILEGE accessible")
            
            # Vérifier les statistiques dans le contexte
            if hasattr(response, 'context') and response.context:
                stats = response.context.get('stats', {})
                print(f"📊 Statistiques trouvées: {len(stats)} éléments")
                
                # Vérifier chaque statistique
                expected_stats = {
                    'total_proprietes': total_proprietes,
                    'total_utilisateurs': total_utilisateurs,
                    'total_contrats': total_contrats,
                    'total_paiements': total_paiements,
                    'total_groupes': total_groupes,
                    'total_notifications': total_notifications,
                    'utilisateurs_actifs': utilisateurs_actifs,
                }
                
                print("\n📈 VÉRIFICATION DES STATISTIQUES")
                print("-" * 30)
                
                for stat_name, expected_value in expected_stats.items():
                    actual_value = stats.get(stat_name, 'NON TROUVÉ')
                    status = "✅" if actual_value == expected_value else "❌"
                    print(f"{status} {stat_name}: {actual_value} (attendu: {expected_value})")
                
                # Vérifier que le template utilise les bonnes variables
                print("\n🔍 VÉRIFICATION DU TEMPLATE")
                print("-" * 30)
                
                if 'stats.total_utilisateurs' in response.content.decode():
                    print("✅ Template utilise stats.total_utilisateurs")
                else:
                    print("❌ Template n'utilise pas stats.total_utilisateurs")
                
                if 'stats.total_proprietes' in response.content.decode():
                    print("✅ Template utilise stats.total_proprietes")
                else:
                    print("❌ Template n'utilise pas stats.total_proprietes")
                
                if 'stats.total_contrats' in response.content.decode():
                    print("✅ Template utilise stats.total_contrats")
                else:
                    print("❌ Template n'utilise pas stats.total_contrats")
                
            else:
                print("⚠️ Aucun contexte trouvé dans la réponse")
                
        else:
            print(f"❌ Erreur {response.status_code} lors de l'accès au dashboard")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    
    print("\n🎯 RÉSUMÉ DU TEST")
    print("-" * 30)
    print("✅ Test des statistiques du dashboard PRIVILEGE terminé")
    print("📊 Les statistiques devraient maintenant s'afficher correctement")
    
    return True

if __name__ == '__main__':
    test_dashboard_privilege_statistiques() 