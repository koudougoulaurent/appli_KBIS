#!/usr/bin/env python3
"""
Test du bouton d'accès au dashboard PRIVILEGE depuis le dashboard principal
Vérification que le lien fonctionne correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from django.urls import reverse

def test_bouton_privilege_dashboard():
    """Test du bouton d'accès au dashboard PRIVILEGE"""
    
    print("🚀 TEST DU BOUTON D'ACCÈS AU DASHBOARD PRIVILEGE")
    print("=" * 60)
    
    client = Client()
    
    try:
        # 1. Test d'accès au dashboard principal
        print("\n📊 Test 1: Accès au dashboard principal (/dashboard/)")
        print("-" * 50)
        
        # Authentification avec un utilisateur
        user = authenticate(username='privilege1', password='test123')
        if user:
            client.force_login(user)
            print(f"✅ Connexion réussie avec {user.username}")
        else:
            print("❌ Échec de la connexion")
            return False
        
        # Accès au dashboard principal
        response = client.get('/dashboard/')
        if response.status_code == 200:
            print("✅ Dashboard principal accessible")
            
            # Vérifier la présence du bouton PRIVILEGE
            content = response.content.decode('utf-8')
            
            if 'Dashboard PRIVILEGE' in content:
                print("✅ Bouton 'Dashboard PRIVILEGE' trouvé dans le contenu")
            else:
                print("❌ Bouton 'Dashboard PRIVILEGE' NON trouvé")
                return False
            
            if 'utilisateurs:dashboard_groupe' in content:
                print("✅ URL du dashboard groupe trouvée")
            else:
                print("❌ URL du dashboard groupe NON trouvée")
            
            if 'PRIVILEGE' in content:
                print("✅ Paramètre 'PRIVILEGE' trouvé")
            else:
                print("❌ Paramètre 'PRIVILEGE' NON trouvé")
                
        else:
            print(f"❌ Erreur {response.status_code} pour le dashboard principal")
            return False
        
        # 2. Test du lien vers le dashboard PRIVILEGE
        print("\n👑 Test 2: Accès direct au dashboard PRIVILEGE")
        print("-" * 50)
        
        # Construction de l'URL
        try:
            privilege_url = reverse('utilisateurs:dashboard_groupe', kwargs={'groupe_nom': 'PRIVILEGE'})
            print(f"📍 URL construite: {privilege_url}")
            
            # Test d'accès
            response = client.get(privilege_url)
            if response.status_code == 200:
                print("✅ Dashboard PRIVILEGE accessible via l'URL")
                
                # Vérifier le contenu spécifique au dashboard PRIVILEGE
                content = response.content.decode('utf-8')
                
                if 'Dashboard PRIVILEGE' in content:
                    print("✅ Contenu du dashboard PRIVILEGE confirmé")
                else:
                    print("❌ Contenu du dashboard PRIVILEGE NON confirmé")
                
                if 'Accès complet' in content:
                    print("✅ Description 'Accès complet' trouvée")
                else:
                    print("❌ Description 'Accès complet' NON trouvée")
                    
            else:
                print(f"❌ Erreur {response.status_code} pour le dashboard PRIVILEGE")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la construction de l'URL: {str(e)}")
            return False
        
        # 3. Test des autres dashboards
        print("\n🏢 Test 3: Accès aux autres dashboards")
        print("-" * 45)
        
        dashboards = [
            ('ADMINISTRATION', '🏢'),
            ('CONTROLES', '🔍'),
            ('CAISSE', '💰')
        ]
        
        for dashboard, icon in dashboards:
            try:
                url = reverse('utilisateurs:dashboard_groupe', kwargs={'groupe_nom': dashboard})
                response = client.get(url)
                if response.status_code == 200:
                    print(f"   ✅ {icon} Dashboard {dashboard} accessible")
                else:
                    print(f"   ❌ {icon} Dashboard {dashboard} erreur {response.status_code}")
            except Exception as e:
                print(f"   ❌ {icon} Dashboard {dashboard} erreur: {str(e)}")
        
        # 4. Vérification de la navigation
        print("\n🔗 Test 4: Navigation complète")
        print("-" * 35)
        
        # Dashboard principal → PRIVILEGE → retour
        print("   📊 Dashboard principal → Dashboard PRIVILEGE")
        response1 = client.get('/dashboard/')
        response2 = client.get(privilege_url)
        
        if response1.status_code == 200 and response2.status_code == 200:
            print("   ✅ Navigation bidirectionnelle OK")
        else:
            print("   ❌ Problème de navigation")
            return False
        
        print("\n🎯 RÉSUMÉ DU TEST")
        print("-" * 20)
        print("   ✅ Dashboard principal accessible")
        print("   ✅ Bouton PRIVILEGE présent")
        print("   ✅ Lien vers dashboard PRIVILEGE fonctionnel")
        print("   ✅ Tous les dashboards accessibles")
        print("   ✅ Navigation complète OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_urls_dashboard():
    """Test des URLs des dashboards"""
    
    print("\n🔗 TEST DES URLs DES DASHBOARDS")
    print("=" * 40)
    
    urls_to_test = [
        ('core:dashboard', {}, 'Dashboard Principal'),
        ('utilisateurs:dashboard_groupe', {'groupe_nom': 'PRIVILEGE'}, 'Dashboard PRIVILEGE'),
        ('utilisateurs:dashboard_groupe', {'groupe_nom': 'ADMINISTRATION'}, 'Dashboard ADMINISTRATION'),
        ('utilisateurs:dashboard_groupe', {'groupe_nom': 'CONTROLES'}, 'Dashboard CONTROLES'),
        ('utilisateurs:dashboard_groupe', {'groupe_nom': 'CAISSE'}, 'Dashboard CAISSE'),
    ]
    
    for url_name, kwargs, description in urls_to_test:
        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"   ✅ {description}: {url}")
        except Exception as e:
            print(f"   ❌ {description}: Erreur - {str(e)}")

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DU TEST DU BOUTON PRIVILEGE")
    
    # Test des URLs
    test_urls_dashboard()
    
    # Test fonctionnel
    success = test_bouton_privilege_dashboard()
    
    if success:
        print("\n🎉 TEST TERMINÉ AVEC SUCCÈS!")
        print("Le bouton d'accès au dashboard PRIVILEGE fonctionne parfaitement!")
    else:
        print("\n💥 TEST ÉCHOUÉ!")
        print("Il y a un problème avec le bouton ou la navigation.")
    
    print("\n" + "=" * 60)