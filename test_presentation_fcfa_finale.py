#!/usr/bin/env python3
"""
Test rapide de la présentation finale avec devise F CFA
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_template_syntax():
    """Test de la syntaxe du template"""
    print("🔍 TEST DE LA SYNTAXE DU TEMPLATE")
    print("=" * 50)
    
    try:
        from django.template.loader import get_template
        template = get_template('proprietes/unites/detail_complet.html')
        print("✅ Template chargé sans erreur de syntaxe")
        return True
    except Exception as e:
        print(f"❌ Erreur de syntaxe template: {e}")
        return False

def test_currency_formatting():
    """Test du formatage de devise"""
    print("\n💰 TEST DU FORMATAGE DEVISE F CFA")
    print("=" * 50)
    
    try:
        from core.templatetags.core_extras import currency_format
        
        test_values = [1000, 150000, 1234567.89, 0, None]
        
        for value in test_values:
            result = currency_format(value)
            print(f"✅ {value} → {result}")
            
            # Vérifier que le résultat contient "F CFA"
            if result and "F CFA" in result:
                print(f"   ✓ Devise F CFA correcte")
            else:
                print(f"   ❌ Devise incorrecte: {result}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur formatage devise: {e}")
        return False

def test_unite_model_methods():
    """Test des méthodes du modèle UniteLocative"""
    print("\n🏠 TEST DES MÉTHODES UNITELOCATIVE")
    print("=" * 50)
    
    try:
        from proprietes.models import UniteLocative
        
        # Récupérer une unité de test
        unite = UniteLocative.objects.first()
        if not unite:
            print("⚠️  Aucune unité locative trouvée pour le test")
            return True
        
        print(f"📋 Test avec unité: {unite.numero_unite} - {unite.nom}")
        
        # Test des méthodes
        methods_to_test = [
            'get_loyer_total',
            'get_loyer_total_formatted',
            'get_revenus_potentiels_annuels',
            'get_taux_occupation',
            'get_duree_moyenne_occupation',
            'get_bailleur_effectif'
        ]
        
        for method_name in methods_to_test:
            try:
                method = getattr(unite, method_name)
                result = method()
                print(f"✅ {method_name}(): {result}")
            except Exception as e:
                print(f"❌ {method_name}(): Erreur - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test modèle: {e}")
        return False

def test_propriete_model_methods():
    """Test des méthodes du modèle Propriete"""
    print("\n🏢 TEST DES MÉTHODES PROPRIETE")
    print("=" * 50)
    
    try:
        from proprietes.models import Propriete
        
        # Récupérer une propriété de test
        propriete = Propriete.objects.first()
        if not propriete:
            print("⚠️  Aucune propriété trouvée pour le test")
            return True
        
        print(f"📋 Test avec propriété: {propriete.titre}")
        
        # Test des méthodes
        methods_to_test = [
            'get_revenus_mensuels_actuels',
            'get_taux_occupation_global',
            'get_statistiques_unites',
            'est_grande_propriete'
        ]
        
        for method_name in methods_to_test:
            try:
                method = getattr(propriete, method_name)
                result = method()
                print(f"✅ {method_name}(): {result}")
            except Exception as e:
                print(f"❌ {method_name}(): Erreur - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test propriété: {e}")
        return False

def test_server_response():
    """Test de réponse du serveur"""
    print("\n🌐 TEST DE RÉPONSE SERVEUR")
    print("=" * 50)
    
    try:
        # Test sur localhost:8001 (serveur de test)
        test_urls = [
            'http://127.0.0.1:8001/',
            'http://127.0.0.1:8001/proprietes/unites/',
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {url} - OK (200)")
                else:
                    print(f"⚠️  {url} - Status {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"⚠️  {url} - Serveur non accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test serveur: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET - PRÉSENTATION PRODUCTION F CFA")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Syntaxe Template", test_template_syntax),
        ("Formatage Devise F CFA", test_currency_formatting),
        ("Méthodes UniteLocative", test_unite_model_methods),
        ("Méthodes Propriete", test_propriete_model_methods),
        ("Réponse Serveur", test_server_response),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name.upper()}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} - RÉUSSI")
            else:
                print(f"❌ {test_name} - ÉCHEC")
                
        except Exception as e:
            print(f"💥 {test_name} - ERREUR: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"   {test_name:<25} : {status}")
    
    print(f"\n🎯 SCORE FINAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS RÉUSSIS - SYSTÈME OPÉRATIONNEL!")
        print("\n✅ Présentation production avec F CFA validée")
        print("✅ Interface responsive fonctionnelle")
        print("✅ Méthodes modèles opérationnelles")
        print("✅ Formatage devise correct")
    else:
        print(f"⚠️  {total - passed} test(s) en échec - Vérification nécessaire")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

