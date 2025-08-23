#!/usr/bin/env python
"""
Script de test pour vérifier que toutes les pages des bailleurs fonctionnent
"""

import os
import requests
from urllib.parse import urljoin

def test_bailleur_pages():
    """Teste toutes les pages des bailleurs"""
    
    print("🧪 Test des pages des bailleurs")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # URLs à tester
    urls_to_test = [
        {
            'url': '/proprietes/bailleurs/',
            'name': 'Liste des Bailleurs',
            'expected_status': 200
        },
        {
            'url': '/proprietes/bailleurs/ajouter/',
            'name': 'Ajouter un Bailleur',
            'expected_status': 200
        }
    ]
    
    success_count = 0
    total_count = len(urls_to_test)
    
    for test in urls_to_test:
        try:
            print(f"🔍 Test de {test['name']}...")
            print(f"   URL: {test['url']}")
            
            response = requests.get(urljoin(base_url, test['url']), timeout=10)
            
            if response.status_code == test['expected_status']:
                print(f"   ✅ Succès - Status: {response.status_code}")
                success_count += 1
            else:
                print(f"   ❌ Échec - Status: {response.status_code} (attendu: {test['expected_status']})")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Erreur de connexion - Le serveur Django n'est pas démarré")
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout - La page met trop de temps à répondre")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    print("=" * 50)
    print(f"📊 Résultat: {success_count}/{total_count} pages fonctionnent")
    
    if success_count == total_count:
        print("🎉 Toutes les pages des bailleurs fonctionnent correctement !")
    else:
        print("⚠️ Certaines pages ont des problèmes.")
    
    return success_count == total_count

def check_templates():
    """Vérifie que tous les templates nécessaires existent"""
    
    print("\n📁 Vérification des templates")
    print("=" * 30)
    
    templates_dir = "templates/proprietes"
    required_templates = [
        'bailleur_ajouter.html',
        'bailleur_detail.html', 
        'bailleur_modifier.html',
        'bailleurs_liste.html'
    ]
    
    missing_templates = []
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if os.path.exists(template_path):
            print(f"✅ {template}")
        else:
            print(f"❌ {template} - MANQUANT")
            missing_templates.append(template)
    
    if missing_templates:
        print(f"\n⚠️ Templates manquants: {', '.join(missing_templates)}")
        return False
    else:
        print("\n🎉 Tous les templates sont présents !")
        return True

def check_urls():
    """Vérifie que toutes les URLs sont configurées"""
    
    print("\n🔗 Vérification des URLs")
    print("=" * 30)
    
    # Vérifier le fichier urls.py des propriétés
    urls_file = "proprietes/urls.py"
    
    if os.path.exists(urls_file):
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_urls = [
            'bailleurs_liste',
            'bailleur_detail', 
            'bailleur_ajouter',
            'bailleur_modifier'
        ]
        
        missing_urls = []
        
        for url_name in required_urls:
            if url_name in content:
                print(f"✅ {url_name}")
            else:
                print(f"❌ {url_name} - MANQUANT")
                missing_urls.append(url_name)
        
        if missing_urls:
            print(f"\n⚠️ URLs manquantes: {', '.join(missing_urls)}")
            return False
        else:
            print("\n🎉 Toutes les URLs sont configurées !")
            return True
    else:
        print("❌ Fichier urls.py non trouvé")
        return False

def check_views():
    """Vérifie que toutes les vues sont définies"""
    
    print("\n👁️ Vérification des vues")
    print("=" * 30)
    
    views_file = "proprietes/views.py"
    
    if os.path.exists(views_file):
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_views = [
            'liste_bailleurs',
            'detail_bailleur',
            'ajouter_bailleur', 
            'modifier_bailleur'
        ]
        
        missing_views = []
        
        for view_name in required_views:
            if f'def {view_name}' in content:
                print(f"✅ {view_name}")
            else:
                print(f"❌ {view_name} - MANQUANT")
                missing_views.append(view_name)
        
        if missing_views:
            print(f"\n⚠️ Vues manquantes: {', '.join(missing_views)}")
            return False
        else:
            print("\n🎉 Toutes les vues sont définies !")
            return True
    else:
        print("❌ Fichier views.py non trouvé")
        return False

def main():
    """Fonction principale"""
    
    print("🚀 Test complet des pages des bailleurs")
    print("=" * 60)
    
    # Vérifications statiques
    templates_ok = check_templates()
    urls_ok = check_urls()
    views_ok = check_views()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES VÉRIFICATIONS")
    print("=" * 60)
    print(f"📁 Templates: {'✅ OK' if templates_ok else '❌ PROBLÈME'}")
    print(f"🔗 URLs: {'✅ OK' if urls_ok else '❌ PROBLÈME'}")
    print(f"👁️ Vues: {'✅ OK' if views_ok else '❌ PROBLÈME'}")
    
    if templates_ok and urls_ok and views_ok:
        print("\n🎉 Toutes les vérifications statiques sont OK !")
        print("💡 Pour tester les pages en action, démarrez le serveur Django:")
        print("   python manage.py runserver")
        print("   Puis visitez: http://127.0.0.1:8000/proprietes/bailleurs/")
    else:
        print("\n⚠️ Des problèmes ont été détectés.")
        print("🔧 Corrigez les problèmes avant de tester les pages.")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main() 