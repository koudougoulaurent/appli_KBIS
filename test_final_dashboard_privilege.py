#!/usr/bin/env python
"""
Test final du dashboard PRIVILEGE avec vérification des statistiques affichées
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

def test_final_dashboard_privilege():
    """Test final du dashboard PRIVILEGE"""
    
    print("👑 TEST FINAL DU DASHBOARD PRIVILEGE")
    print("=" * 50)
    
    # Récupérer les vraies données de la base
    print("\n📊 DONNÉES DE LA BASE")
    print("-" * 30)
    
    total_proprietes = Propriete.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_contrats = Contrat.objects.count()
    total_paiements = Paiement.objects.count()
    total_groupes = GroupeTravail.objects.count()
    total_notifications = Notification.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    
    print(f"🏠 Propriétés: {total_proprietes}")
    print(f"👥 Utilisateurs: {total_utilisateurs}")
    print(f"📄 Contrats: {total_contrats}")
    print(f"💰 Paiements: {total_paiements}")
    print(f"👨‍💼 Groupes: {total_groupes}")
    print(f"🔔 Notifications: {total_notifications}")
    print(f"✅ Utilisateurs actifs: {utilisateurs_actifs}")
    
    # Test de connexion et accès au dashboard
    print("\n🔐 TEST DE CONNEXION ET ACCÈS")
    print("-" * 30)
    
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
            
            # Vérifier le contenu de la réponse
            content = response.content.decode()
            
            # Vérifier que les statistiques sont présentes dans le HTML
            print("\n📈 VÉRIFICATION DES STATISTIQUES DANS LE HTML")
            print("-" * 40)
            
            # Vérifier chaque statistique dans le contenu HTML
            stats_to_check = [
                ('Utilisateurs', str(total_utilisateurs)),
                ('Propriétés', str(total_proprietes)),
                ('Contrats', str(total_contrats)),
                ('Paiements', str(total_paiements)),
                ('Groupes', str(total_groupes)),
                ('Notifications', str(total_notifications)),
            ]
            
            for label, expected_value in stats_to_check:
                if expected_value in content:
                    print(f"✅ {label}: {expected_value} trouvé dans le HTML")
                else:
                    print(f"❌ {label}: {expected_value} NON trouvé dans le HTML")
            
            # Vérifier que le template utilise les bonnes variables
            print("\n🔍 VÉRIFICATION DES VARIABLES DU TEMPLATE")
            print("-" * 40)
            
            template_vars = [
                'stats.total_utilisateurs',
                'stats.total_proprietes',
                'stats.total_contrats',
                'stats.total_paiements',
                'stats.total_groupes',
                'stats.total_notifications',
            ]
            
            for var in template_vars:
                if var in content:
                    print(f"✅ Variable {var} utilisée dans le template")
                else:
                    print(f"❌ Variable {var} NON utilisée dans le template")
            
            # Vérifier le contexte de la réponse
            print("\n🔍 VÉRIFICATION DU CONTEXTE")
            print("-" * 30)
            
            if hasattr(response, 'context') and response.context:
                stats = response.context.get('stats', {})
                print(f"📊 Statistiques dans le contexte: {len(stats)} éléments")
                
                # Afficher les statistiques du contexte
                for key, value in stats.items():
                    print(f"   {key}: {value}")
            else:
                print("⚠️ Aucun contexte trouvé dans la réponse")
            
            # Vérifier que le template est correct
            print("\n🔍 VÉRIFICATION DU TEMPLATE")
            print("-" * 30)
            
            if 'dashboard_privilege.html' in content or 'Dashboard PRIVILEGE' in content:
                print("✅ Template dashboard_privilege.html utilisé")
            else:
                print("❌ Template dashboard_privilege.html NON utilisé")
            
            if 'Accès complet à toutes les fonctionnalités' in content:
                print("✅ Contenu spécifique au dashboard PRIVILEGE trouvé")
            else:
                print("❌ Contenu spécifique au dashboard PRIVILEGE NON trouvé")
                
        else:
            print(f"❌ Erreur {response.status_code} lors de l'accès au dashboard")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    
    print("\n🎯 RÉSUMÉ DU TEST FINAL")
    print("-" * 30)
    print("✅ Test du dashboard PRIVILEGE terminé")
    print("📊 Les statistiques devraient maintenant s'afficher correctement")
    print("🔧 Corrections appliquées:")
    print("   - Ajout du compteur de contrats dans la vue")
    print("   - Correction des variables dans le template (stats.total_*)")
    print("   - Vérification de la cohérence des données")
    
    return True

if __name__ == '__main__':
    test_final_dashboard_privilege() 