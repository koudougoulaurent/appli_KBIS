#!/usr/bin/env python
"""
Diagnostic complet des redirections persistantes
- Test de toutes les pages pour identifier celles qui redirigent encore
- Identification des mécanismes de protection restants
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import get_resolver

def diagnostic_redirections_persistantes():
    """Diagnostic complet des redirections persistantes"""
    
    print("🔍 DIAGNOSTIC COMPLET DES REDIRECTIONS PERSISTANTES")
    print("=" * 70)
    
    client = Client()
    
    # Étape 1: Identifier toutes les URLs de l'application paiements
    print("\n📋 Étape 1: Identification des URLs de l'application paiements")
    print("-" * 60)
    
    try:
        from paiements.urls import urlpatterns
        
        urls_a_tester = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                urls_a_tester.append((pattern.name, pattern.pattern))
        
        print(f"✅ URLs trouvées: {len(urls_a_tester)}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'identification des URLs: {e}")
        return False
    
    # Étape 2: Tester les URLs principales
    print("\n🧪 Étape 2: Test des URLs principales")
    print("-" * 60)
    
    urls_principales = [
        ('/paiements/', 'Page principale'),
        ('/paiements/retraits/', 'Liste des retraits'),
        ('/paiements/recaps-mensuels/', 'Recaps mensuels'),
        ('/paiements/recus/', 'Liste des reçus'),
        ('/paiements/charges-deductibles/', 'Charges déductibles'),
        ('/paiements/comptes/', 'Comptes bancaires'),
        ('/paiements/retraits-bailleur/', 'Retraits bailleur'),
    ]
    
    for url, description in urls_principales:
        try:
            response = client.get(url)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {description}: {url} - Status: {status}")
            elif status == 302:
                print(f"❌ {description}: {url} - Status: {status} -> Redirection vers: {response.url}")
            elif status == 403:
                print(f"🚫 {description}: {url} - Status: {status} (Forbidden)")
            elif status == 404:
                print(f"❓ {description}: {url} - Status: {status} (Not Found)")
            else:
                print(f"⚠️ {description}: {url} - Status: {status}")
                
        except Exception as e:
            print(f"❌ {description}: {url} - Erreur: {e}")
    
    # Étape 3: Vérifier les décorateurs restants
    print("\n🔍 Étape 3: Vérification des décorateurs restants")
    print("-" * 60)
    
    try:
        with open('paiements/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compter les décorateurs restants
        login_required_count = content.count('@login_required')
        user_passes_count = content.count('@user_passes_test')
        permission_required_count = content.count('@permission_required')
        groupe_required_count = content.count('@groupe_required')
        
        print(f"📊 Décorateurs restants:")
        print(f"   @login_required: {login_required_count}")
        print(f"   @user_passes_test: {user_passes_count}")
        print(f"   @permission_required: {permission_required_count}")
        print(f"   @groupe_required: {groupe_required_count}")
        
        if login_required_count == 0 and user_passes_count == 0:
            print("✅ Tous les décorateurs de sécurité ont été supprimés")
        else:
            print("⚠️ Il reste des décorateurs de sécurité")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    # Étape 4: Vérifier les mixins et classes de base
    print("\n🏗️ Étape 4: Vérification des mixins et classes de base")
    print("-" * 60)
    
    try:
        # Vérifier si les vues héritent de classes avec protection
        from paiements.views import RetraitListView, liste_recaps_mensuels
        
        print(f"✅ RetraitListView hérite de: {RetraitListView.__bases__}")
        
        # Vérifier les méthodes dispatch
        if hasattr(RetraitListView, 'dispatch'):
            print(f"✅ RetraitListView a une méthode dispatch")
        
        # Vérifier les attributs de classe
        if hasattr(RetraitListView, '_decorators'):
            print(f"⚠️ RetraitListView a des décorateurs: {RetraitListView._decorators}")
        else:
            print("✅ RetraitListView n'a pas de décorateurs")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des classes: {e}")
    
    # Étape 5: Vérifier les paramètres de sécurité Django
    print("\n⚙️ Étape 5: Vérification des paramètres Django")
    print("-" * 60)
    
    try:
        from django.conf import settings
        
        print(f"✅ LOGIN_URL: {getattr(settings, 'LOGIN_URL', 'Non défini')}")
        print(f"✅ LOGIN_REDIRECT_URL: {getattr(settings, 'LOGIN_REDIRECT_URL', 'Non défini')}")
        print(f"✅ LOGOUT_REDIRECT_URL: {getattr(settings, 'LOGOUT_REDIRECT_URL', 'Non défini')}")
        
        # Vérifier les middlewares
        middlewares = getattr(settings, 'MIDDLEWARE', [])
        auth_middlewares = [m for m in middlewares if 'auth' in m.lower()]
        print(f"✅ Middlewares d'authentification: {auth_middlewares}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des paramètres: {e}")
    
    print("\n✅ DIAGNOSTIC TERMINÉ !")
    print("🎯 Analysez les résultats pour identifier les redirections persistantes")
    
    return True

if __name__ == "__main__":
    diagnostic_redirections_persistantes()
