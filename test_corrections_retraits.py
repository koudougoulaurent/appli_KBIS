#!/usr/bin/env python
"""
Test des corrections apportées aux pages de retraits
- Correction de la redirection vers la page de connexion des groupes
- Fusion des pages "Retraits" et "Retraits Bailleur"
- Suppression de la redondance fonctionnelle
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from utilisateurs.models import Utilisateur, GroupeTravail
from django.test import TestCase
from django.urls import reverse

def test_corrections_retraits():
    """Test des corrections apportées aux pages de retraits"""
    
    print("🔍 TEST DES CORRECTIONS DES PAGES DE RETRAITS")
    print("=" * 60)
    
    # Test 1: Vérifier que LOGIN_URL pointe vers la bonne page
    print("\n📋 Test 1: Configuration LOGIN_URL")
    print("-" * 40)
    
    from django.conf import settings
    if hasattr(settings, 'LOGIN_URL'):
        print(f"✅ LOGIN_URL configuré: {settings.LOGIN_URL}")
        if 'connexion_groupes' in settings.LOGIN_URL:
            print("✅ LOGIN_URL pointe vers la page de connexion des groupes")
        else:
            print("❌ LOGIN_URL ne pointe pas vers la page de connexion des groupes")
    else:
        print("❌ LOGIN_URL non configuré")
    
    # Test 2: Vérifier que les URLs des retraits sont accessibles
    print("\n🔗 Test 2: URLs des retraits")
    print("-" * 40)
    
    try:
        from paiements.urls import urlpatterns
        
        # Vérifier que l'URL des retraits existe
        retraits_url = None
        retraits_bailleur_url = None
        
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name == 'retraits_liste':
                retraits_url = pattern
                print(f"✅ URL retraits trouvée: {pattern}")
            elif hasattr(pattern, 'name') and pattern.name == 'liste_retraits_bailleur':
                retraits_bailleur_url = pattern
                print(f"✅ URL retraits bailleur trouvée: {pattern}")
        
        if retraits_url and retraits_bailleur_url:
            print("✅ Les deux URLs de retraits sont disponibles")
        else:
            print("❌ Certaines URLs de retraits sont manquantes")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des URLs: {e}")
    
    # Test 3: Vérifier que le template unifié existe
    print("\n📄 Test 3: Template unifié des retraits")
    print("-" * 40)
    
    template_path = 'templates/paiements/retrait_liste_unifiee.html'
    if os.path.exists(template_path):
        print(f"✅ Template unifié trouvé: {template_path}")
        
        # Vérifier le contenu du template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'Retraits Généraux' in content and 'Retraits Bailleurs Récents' in content:
            print("✅ Template contient les deux sections (généraux et bailleurs)")
        else:
            print("❌ Template ne contient pas les deux sections")
            
    else:
        print(f"❌ Template unifié non trouvé: {template_path}")
    
    # Test 4: Vérifier que la navigation a été mise à jour
    print("\n🧭 Test 4: Navigation mise à jour")
    print("-" * 40)
    
    base_template_path = 'templates/base.html'
    if os.path.exists(base_template_path):
        with open(base_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'Retraits Bailleur' not in content:
            print("✅ Page 'Retraits Bailleur' supprimée de la navigation")
        else:
            print("❌ Page 'Retraits Bailleur' encore présente dans la navigation")
            
        if 'Retraits' in content:
            print("✅ Page 'Retraits' maintenue dans la navigation")
        else:
            print("❌ Page 'Retraits' manquante dans la navigation")
    else:
        print(f"❌ Template de base non trouvé: {base_template_path}")
    
    # Test 5: Vérifier que la vue RetraitListView utilise le bon template
    print("\n👁️ Test 5: Vue RetraitListView")
    print("-" * 40)
    
    try:
        from paiements.views import RetraitListView
        
        if RetraitListView.template_name == 'paiements/retrait_liste_unifiee.html':
            print("✅ RetraitListView utilise le template unifié")
        else:
            print(f"❌ RetraitListView utilise un autre template: {RetraitListView.template_name}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la vue: {e}")
    
    # Test 6: Vérifier que les modèles de retraits sont disponibles
    print("\n🗄️ Test 6: Modèles de retraits")
    print("-" * 40)
    
    try:
        from paiements.models import Retrait
        
        retraits_count = Retrait.objects.count()
        print(f"✅ Modèle Retrait disponible - {retraits_count} retraits en base")
        
        # Vérifier le modèle RetraitBailleur
        try:
            from paiements.models import RetraitBailleur
            retraits_bailleur_count = RetraitBailleur.objects.count()
            print(f"✅ Modèle RetraitBailleur disponible - {retraits_bailleur_count} retraits bailleur en base")
        except ImportError:
            print("❌ Modèle RetraitBailleur non disponible")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des modèles: {e}")
    
    # Test 7: Vérifier la configuration des URLs principales
    print("\n🌐 Test 7: Configuration des URLs principales")
    print("-" * 40)
    
    try:
        from gestion_immobiliere.urls import urlpatterns
        
        # Vérifier que la redirection racine pointe vers core
        root_redirect = None
        for pattern in urlpatterns:
            if hasattr(pattern, 'callback') and 'redirect_to_groupes' in str(pattern.callback):
                root_redirect = pattern
                break
        
        if root_redirect:
            print("✅ Redirection racine vers la page de connexion des groupes configurée")
        else:
            print("❌ Redirection racine vers la page de connexion des groupes non configurée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des URLs principales: {e}")
    
    print("\n✅ TOUS LES TESTS TERMINÉS !")
    print("🎉 Vérifiez les résultats ci-dessus pour confirmer les corrections")
    
    return True

if __name__ == "__main__":
    test_corrections_retraits()
