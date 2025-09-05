#!/usr/bin/env python
"""
Diagnostic complet de tous les boutons d'actions rapides
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model

def test_quick_action_urls():
    """Teste toutes les URLs des actions rapides"""
    print("🔍 Test des URLs des Actions Rapides")
    print("=" * 60)
    
    # URLs des actions rapides identifiées dans les templates
    quick_action_urls = [
        # Core
        ('core:intelligent_search', [], 'Recherche Intelligente'),
        ('core:configuration_entreprise', [], 'Configuration'),
        ('core:dashboard', [], 'Dashboard Principal'),
        
        # Propriétés
        ('proprietes:ajouter', [], 'Ajouter Propriété'),
        ('proprietes:liste', [], 'Liste Propriétés'),
        ('proprietes:bailleurs_liste', [], 'Liste Bailleurs'),
        ('proprietes:locataires_liste', [], 'Liste Locataires'),
        ('proprietes:liste_charges_bailleur', [], 'Charges Bailleur'),
        ('proprietes:dashboard', [], 'Dashboard Propriétés'),
        
        # Paiements
        ('paiements:ajouter', [], 'Ajouter Paiement'),
        ('paiements:liste', [], 'Liste Paiements'),
        ('paiements:dashboard', [], 'Dashboard Paiements'),
        ('paiements:liste_recaps_mensuels', [], 'Récaps Mensuels'),
        ('paiements:retraits_liste', [], 'Liste Retraits'),
        ('paiements:retrait_ajouter', [], 'Ajouter Retrait'),
        
        # Contrats
        ('contrats:dashboard', [], 'Dashboard Contrats'),
        ('contrats:liste', [], 'Liste Contrats'),
        ('contrats:ajouter', [], 'Ajouter Contrat'),
        
        # Utilisateurs
        ('utilisateurs:dashboard_groupe', ['PRIVILEGE'], 'Dashboard Groupe'),
        ('utilisateurs:profile', [], 'Profil Utilisateur'),
        
        # Notifications
        ('notifications:notification_list', [], 'Liste Notifications'),
    ]
    
    working_urls = []
    broken_urls = []
    
    for url_name, args, description in quick_action_urls:
        try:
            url = reverse(url_name, args=args)
            working_urls.append((url_name, url, description))
            print(f"✅ {description}: {url}")
        except NoReverseMatch as e:
            broken_urls.append((url_name, args, description, str(e)))
            print(f"❌ {description}: ERREUR - {e}")
        except Exception as e:
            broken_urls.append((url_name, args, description, str(e)))
            print(f"❌ {description}: ERREUR GÉNÉRALE - {e}")
    
    print(f"\n📊 Résumé:")
    print(f"✅ URLs fonctionnelles: {len(working_urls)}")
    print(f"❌ URLs cassées: {len(broken_urls)}")
    
    return working_urls, broken_urls

def test_quick_action_views():
    """Teste l'accès aux vues des actions rapides"""
    print("\n🎨 Test d'Accès aux Vues")
    print("=" * 60)
    
    User = get_user_model()
    client = Client()
    
    # Récupérer un utilisateur privilégié
    user = User.objects.filter(username='privilege1').first()
    if not user:
        print("⚠️ Aucun utilisateur privilégié trouvé")
        return
    
    client.force_login(user)
    
    # URLs à tester avec client HTTP
    test_urls = [
        ('/proprietes/', 'Dashboard Propriétés'),
        ('/paiements/', 'Dashboard Paiements'),
        ('/contrats/', 'Dashboard Contrats'),
        ('/utilisateurs/dashboard/PRIVILEGE/', 'Dashboard Groupe'),
        ('/proprietes/liste/', 'Liste Propriétés'),
        ('/paiements/liste/', 'Liste Paiements'),
        ('/notifications/', 'Notifications'),
    ]
    
    working_views = []
    broken_views = []
    
    for url, description in test_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                working_views.append((url, description))
                print(f"✅ {description}: Status 200")
            elif response.status_code == 302:
                print(f"🔄 {description}: Redirection (Status 302)")
                working_views.append((url, description))
            else:
                broken_views.append((url, description, response.status_code))
                print(f"❌ {description}: Status {response.status_code}")
        except Exception as e:
            broken_views.append((url, description, str(e)))
            print(f"❌ {description}: ERREUR - {e}")
    
    print(f"\n📊 Résumé:")
    print(f"✅ Vues fonctionnelles: {len(working_views)}")
    print(f"❌ Vues cassées: {len(broken_views)}")
    
    return working_views, broken_views

