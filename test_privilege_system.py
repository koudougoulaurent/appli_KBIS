#!/usr/bin/env python3
"""
Script de test pour vérifier le bon fonctionnement du système de privilège.
Ce script teste l'importation des modules et la création des vues.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetImo.settings')
django.setup()

def test_imports():
    """Teste l'importation des modules de privilège."""
    try:
        from utilisateurs.mixins import PrivilegeButtonsMixin, PrivilegeDeleteMixin, PrivilegeRequiredMixin
        print("✅ Import des mixins réussi")
        
        from utilisateurs.views import PrivilegeActionView, PrivilegeDeleteView, PrivilegeDisableView
        print("✅ Import des vues de privilège réussi")
        
        from utilisateurs.views import UtilisateurListView
        print("✅ Import de la vue UtilisateurListView réussi")
        
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_mixin_inheritance():
    """Teste que les vues héritent bien du mixin de privilège."""
    try:
        from utilisateurs.views import UtilisateurListView
        from proprietes.views import ProprieteListView, BailleurListView, LocataireListView
        from paiements.views import PaiementListView, RecuListView
        from contrats.views import ContratListView, QuittanceListView
        from notifications.views import NotificationListView
        
        # Vérifier que les vues héritent du mixin
        views_to_check = [
            (UtilisateurListView, "UtilisateurListView"),
            (ProprieteListView, "ProprieteListView"),
            (BailleurListView, "BailleurListView"),
            (LocataireListView, "LocataireListView"),
            (PaiementListView, "PaiementListView"),
            (RecuListView, "RecuListView"),
            (ContratListView, "ContratListView"),
            (QuittanceListView, "QuittanceListView"),
            (NotificationListView, "NotificationListView"),
        ]
        
        for view_class, view_name in views_to_check:
            if hasattr(view_class, 'get_privilege_actions'):
                print(f"✅ {view_name} hérite du PrivilegeButtonsMixin")
            else:
                print(f"❌ {view_name} n'hérite pas du PrivilegeButtonsMixin")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test d'héritage: {e}")
        return False

def test_urls():
    """Teste que les URLs de privilège sont bien configurées."""
    try:
        from django.urls import reverse, NoReverseMatch
        
        # URLs à tester
        urls_to_test = [
            'utilisateurs:privilege_delete_element_generic',
            'utilisateurs:privilege_disable_element_generic',
            'utilisateurs:privilege_delete_bailleur',
            'utilisateurs:privilege_delete_locataire',
            'utilisateurs:privilege_delete_propriete',
            'utilisateurs:privilege_bulk_actions',
        ]
        
        for url_name in urls_to_test:
            try:
                # Essayer de construire l'URL avec des paramètres factices
                if 'delete' in url_name or 'disable' in url_name:
                    if 'generic' in url_name:
                        url = reverse(url_name, kwargs={'model_name': 'test', 'element_id': 1})
                    else:
                        url = reverse(url_name, kwargs={'element_id': 1})
                else:
                    url = reverse(url_name)
                print(f"✅ URL {url_name} configurée correctement: {url}")
            except NoReverseMatch as e:
                print(f"❌ URL {url_name} non configurée: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test des URLs: {e}")
        return False

def test_template_inclusion():
    """Teste que le template de base inclut bien les boutons de privilège."""
    try:
        from django.template.loader import get_template
        
        # Vérifier que le template de base existe
        template = get_template('base_liste_intelligente.html')
        template_content = template.template.source
        
        # Vérifier la présence des éléments clés
        required_elements = [
            'privilege_buttons.html',
            'Actions PRIVILEGE',
            'privilege-actions-column'
        ]
        
        for element in required_elements:
            if element in template_content:
                print(f"✅ Élément '{element}' trouvé dans le template")
            else:
                print(f"❌ Élément '{element}' manquant dans le template")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test du template: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 Test du système de privilège")
    print("=" * 50)
    
    tests = [
        ("Import des modules", test_imports),
        ("Héritage des mixins", test_mixin_inheritance),
        ("Configuration des URLs", test_urls),
        ("Inclusion des templates", test_template_inclusion),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            results.append((test_name, False))
    
    # Résumé des tests
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Le système de privilège est correctement configuré.")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
