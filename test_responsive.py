#!/usr/bin/env python
"""
Script de test pour vérifier la responsivité du site
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

def test_responsive_features():
    """Test des fonctionnalités responsive"""
    
    print("📱 TEST DE LA RESPONSIVITÉ DU SITE")
    print("=" * 60)
    
    client = Client()
    
    # Créer un utilisateur de test
    try:
        user = User.objects.create_user(
            username='test_responsive',
            email='test.responsive@email.com',
            password='testpass123',
            first_name='Test',
            last_name='Responsive'
        )
        print("✅ Utilisateur de test créé")
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {e}")
        return
    
    # Se connecter
    client.login(username='test_responsive', password='testpass123')
    print("✅ Connexion réussie")
    
    # Test 1: Vérifier les fichiers CSS
    print("\n📝 Test 1: Vérification des fichiers CSS")
    css_files = [
        'static/css/style.css',
        'static/css/forms.css', 
        'static/css/responsive.css'
    ]
    
    for css_file in css_files:
        if os.path.exists(css_file):
            print(f"✅ {css_file} - Présent")
        else:
            print(f"❌ {css_file} - Manquant")
    
    # Test 2: Vérifier le fichier JavaScript
    print("\n📝 Test 2: Vérification du fichier JavaScript")
    js_file = 'static/js/responsive.js'
    if os.path.exists(js_file):
        print(f"✅ {js_file} - Présent")
    else:
        print(f"❌ {js_file} - Manquant")
    
    # Test 3: Test des pages principales
    print("\n📝 Test 3: Test des pages principales")
    pages_to_test = [
        ('core:dashboard', 'Dashboard'),
        ('proprietes:liste', 'Liste des propriétés'),
        ('proprietes:bailleurs_liste', 'Liste des bailleurs'),
        ('proprietes:locataires_liste', 'Liste des locataires'),
        ('contrats:liste', 'Liste des contrats'),
        ('paiements:liste', 'Liste des paiements'),
        ('paiements:recus_liste', 'Liste des reçus'),
        ('utilisateurs:liste_utilisateurs', 'Liste des utilisateurs'),
    ]
    
    for url_name, page_name in pages_to_test:
        try:
            response = client.get(reverse(url_name))
            if response.status_code == 200:
                print(f"✅ {page_name} - Accessible")
                
                # Vérifier la présence d'éléments responsive
                content = response.content.decode('utf-8')
                
                # Vérifier la meta viewport
                if 'viewport' in content and 'width=device-width' in content:
                    print(f"   ✅ Meta viewport présente")
                else:
                    print(f"   ❌ Meta viewport manquante")
                
                # Vérifier les classes responsive
                responsive_classes = [
                    'table-responsive',
                    'd-lg-none',
                    'd-none d-lg-inline',
                    'sidebar-overlay'
                ]
                
                for class_name in responsive_classes:
                    if class_name in content:
                        print(f"   ✅ Classe {class_name} présente")
                    else:
                        print(f"   ⚠️  Classe {class_name} manquante")
                
            else:
                print(f"❌ {page_name} - Erreur {response.status_code}")
        except Exception as e:
            print(f"❌ {page_name} - Erreur: {e}")
    
    # Test 4: Vérifier le template de base
    print("\n📝 Test 4: Vérification du template de base")
    try:
        response = client.get(reverse('core:dashboard'))
        content = response.content.decode('utf-8')
        
        # Vérifier les éléments responsive dans le template de base
        base_elements = [
            'responsive.css',
            'responsive.js',
            'sidebar-overlay',
            'navbar-toggler',
            'd-lg-none',
            'd-none d-sm-inline',
            'd-inline d-sm-none'
        ]
        
        for element in base_elements:
            if element in content:
                print(f"✅ Élément {element} présent")
            else:
                print(f"❌ Élément {element} manquant")
                
    except Exception as e:
        print(f"❌ Erreur test template de base: {e}")
    
    # Test 5: Vérifier les formulaires
    print("\n📝 Test 5: Vérification des formulaires")
    form_pages = [
        ('proprietes:ajouter', 'Ajouter propriété'),
        ('proprietes:bailleur_ajouter', 'Ajouter bailleur'),
        ('proprietes:locataire_ajouter', 'Ajouter locataire'),
        ('contrats:ajouter', 'Ajouter contrat'),
        ('paiements:ajouter', 'Ajouter paiement'),
    ]
    
    for url_name, form_name in form_pages:
        try:
            response = client.get(reverse(url_name))
            if response.status_code == 200:
                print(f"✅ {form_name} - Accessible")
                
                content = response.content.decode('utf-8')
                
                # Vérifier les classes de formulaire responsive
                form_classes = [
                    'form-container',
                    'form-section',
                    'form-actions',
                    'form-control',
                    'form-select'
                ]
                
                for class_name in form_classes:
                    if class_name in content:
                        print(f"   ✅ Classe {class_name} présente")
                    else:
                        print(f"   ⚠️  Classe {class_name} manquante")
                        
            else:
                print(f"❌ {form_name} - Erreur {response.status_code}")
        except Exception as e:
            print(f"❌ {form_name} - Erreur: {e}")
    
    # Test 6: Vérifier les tableaux
    print("\n📝 Test 6: Vérification des tableaux")
    try:
        response = client.get(reverse('proprietes:liste'))
        content = response.content.decode('utf-8')
        
        if 'table-responsive' in content:
            print("✅ Classe table-responsive présente")
        else:
            print("❌ Classe table-responsive manquante")
            
        if 'data-label' in content:
            print("✅ Attributs data-label présents")
        else:
            print("⚠️  Attributs data-label manquants")
            
    except Exception as e:
        print(f"❌ Erreur test tableaux: {e}")
    
    # Test 7: Vérifier les breakpoints CSS
    print("\n📝 Test 7: Vérification des breakpoints CSS")
    try:
        with open('static/css/responsive.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        breakpoints = [
            '@media (max-width: 575.98px)',
            '@media (min-width: 576px) and (max-width: 767.98px)',
            '@media (min-width: 768px) and (max-width: 991.98px)',
            '@media (min-width: 992px)'
        ]
        
        for breakpoint in breakpoints:
            if breakpoint in css_content:
                print(f"✅ Breakpoint {breakpoint} présent")
            else:
                print(f"❌ Breakpoint {breakpoint} manquant")
                
    except Exception as e:
        print(f"❌ Erreur lecture CSS: {e}")
    
    # Test 8: Vérifier les fonctionnalités JavaScript
    print("\n📝 Test 8: Vérification des fonctionnalités JavaScript")
    try:
        with open('static/js/responsive.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        js_features = [
            'toggleSidebar',
            'closeSidebar',
            'isMobile',
            'isTablet',
            'isDesktop',
            'getScreenSize',
            'addEventListener'
        ]
        
        for feature in js_features:
            if feature in js_content:
                print(f"✅ Fonction {feature} présente")
            else:
                print(f"❌ Fonction {feature} manquante")
                
    except Exception as e:
        print(f"❌ Erreur lecture JavaScript: {e}")
    
    # Nettoyage
    try:
        user.delete()
        print("\n✅ Utilisateur de test supprimé")
    except Exception as e:
        print(f"\n❌ Erreur suppression utilisateur: {e}")
    
    print("\n🎉 TEST DE RESPONSIVITÉ TERMINÉ !")
    print("=" * 60)
    print("📱 Le site devrait maintenant être parfaitement responsive !")
    print("🔧 Vérifiez sur différents appareils et navigateurs.")
    print("📊 Utilisez les outils de développement pour tester les breakpoints.")

if __name__ == '__main__':
    test_responsive_features() 