def generate_fixes_for_broken_urls(broken_urls):
    """Génère les corrections pour les URLs cassées"""
    print("\n🔧 Corrections Suggérées pour URLs Cassées")
    print("=" * 60)
    
    if not broken_urls:
        print("✅ Aucune URL cassée à corriger !")
        return
    
    fixes = []
    
    for url_name, args, description, error in broken_urls:
        print(f"\n❌ {description} ({url_name}):")
        print(f"   Erreur: {error}")
        
        # Suggestions de correction
        if 'not found' in error.lower():
            # Chercher des URLs similaires
            app_name = url_name.split(':')[0] if ':' in url_name else ''
            view_name = url_name.split(':')[1] if ':' in url_name else url_name
            
            print(f"   💡 Suggestions:")
            print(f"   - Vérifier que l'URL existe dans {app_name}/urls.py")
            print(f"   - Chercher des URLs similaires à '{view_name}'")
            
            # Corrections communes
            common_fixes = {
                'intelligent_search': 'recherche_intelligente',
                'detail_retrait': 'retrait_detail',
                'modifier_retrait': 'retrait_modifier',
                'ajouter_retrait': 'retrait_ajouter',
            }
            
            if view_name in common_fixes:
                suggested_url = f"{app_name}:{common_fixes[view_name]}"
                print(f"   ✅ Correction suggérée: {url_name} → {suggested_url}")
                fixes.append((url_name, suggested_url, description))
        
        elif 'arguments' in error.lower():
            print(f"   💡 Vérifier les arguments requis pour cette URL")
    
    return fixes

def create_comprehensive_quick_actions():
    """Crée un fichier avec toutes les actions rapides fonctionnelles"""
    print("\n📝 Création du Guide des Actions Rapides")
    print("=" * 60)
    
    working_urls, broken_urls = test_quick_action_urls()
    working_views, broken_views = test_quick_action_views()
    
    # Créer le contenu du guide
    guide_content = f"""# 🚀 Guide Complet des Actions Rapides

## ✅ URLs Fonctionnelles ({len(working_urls)})

"""
    
    for url_name, url, description in working_urls:
        guide_content += f"- **{description}** : `{url_name}` → `{url}`\n"
    
    if broken_urls:
        guide_content += f"\n## ❌ URLs à Corriger ({len(broken_urls)})\n\n"
        for url_name, args, description, error in broken_urls:
            guide_content += f"- **{description}** : `{url_name}` - {error}\n"
    
    guide_content += f"\n## 🎯 Vues Testées\n\n"
    guide_content += f"✅ Vues fonctionnelles: {len(working_views)}\n"
    guide_content += f"❌ Vues avec problèmes: {len(broken_views)}\n"
    
    # Sauvegarder le guide
    with open('GUIDE_ACTIONS_RAPIDES_DIAGNOSTIC.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Guide créé: GUIDE_ACTIONS_RAPIDES_DIAGNOSTIC.md")
    
    return guide_content

def main():
    """Fonction principale"""
    print("🚀 Diagnostic Complet des Actions Rapides")
    print("=" * 80)
    
    # Test des URLs
    working_urls, broken_urls = test_quick_action_urls()
    
    # Test des vues
    working_views, broken_views = test_quick_action_views()
    
    # Générer les corrections
    fixes = generate_fixes_for_broken_urls(broken_urls)
    
    # Créer le guide
    guide = create_comprehensive_quick_actions()
    
    print("\n🎉 Diagnostic Terminé!")
    print("=" * 80)
    print(f"📊 Résumé Global:")
    print(f"   ✅ URLs fonctionnelles: {len(working_urls)}")
    print(f"   ❌ URLs à corriger: {len(broken_urls)}")
    print(f"   ✅ Vues accessibles: {len(working_views)}")
    print(f"   ❌ Vues avec problèmes: {len(broken_views)}")
    
    if broken_urls:
        print(f"\n🔧 Actions Recommandées:")
        print("   1. Corriger les URLs cassées identifiées")
        print("   2. Tester à nouveau après corrections")
        print("   3. Vérifier les permissions utilisateur")
    else:
        print(f"\n🎉 Toutes les actions rapides sont fonctionnelles !")

if __name__ == "__main__":
    main()
